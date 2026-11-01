import asyncio
import json
import logging
import ssl
import time

import aiohttp
import psutil
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand
from aiohttp import web

from . import config, watch
from .bot import setup
from .service import Service
from .sub import make_app

log = logging.getLogger("vpnbot")


async def notify(bot: Bot, text: str) -> None:
    for admin in config.ADMIN_IDS:
        try:
            await bot.send_message(admin, text)
        except TelegramAPIError as e:
            log.warning("cannot notify %s: %s", admin, e)


def sub_ssl_context() -> ssl.SSLContext | None:
    if not (config.SUB_CERT and config.SUB_KEY):
        return None
    ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ctx.load_cert_chain(config.SUB_CERT, config.SUB_KEY)
    return ctx


async def keep_reachable(service: Service, bot: Bot) -> None:
    """Every 5 minutes: point DuckDNS at the current IP. Every hour: check reachability from Russia, alert on change."""
    last_check = 0.0
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if config.DDNS_DOMAIN and config.DDNS_TOKEN:
                    ip = await watch.public_ip(session)
                    if ip and ip != service.db.get("ddns_ip"):
                        if await watch.duckdns_update(session, config.DDNS_DOMAIN, config.DDNS_TOKEN, ip):
                            old = service.db.get("ddns_ip")
                            service.db.set("ddns_ip", ip)
                            if old:
                                await notify(bot, f"🌐 IP сервера сменился: {old} → {ip}\n"
                                                  f"{config.DDNS_DOMAIN} уже указывает на новый адрес — "
                                                  "на устройствах ничего менять не нужно (DNS обновится за ~5 минут).")
                        else:
                            log.warning("duckdns update failed")
                if service.db.get("watch_enabled", "1") == "1" and time.time() - last_check > 3600:
                    last_check = time.time()
                    port = config.XHTTP_PORT or config.XRAY_PORT
                    result = await service.reach.check(session, service.host, port)
                    service.db.set("watch_last", json.dumps(result))
                    previous = service.db.get("watch_state", "ok")
                    if result["state"] != "error" and result["state"] != previous:
                        service.db.set("watch_state", result["state"])
                        await notify(bot, watch.describe(result, service.host, port))
            except Exception:  # noqa: BLE001 - the loop must survive
                log.exception("reachability job failed")
            await asyncio.sleep(300)


async def background(service: Service, bot: Bot, ssl_ctx: ssl.SSLContext | None) -> None:
    """Every minute: account traffic and disable expired users. Once a day: reload the subscription cert."""
    last_cert_reload = time.time()
    while True:
        await asyncio.sleep(60)
        try:
            await service.collect_stats()
            disabled = await service.enforce_limits()
            if disabled:
                await notify(bot, "⏸ Отключены пользователи:\n" + "\n".join(disabled))
            if ssl_ctx and time.time() - last_cert_reload > 86400:
                last_cert_reload = time.time()
                ssl_ctx.load_cert_chain(config.SUB_CERT, config.SUB_KEY)  # pick up a renewed certificate
        except Exception:  # noqa: BLE001 - the loop must survive
            log.exception("background job failed")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not config.BOT_TOKEN or not config.ADMIN_IDS:
        raise SystemExit("Задайте BOT_TOKEN и ADMIN_IDS в .env")

    service = Service()
    service.init_settings()
    try:
        await service.detect_host()
    except RuntimeError as e:
        log.warning("%s", e)
    psutil.cpu_percent()

    error = await service.apply()
    if error:
        log.error("cannot start cores: %s", error)

    runner = web.AppRunner(make_app(service), access_log=None)
    await runner.setup()
    ssl_ctx = sub_ssl_context()
    await web.TCPSite(runner, config.SUB_LISTEN, config.SUB_PORT, ssl_context=ssl_ctx).start()
    log.info("subscription server on %s:%s", "https" if ssl_ctx else "http", config.SUB_PORT)

    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(setup(service))
    await bot.set_my_commands([BotCommand(command="menu", description="Главное меню"),
                               BotCommand(command="cancel", description="Отменить ввод")])

    previous = service.db.get("bot_version")
    service.db.set("bot_version", config.VERSION)
    if previous and previous != config.VERSION:
        await notify(bot, f"✅ Бот обновлён: {previous} → {config.VERSION}")
    else:
        await notify(bot, f"🚀 VPN Bot Lite v{config.VERSION} запущен. /menu"
                          + (f"\n⚠️ {error}" if error else ""))

    # a webhook left by another bot on the same token (e.g. the old vpnbot) blocks polling
    await bot.delete_webhook(drop_pending_updates=False)
    task = asyncio.create_task(background(service, bot, ssl_ctx))
    reach_task = asyncio.create_task(keep_reachable(service, bot))
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        task.cancel()
        reach_task.cancel()
        await service.collect_stats()
        await service.xray.stop()
        await service.hysteria.stop()
        await service.awg.stop()
        await service.mtproto.stop()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
