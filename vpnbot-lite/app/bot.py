"""Telegram admin bot."""
import asyncio
import html
import json
import os
import platform
import re
import tempfile
import time
from pathlib import Path

import aiohttp
import psutil
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (BufferedInputFile, CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import config, watch
from .cores import latest_tag, plain_version
from .service import Service, fmt_bytes
from .sub import qr_png

NAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,32}$")
GB = 1024 ** 3


class Input(StatesGroup):
    add_user = State()
    days = State()
    limit = State()
    reality_sni = State()
    host = State()
    mtproto_domain = State()


def kb(*rows: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t, callback_data=d) for t, d in row] for row in rows])


BACK = [("⬅️ Меню", "menu")]


def fmt_date(ts: int | None) -> str:
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts)) if ts else "бессрочно"


def fmt_uptime(seconds: float) -> str:
    seconds = int(seconds)
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    return f"{d}д {h}ч {rem // 60}м" if d else f"{h}ч {rem // 60}м"


def setup(service: Service) -> Router:
    router = Router()
    router.message.filter(F.from_user.id.in_(config.ADMIN_IDS))
    router.callback_query.filter(F.from_user.id.in_(config.ADMIN_IDS))
    db = service.db

    async def show(target: Message | CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
        if isinstance(target, CallbackQuery):
            try:
                await target.message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
            except TelegramBadRequest as e:
                if "not modified" not in str(e):
                    await target.message.answer(text, reply_markup=markup, disable_web_page_preview=True)
            await target.answer()
        else:
            await target.answer(text, reply_markup=markup, disable_web_page_preview=True)

    async def apply(target: Message | CallbackQuery) -> bool:
        error = await service.apply()
        if error:
            msg = target.message if isinstance(target, CallbackQuery) else target
            await msg.answer(f"⚠️ Ошибка применения конфигурации:\n<pre>{html.escape(error)}</pre>")
        return error is None

    def dot(core) -> str:
        return "🟢" if core.running else ("⚪️" if not core.wanted else "🔴")

    # ---------- main menu ----------
    def menu_markup() -> InlineKeyboardMarkup:
        return kb([("👥 Пользователи", "users"), ("📊 Сервер", "server")],
                  [("⬆️ Обновления", "updates"), ("⚙️ Настройки", "settings")],
                  [("📨 Прокси Telegram", "mtp"), ("💾 Бэкап", "backup")],
                  [("📜 Логи", "logs")])

    def menu_text() -> str:
        users = db.users()
        active = sum(1 for u in users if u["enabled"])
        return (f"<b>VPN Bot Lite</b> v{config.VERSION}\n"
                f"Сервер: <code>{html.escape(service.host)}</code>\n"
                f"Пользователи: {active} активных из {len(users)}\n"
                f"Xray: {dot(service.xray)}   "
                f"Hysteria2: {dot(service.hysteria)}   AmneziaWG: {dot(service.awg)}   "
                f"MTProto: {dot(service.mtproto)}")

    @router.message(CommandStart())
    @router.message(Command("menu"))
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(menu_text(), reply_markup=menu_markup())

    @router.callback_query(F.data == "menu")
    async def menu(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await show(cb, menu_text(), menu_markup())

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Отменено.", reply_markup=menu_markup())

    # ---------- users ----------
    async def users_list(target: Message | CallbackQuery) -> None:
        b = InlineKeyboardBuilder()
        for u in db.users():
            used = fmt_bytes(u["up"] + u["down"])
            b.button(text=f"{service.user_status(u)} {u['name']} · {used}", callback_data=f"u:{u['id']}")
        b.adjust(1)
        b.row(*kb([("➕ Добавить", "add"), *BACK]).inline_keyboard[0])
        text = "<b>Пользователи</b>\n✅ активен  ⏳ скоро истекает  ⏸ отключён"
        await show(target, text, b.as_markup())

    @router.callback_query(F.data == "users")
    async def users(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await users_list(cb)

    def user_card(u) -> tuple[str, InlineKeyboardMarkup]:
        limit = fmt_bytes(u["limit_bytes"]) if u["limit_bytes"] else "без лимита"
        text = (f"<b>{html.escape(u['name'])}</b> {service.user_status(u)}\n"
                f"Статус: {'активен' if u['enabled'] else 'отключён'}\n"
                f"Срок: {fmt_date(u['expire_at'])}\n"
                f"Трафик: ↑{fmt_bytes(u['up'])} ↓{fmt_bytes(u['down'])} = "
                f"<b>{fmt_bytes(u['up'] + u['down'])}</b> / {limit}\n"
                f"Создан: {fmt_date(u['created_at'])}")
        i = u["id"]
        markup = kb([("🔗 Ключи и QR", f"links:{i}"), ("📡 AmneziaWG (роутер)", f"awg:{i}")],
                    [("⏸ Отключить" if u["enabled"] else "▶️ Включить", f"toggle:{i}"),
                     ("📅 Срок", f"days:{i}"), ("📦 Лимит", f"limit:{i}")],
                    [("🔄 Сбросить трафик", f"reset:{i}"), ("🗑 Удалить", f"del:{i}")],
                    [("⬅️ Пользователи", "users")])
        return text, markup

    async def get_user(cb: CallbackQuery):
        u = db.user(int(cb.data.split(":")[1]))
        if not u:
            await cb.answer("Пользователь не найден", show_alert=True)
        return u

    @router.callback_query(F.data.startswith("u:"))
    async def user_view(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        if u := await get_user(cb):
            await show(cb, *user_card(u))

    @router.callback_query(F.data.startswith("links:"))
    async def user_links(cb: CallbackQuery) -> None:
        u = await get_user(cb)
        if not u:
            return
        sub = service.sub_url(u)
        text = (f"<b>{html.escape(u['name'])}</b>\n\n"
                f"📲 <b>Подписка</b> (рекомендуется — ключи обновляются сами):\n<code>{html.escape(sub)}</code>\n\n"
                + "\n\n".join(f"<code>{html.escape(link)}</code>" for link in service.links(u))
                + (f"\n\nHysteria2 для Happ / v2RayTun / v2rayN (без insecure):\n"
                   f"<code>{html.escape(service.hy2_link(u, insecure=False))}</code>"
                   if db.get("hy_enabled") == "1" else "")
                + "\n\nПриложения: Hiddify, v2RayTun, Happ (iOS/Android), v2rayN (Windows), Streisand (iOS).")
        await cb.message.answer_photo(BufferedInputFile(qr_png(sub), "qr.png"), caption="QR-код подписки")
        await cb.message.answer(text, disable_web_page_preview=True)
        await cb.answer()

    @router.callback_query(F.data.startswith("awg:"))
    async def user_awg(cb: CallbackQuery) -> None:
        u = await get_user(cb)
        if not u:
            return
        if db.get("awg_enabled") != "1":
            await cb.answer("AmneziaWG выключен в настройках", show_alert=True)
            return
        conf = service.awg_conf(u)
        if conf is None:
            await cb.answer("Конфиг перенесён со старого сервера без приватного ключа — "
                            "файл у клиента уже есть, новый выдать нельзя", show_alert=True)
            return
        await cb.message.answer_document(
            BufferedInputFile(conf.encode(), f"{u['name']}.conf"),
            caption=f"📡 AmneziaWG для <b>{html.escape(u['name'])}</b>\n"
                    "Роутер: Keenetic (4.2+), OpenWrt (amneziawg) — импорт этого .conf.\n"
                    "Телефон/ПК: приложение AmneziaVPN или AmneziaWG — импорт файла или QR.")
        await cb.message.answer_photo(BufferedInputFile(qr_png(conf), "awg.png"), caption="QR для AmneziaWG")
        await cb.answer()

    @router.callback_query(F.data.startswith("toggle:"))
    async def user_toggle(cb: CallbackQuery) -> None:
        u = await get_user(cb)
        if not u:
            return
        enable = not u["enabled"]
        fields = {"enabled": int(enable)}
        if enable and u["expire_at"] and u["expire_at"] <= time.time():
            fields["expire_at"] = None
        if enable and u["limit_bytes"] and u["up"] + u["down"] >= u["limit_bytes"]:
            fields.update(up=0, down=0)
        db.update_user(u["id"], **fields)
        await apply(cb)
        await show(cb, *user_card(db.user(u["id"])))

    @router.callback_query(F.data.startswith("reset:"))
    async def user_reset(cb: CallbackQuery) -> None:
        if u := await get_user(cb):
            db.update_user(u["id"], up=0, down=0)
            await show(cb, *user_card(db.user(u["id"])))

    @router.callback_query(F.data.startswith("del:"))
    async def user_delete(cb: CallbackQuery) -> None:
        if u := await get_user(cb):
            await show(cb, f"Удалить <b>{html.escape(u['name'])}</b>? Ключи перестанут работать.",
                       kb([("🗑 Да, удалить", f"delok:{u['id']}"), ("Отмена", f"u:{u['id']}")]))

    @router.callback_query(F.data.startswith("delok:"))
    async def user_delete_ok(cb: CallbackQuery) -> None:
        if u := await get_user(cb):
            db.delete_user(u["id"])
            await apply(cb)
            await users_list(cb)

    @router.callback_query(F.data.startswith("days:"))
    async def user_days(cb: CallbackQuery, state: FSMContext) -> None:
        if u := await get_user(cb):
            await state.set_state(Input.days)
            await state.update_data(user_id=u["id"])
            await show(cb, f"Срок для <b>{html.escape(u['name'])}</b>: сейчас {fmt_date(u['expire_at'])}.\n"
                           "Отправьте число дней от сегодня (0 — бессрочно) или «+30», чтобы продлить.",
                       kb([("+30 дней", f"plus30:{u['id']}"), ("♾ Бессрочно", f"nodays:{u['id']}")],
                          [("Отмена", f"u:{u['id']}")]))

    async def set_expire(target, user_id: int, expire_at: int | None) -> None:
        u = db.user(user_id)
        fields = {"expire_at": expire_at}
        was_expired = u["expire_at"] and u["expire_at"] <= time.time()
        if not u["enabled"] and was_expired and (expire_at is None or expire_at > time.time()):
            fields["enabled"] = 1
        db.update_user(user_id, **fields)
        if "enabled" in fields:
            await apply(target)
        await show(target, *user_card(db.user(user_id)))

    def extend(u, days: int) -> int:
        base = max(u["expire_at"] or 0, int(time.time()))
        return base + days * 86400

    @router.callback_query(F.data.startswith("plus30:"))
    async def user_plus30(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        if u := await get_user(cb):
            await set_expire(cb, u["id"], extend(u, 30))

    @router.callback_query(F.data.startswith("nodays:"))
    async def user_nodays(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        if u := await get_user(cb):
            await set_expire(cb, u["id"], None)

    @router.message(Input.days, F.text)
    async def user_days_input(message: Message, state: FSMContext) -> None:
        m = re.fullmatch(r"\s*(\+?)(\d{1,5})\s*", message.text)
        if not m:
            await message.answer("Нужно число дней, например 30 или +30. /cancel — отмена.")
            return
        user_id = (await state.get_data())["user_id"]
        await state.clear()
        u = db.user(user_id)
        if not u:
            return
        days = int(m.group(2))
        if m.group(1):
            expire = extend(u, days)
        else:
            expire = int(time.time()) + days * 86400 if days else None
        await set_expire(message, user_id, expire)

    @router.callback_query(F.data.startswith("limit:"))
    async def user_limit(cb: CallbackQuery, state: FSMContext) -> None:
        if u := await get_user(cb):
            await state.set_state(Input.limit)
            await state.update_data(user_id=u["id"])
            await show(cb, f"Лимит трафика для <b>{html.escape(u['name'])}</b> в ГБ (0 — без лимита):",
                       kb([("Отмена", f"u:{u['id']}")]))

    @router.message(Input.limit, F.text)
    async def user_limit_input(message: Message, state: FSMContext) -> None:
        try:
            gb = float(message.text.replace(",", "."))
            assert gb >= 0
        except (ValueError, AssertionError):
            await message.answer("Нужно число гигабайт, например 50. /cancel — отмена.")
            return
        user_id = (await state.get_data())["user_id"]
        await state.clear()
        if db.user(user_id):
            db.update_user(user_id, limit_bytes=int(gb * GB) or None)
            await show(message, *user_card(db.user(user_id)))

    @router.callback_query(F.data == "add")
    async def user_add(cb: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(Input.add_user)
        await show(cb, "Отправьте имя пользователя (латиница, цифры, <code>_ . -</code>).\n"
                       "Можно сразу указать срок в днях и лимит в ГБ:\n<code>ivan 30 100</code>\n\n"
                       "Можно несколько — по одному в строке.", kb([("Отмена", "users")]))

    @router.message(Input.add_user, F.text)
    async def user_add_input(message: Message, state: FSMContext) -> None:
        created, errors = [], []
        for line in message.text.strip().splitlines():
            parts = line.split()
            if not parts:
                continue
            name = parts[0]
            if not NAME_RE.match(name):
                errors.append(f"{name}: недопустимое имя")
                continue
            if db.user_by_name(name):
                errors.append(f"{name}: уже существует")
                continue
            try:
                days = int(parts[1]) if len(parts) > 1 else 0
                gb = float(parts[2].replace(",", ".")) if len(parts) > 2 else 0
            except ValueError:
                errors.append(f"{name}: срок и лимит должны быть числами")
                continue
            created.append(db.add_user(name, int(time.time()) + days * 86400 if days else None,
                                       int(gb * GB) or None))
        if errors:
            await message.answer("⚠️ " + "\n".join(html.escape(e) for e in errors))
        if not created:
            await message.answer("Никто не добавлен. Попробуйте ещё раз или /cancel.")
            return
        await state.clear()
        await apply(message)
        if len(created) == 1:
            await show(message, *user_card(db.user(created[0])))
        else:
            await users_list(message)

    # ---------- server ----------
    @router.callback_query(F.data == "server")
    async def server(cb: CallbackQuery) -> None:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(config.DATA_DIR))
        net = psutil.net_io_counters()
        load = ", ".join(f"{x:.2f}" for x in os.getloadavg())
        users = db.users()
        total = sum(u["up"] + u["down"] for u in users)
        xv, hv = await service.xray.version(), await service.hysteria.version()

        def core_line(core, ver):
            state = "🟢 работает" if core.running else ("⚪️ выключен" if not core.wanted else "🔴 упал")
            up = f", аптайм {fmt_uptime(time.time() - core.started_at)}" if core.running else ""
            return f"{core.name} {ver or '?'}: {state}{up}"

        text = (f"<b>Сервер</b> {html.escape(service.host)}\n"
                f"ОС: {html.escape(platform.platform(terse=True))}\n"
                f"Аптайм: {fmt_uptime(time.time() - psutil.boot_time())}\n"
                f"CPU: {psutil.cpu_percent(interval=0.5):.0f}% ({psutil.cpu_count()} ядер), load {load}\n"
                f"RAM: {fmt_bytes(mem.used)} / {fmt_bytes(mem.total)} ({mem.percent:.0f}%)\n"
                f"Диск: {fmt_bytes(disk.used)} / {fmt_bytes(disk.total)} ({disk.percent:.0f}%)\n"
                f"Сеть с загрузки ОС: ↑{fmt_bytes(net.bytes_sent)} ↓{fmt_bytes(net.bytes_recv)}\n\n"
                f"{core_line(service.xray, xv)}\n{core_line(service.hysteria, hv)}\n"
                f"{core_line(service.awg, await service.awg.version())}\n"
                f"{core_line(service.mtproto, await service.mtproto.version())}\n\n"
                f"Трафик пользователей (всего): {fmt_bytes(total)}")
        if config.DDNS_DOMAIN:
            text += f"\n\n🌐 DuckDNS: {html.escape(config.DDNS_DOMAIN)} → {db.get('ddns_ip') or '…'}"
        last = json.loads(db.get("watch_last") or "{}")
        if last.get("state"):
            text += (f"\n📡 {watch.STATE_TEXT.get(last['state'], last['state'])}"
                     f" (проверено {time.strftime('%d.%m %H:%M', time.localtime(last.get('time', 0)))})")
        watch_on = db.get("watch_enabled", "1") == "1"
        await show(cb, text, kb([("🔄 Обновить", "server"), ("♻️ Перезапуск ядер", "restart")],
                                [("📡 Доступность из РФ", "reach")],
                                [(f"🔔 Сторож раз в час: {'вкл' if watch_on else 'выкл'}", "reach_toggle")], BACK))

    @router.callback_query(F.data == "reach")
    async def reach(cb: CallbackQuery) -> None:
        await cb.answer("Проверяю с узлов в России, ~20 секунд…")
        port = config.XHTTP_PORT or config.XRAY_PORT
        async with aiohttp.ClientSession() as session:
            result = await service.reach.check(session, service.host, port)
        if result["state"] != "error":
            db.set("watch_last", json.dumps(result))
            db.set("watch_state", result["state"])
        await cb.message.answer(watch.describe(result, service.host, port), reply_markup=kb([("📊 Сервер", "server")]))

    @router.callback_query(F.data == "reach_toggle")
    async def reach_toggle(cb: CallbackQuery) -> None:
        db.set("watch_enabled", "0" if db.get("watch_enabled", "1") == "1" else "1")
        await server(cb)

    @router.callback_query(F.data == "restart")
    async def restart(cb: CallbackQuery) -> None:
        await cb.answer("Перезапускаю…")
        if await apply(cb):
            await cb.message.answer("✅ Ядра перезапущены")

    # ---------- updates ----------
    async def remote_bot_version(session: aiohttp.ClientSession) -> str | None:
        if not config.BOT_VERSION_URL:
            return None
        try:
            async with session.get(config.BOT_VERSION_URL, timeout=aiohttp.ClientTimeout(total=10)) as r:
                return (await r.text()).strip() if r.status == 200 else None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    @router.callback_query(F.data == "updates")
    async def updates(cb: CallbackQuery) -> None:
        await cb.answer("Проверяю…")
        rows, lines = [], ["<b>Обновления</b>\n"]
        async with aiohttp.ClientSession() as session:
            for core in (service.xray, service.hysteria, service.mtproto):
                current = await core.version()
                try:
                    tag = await latest_tag(session, core.repo)
                    latest = plain_version(tag)
                except Exception as e:  # noqa: BLE001 - shown to the admin
                    tag, latest = None, None
                    lines.append(f"{core.name}: {current} (ошибка проверки: {html.escape(str(e))})")
                if latest:
                    mark = "✅ актуальная" if latest == current else f"→ доступна <b>{latest}</b>"
                    lines.append(f"{core.name}: {current} {mark}")
                    if latest != current:
                        rows.append([(f"⬆️ {core.name} {latest}", f"upd:{core.name}:{tag}")])
                if core.has_backup():
                    rows.append([(f"↩️ Откатить {core.name}", f"rollback:{core.name}")])
            remote = await remote_bot_version(session)
        lines.append(f"amneziawg: {await service.awg.version() or '?'} (обновляется вместе с ботом)")
        if remote and remote != config.VERSION:
            lines.append(f"бот: {config.VERSION} → доступна <b>{html.escape(remote)}</b>")
        else:
            lines.append(f"бот: {config.VERSION}" + (" ✅ актуальная" if remote else ""))
        rows.append([("⬆️ Обновить бота", "updbot")])
        rows.append([("🔄 Проверить снова", "updates"), *BACK])
        await show(cb, "\n".join(lines), kb(*rows))

    def core_by_name(name: str):
        return {"xray": service.xray, "hysteria": service.hysteria, "amneziawg": service.awg,
                "mtproto": service.mtproto, "telemt": service.mtproto}[name]

    @router.callback_query(F.data.startswith("upd:"))
    async def update_core(cb: CallbackQuery) -> None:
        _, name, tag = cb.data.split(":", 2)
        core = core_by_name(name)
        await cb.answer()
        msg = await cb.message.answer(f"⏳ Обновляю {name} до {html.escape(tag)}…")
        try:
            async with aiohttp.ClientSession() as session:
                await service.collect_stats()
                version = await core.install(session, tag)
            error = await service.xray.check_config() if core is service.xray else None
            if error:
                await core.rollback()
                await msg.edit_text(f"⚠️ Новая версия не приняла конфиг, выполнен откат:\n"
                                    f"<pre>{html.escape(error)}</pre>")
                return
            await msg.edit_text(f"✅ {name} обновлён до {version}")
        except Exception as e:  # noqa: BLE001
            await msg.edit_text(f"❌ Не удалось обновить {name}: {html.escape(str(e))}")

    @router.callback_query(F.data.startswith("rollback:"))
    async def rollback_core(cb: CallbackQuery) -> None:
        core = core_by_name(cb.data.split(":")[1])
        await cb.answer()
        try:
            version = await core.rollback()
            await cb.message.answer(f"↩️ {core.name} откатан до {version}")
        except Exception as e:  # noqa: BLE001
            await cb.message.answer(f"❌ {html.escape(str(e))}")

    @router.callback_query(F.data == "updbot")
    async def update_bot(cb: CallbackQuery) -> None:
        (config.DATA_DIR / "update.request").write_text(str(cb.from_user.id))
        await cb.answer()
        await cb.message.answer(
            "⏳ Запрос на обновление отправлен. Сервер скачает новую версию и перезапустит бота "
            "(1–3 минуты), после чего придёт сообщение.\n\n"
            "Если ничего не произошло — выполните на сервере: <code>./vpn.sh update</code>")

    # ---------- telegram proxy ----------
    def mtproto_view() -> tuple[str, InlineKeyboardMarkup]:
        if not config.MTPROTO_PORT:
            return "Прокси Telegram выключен в .env (MTPROTO_PORT=0).", kb(BACK)
        enabled = db.get("mtproto_enabled") == "1"
        if not enabled:
            return ("📨 <b>Прокси Telegram (MTProto)</b>: выключен",
                    kb([("▶️ Включить", "mtp:toggle")], BACK))
        link = service.mtproto_link()
        text = (f"📨 <b>Прокси Telegram (MTProto)</b> {dot(service.mtproto)}\n\n"
                f"Нажмите на ссылку на устройстве с Telegram — он предложит подключить прокси:\n"
                f"{html.escape(link)}\n\n"
                f"Вручную (Настройки → Данные и память → Прокси → Добавить → MTProto):\n"
                f"Сервер: <code>{html.escape(service.host)}</code>\nПорт: <code>{config.MTPROTO_PORT}</code>\n"
                f"Секрет: <code>{db.get('mtproto_secret')}</code>\n\n"
                f"Маскировка: <code>{html.escape(bytes.fromhex(db.get('mtproto_secret')[34:]).decode())}</code>. "
                "Одна ссылка для всех — можно пересылать друзьям.")
        return text, kb([("🔳 QR", "mtp:qr"), ("🔄 Новая ссылка", "mtp:new")],
                        [("🌐 Сайт маскировки", "mtp:domain")],
                        [("⏸ Выключить", "mtp:toggle")], BACK)

    @router.callback_query(F.data == "mtp")
    async def mtproto(cb: CallbackQuery) -> None:
        await show(cb, *mtproto_view())

    @router.callback_query(F.data == "mtp:toggle")
    async def mtproto_toggle(cb: CallbackQuery) -> None:
        db.set("mtproto_enabled", "0" if db.get("mtproto_enabled") == "1" else "1")
        await apply(cb)
        await show(cb, *mtproto_view())

    @router.callback_query(F.data == "mtp:qr")
    async def mtproto_qr(cb: CallbackQuery) -> None:
        await cb.message.answer_photo(BufferedInputFile(qr_png(service.mtproto_link()), "proxy.png"),
                                      caption="QR прокси Telegram — отсканируйте камерой телефона")
        await cb.answer()

    @router.callback_query(F.data == "mtp:domain")
    async def mtproto_domain(cb: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(Input.mtproto_domain)
        await show(cb, "Под какой сайт маскировать прокси? Отправьте домен (сайт с TLS 1.3), например "
                       "<code>petrovich.ru</code>, <code>ya.ru</code>, <code>vk.com</code>.\n"
                       "«auto» — собственный адрес сервера (IP.nip.io).\n\n"
                       "Ссылка на прокси изменится — старую придётся заменить.", kb([("Отмена", "mtp")]))

    @router.message(Input.mtproto_domain, F.text)
    async def mtproto_domain_input(message: Message, state: FSMContext) -> None:
        domain = message.text.strip().lower()
        if domain == "auto":
            await state.clear()
            db.conn.execute("DELETE FROM settings WHERE key='mtproto_domain'")
        else:
            if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", domain):
                await message.answer("Это не похоже на домен. /cancel — отмена.")
                return
            await state.clear()
            check = await service.check_sni(domain)
            await message.answer(html.escape(check))
            if "✅" not in check:
                await message.answer("Сайт маскировки не изменён.")
                return
            db.set("mtproto_domain", domain)
        service.regenerate_mtproto()
        await apply(message)
        await show(message, *mtproto_view())

    @router.callback_query(F.data == "mtp:new")
    async def mtproto_new(cb: CallbackQuery) -> None:
        await show(cb, "Сделать новую ссылку на прокси? Старая перестанет работать у всех, кому вы её давали.",
                   kb([("Да", "mtp:newok"), ("Отмена", "mtp")]))

    @router.callback_query(F.data == "mtp:newok")
    async def mtproto_new_ok(cb: CallbackQuery) -> None:
        service.regenerate_mtproto()
        await apply(cb)
        await show(cb, *mtproto_view())

    # ---------- settings ----------
    def settings_view() -> tuple[str, InlineKeyboardMarkup]:
        s = service.settings()
        on = lambda key: "вкл" if s.get(key) == "1" else "выкл"  # noqa: E731
        text = (f"<b>Настройки</b>\n\n"
                f"Адрес сервера: <code>{html.escape(service.host)}</code>\n"
                f"Порты: Reality {config.XRAY_PORT}/tcp, XHTTP {config.XHTTP_PORT or '—'}/tcp, "
                f"Hysteria2 {config.HY2_PORT}/udp, "
                f"AmneziaWG {config.AWG_PORT}/udp, подписка {config.SUB_PORT}/tcp\n\n"
                f"<b>VLESS Reality</b>\nSNI (маскировка): <code>{html.escape(s['reality_sni'])}</code>, "
                f"передавать SNI в ссылках: {'нет' if s.get('reality_nosni') == '1' else 'да'}\n"
                f"XHTTP: {on('xhttp_enabled') if config.XHTTP_PORT else 'выкл (XHTTP_PORT=0)'}\n"
                f"Public key: <code>{s['reality_public']}</code>\nShort ID: <code>{s['reality_sid']}</code>\n\n"
                f"<b>Hysteria2</b>: {on('hy_enabled')}, обфускация Salamander: {on('hy_obfs')}\n"
                f"<b>AmneziaWG</b>: {on('awg_enabled')}, подсеть {config.AWG_SUBNET}, порт {config.AWG_PORT}\n"
                f"Маскировка новых конфигов: "
                f"{'QUIC Initial 1200 байт' if s.get('awg_client_profile', 'quic') == 'quic' else 'как у сервера'}\n"
                f"<b>Блокировка рекламы</b>: {on('block_ads')}")
        markup = kb([("🌐 SNI Reality", "set:sni"), ("🩺 Проверить SNI", "set:check")],
                    [(f"SNI в ссылках: {'нет' if s.get('reality_nosni') == '1' else 'да'}", "set:nosni"),
                     (f"XHTTP: {on('xhttp_enabled')}", "set:xhttp")],
                    [("🔑 Новые ключи Reality", "set:rekey")],
                    [(f"Hysteria2: {on('hy_enabled')}", "set:hy"), (f"Обфускация: {on('hy_obfs')}", "set:obfs")],
                    [(f"AmneziaWG: {on('awg_enabled')}", "set:awg"), ("🔑 Новые ключи AWG", "set:awgkey")],
                    [("Маскировка новых AWG-конфигов: "
                      + ("QUIC" if s.get("awg_client_profile", "quic") == "quic" else "как у сервера"), "set:awgprof")],
                    [(f"Блок рекламы: {on('block_ads')}", "set:ads"), ("📍 Адрес сервера", "set:host")],
                    BACK)
        return text, markup

    @router.callback_query(F.data == "settings")
    async def settings(cb: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await show(cb, *settings_view())

    @router.callback_query(F.data.in_({"set:hy", "set:obfs", "set:ads", "set:awg", "set:nosni", "set:xhttp"}))
    async def toggle_setting(cb: CallbackQuery) -> None:
        key = {"set:hy": "hy_enabled", "set:obfs": "hy_obfs", "set:ads": "block_ads",
               "set:awg": "awg_enabled", "set:nosni": "reality_nosni", "set:xhttp": "xhttp_enabled"}[cb.data]
        db.set(key, "0" if db.get(key) == "1" else "1")
        await apply(cb)
        await show(cb, *settings_view())
        if key in ("hy_enabled", "hy_obfs", "reality_nosni", "xhttp_enabled"):
            await cb.message.answer("ℹ️ Ссылки изменились — клиентам с подпиской достаточно обновить её.")

    @router.callback_query(F.data == "set:rekey")
    async def rekey(cb: CallbackQuery) -> None:
        await show(cb, "Сгенерировать новые ключи Reality? Старые ключи у всех клиентов перестанут работать "
                       "(подписки обновятся автоматически).", kb([("Да", "set:rekeyok"), ("Отмена", "settings")]))

    @router.callback_query(F.data == "set:rekeyok")
    async def rekey_ok(cb: CallbackQuery) -> None:
        service.regenerate_reality()
        await apply(cb)
        await show(cb, *settings_view())

    @router.callback_query(F.data == "set:awgkey")
    async def awg_rekey(cb: CallbackQuery) -> None:
        await show(cb, "⚠️ Сгенерировать новый ключ и маскировку AmneziaWG (2.0)?\n\n"
                       "<b>Все</b> выданные .conf перестанут работать, <b>включая роутер</b> — "
                       "их нужно будет выдать и импортировать заново.",
                   kb([("Да", "set:awgkeyok"), ("Отмена", "settings")]))

    @router.callback_query(F.data == "set:awgkeyok")
    async def awg_rekey_ok(cb: CallbackQuery) -> None:
        service.regenerate_awg()
        await service.awg.stop()  # obfuscation parameters can't be changed on a running interface
        await apply(cb)
        await show(cb, *settings_view())

    @router.callback_query(F.data == "set:awgprof")
    async def awg_profile(cb: CallbackQuery) -> None:
        # client-side only: affects .conf files issued from now on; the server and existing devices are unchanged
        db.set("awg_client_profile", "server" if db.get("awg_client_profile", "quic") == "quic" else "quic")
        await show(cb, *settings_view())

    @router.callback_query(F.data == "set:sni")
    async def set_sni(cb: CallbackQuery, state: FSMContext) -> None:
        await state.set_state(Input.reality_sni)
        await show(cb, "Отправьте домен для маскировки Reality (сайт с TLS 1.3 и HTTP/2, "
                       "не за Cloudflare), например:\n<code>www.microsoft.com</code>, <code>dl.google.com</code>, "
                       "<code>www.samsung.com</code>", kb([("Отмена", "settings")]))

    @router.message(Input.reality_sni, F.text)
    async def set_sni_input(message: Message, state: FSMContext) -> None:
        domain = message.text.strip().lower()
        if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", domain):
            await message.answer("Это не похоже на домен. /cancel — отмена.")
            return
        await state.clear()
        check = await service.check_sni(domain)
        if "❌" in check and "✅" not in check:
            await message.answer(f"{html.escape(check)}\n\nSNI не изменён.")
            return
        db.set("reality_sni", domain)
        await apply(message)
        await message.answer(html.escape(check) + "\n\nКлиентам с подпиской достаточно обновить её.")
        await show(message, *settings_view())

    @router.callback_query(F.data == "set:check")
    async def check_sni(cb: CallbackQuery) -> None:
        await cb.answer("Проверяю…")
        await cb.message.answer(html.escape(await service.check_sni(db.get("reality_sni"))))

    @router.callback_query(F.data == "set:host")
    async def set_host(cb: CallbackQuery, state: FSMContext) -> None:
        if config.SERVER_HOST:
            await cb.answer("Адрес задан в .env (SERVER_HOST)", show_alert=True)
            return
        await state.set_state(Input.host)
        await show(cb, "Отправьте IP или домен, который будет в ключах. «auto» — определить IP заново.",
                   kb([("Отмена", "settings")]))

    @router.message(Input.host, F.text)
    async def set_host_input(message: Message, state: FSMContext) -> None:
        value = message.text.strip()
        await state.clear()
        if value.lower() == "auto":
            db.conn.execute("DELETE FROM settings WHERE key='host'")
            try:
                await service.detect_host()
            except RuntimeError as e:
                await message.answer(str(e))
        elif re.fullmatch(r"[A-Za-z0-9.:\-]+", value):
            db.set("host", value)
        else:
            await message.answer("Некорректный адрес.")
        await show(message, *settings_view())

    # ---------- backup ----------
    @router.callback_query(F.data == "backup")
    async def backup(cb: CallbackQuery) -> None:
        await cb.answer()
        await send_backup(service, cb.bot, cb.from_user.id)
        await cb.message.answer("Чтобы восстановить — просто отправьте этот файл боту.")

    @router.message(F.document)
    async def restore(message: Message, state: FSMContext) -> None:
        if not (message.document.file_name or "").endswith(".db"):
            await message.answer("Для восстановления отправьте файл бэкапа <code>.db</code>.")
            return
        with tempfile.TemporaryDirectory(dir=config.DATA_DIR) as tmp:
            path = Path(tmp) / "restore.db"
            await message.bot.download(message.document, destination=path)
            if not db.is_valid_backup(path):
                await message.answer("❌ Это не бэкап VPN Bot Lite.")
                return
            await service.collect_stats()
            db.close()
            for suffix in ("-wal", "-shm"):
                Path(str(db.path) + suffix).unlink(missing_ok=True)
            os.replace(path, db.path)
            db.open()
        await state.clear()
        service.init_settings()
        await service.awg.stop()  # the restored server key/parameters need a fresh interface
        await apply(message)
        await message.answer(f"✅ Восстановлено. Пользователей: {len(db.users())}", reply_markup=menu_markup())

    # ---------- logs ----------
    @router.callback_query(F.data == "logs")
    async def logs(cb: CallbackQuery) -> None:
        debug = db.get("debug_logs") == "1"
        await show(cb, "Какие логи показать?\n\nПодробные логи Xray и MTProto показывают каждое подключение — "
                       "включите, попробуйте подключиться и откройте нужные логи.",
                   kb([("Xray", "log:xray"), ("Hysteria2", "log:hysteria"), ("AmneziaWG", "log:amneziawg")],
                      [("MTProto", "log:mtproto")],
                      [(f"🔍 Подробные логи: {'вкл' if debug else 'выкл'}", "debuglogs")], BACK))

    @router.callback_query(F.data == "debuglogs")
    async def toggle_debug_logs(cb: CallbackQuery) -> None:
        db.set("debug_logs", "0" if db.get("debug_logs") == "1" else "1")
        await apply(cb)
        await logs(cb)

    @router.callback_query(F.data.startswith("log:"))
    async def show_logs(cb: CallbackQuery) -> None:
        core = core_by_name(cb.data.split(":")[1])
        text = "\n".join(list(core.logs)[-40:]) or "пусто"
        await cb.message.answer(f"<b>{core.name}</b>\n<pre>{html.escape(text[-3800:])}</pre>")
        await cb.answer()

    return router


async def send_backup(service: Service, bot: Bot, chat_id: int) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"vpnbot-{time.strftime('%Y%m%d-%H%M')}.db"
        service.db.backup_to(path)
        await bot.send_document(chat_id, FSInputFile(path), caption="💾 Бэкап VPN Bot Lite")
