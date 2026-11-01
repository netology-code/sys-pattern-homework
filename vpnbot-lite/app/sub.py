"""HTTP subscription server: /sub/<token> returns links for v2rayN / Hiddify / v2RayTun / Happ / Streisand."""
import base64
import html
import io
import time

import qrcode
from aiohttp import web

from .service import Service, fmt_bytes

PAGE = """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:640px;margin:24px auto;padding:0 16px;
background:#f6f7f9;color:#111}}.c{{background:#fff;border-radius:12px;padding:16px;margin:12px 0;
box-shadow:0 1px 3px #0001}}code{{word-break:break-all;font-size:12px}}img{{max-width:240px}}
button{{padding:8px 14px;border:0;border-radius:8px;background:#2563eb;color:#fff;cursor:pointer}}
@media (prefers-color-scheme:dark){{body{{background:#111;color:#eee}}.c{{background:#1c1c1e}}}}</style>
</head><body><h2>{title}</h2><div class="c">{info}</div>
<div class="c"><b>Ссылка-подписка</b> — добавьте её в приложение (Hiddify, v2RayTun, Happ, v2rayN, Streisand):<br>
<p><code id="s">{sub}</code></p><button onclick="navigator.clipboard.writeText(document.getElementById('s').textContent)">
Копировать</button><p><img src="{sub}?qr=1" alt="QR"></p></div>
<div class="c"><b>Отдельные ключи</b>{keys}</div></body></html>"""


def qr_png(data: str) -> bytes:
    buf = io.BytesIO()
    qrcode.make(data, border=2).save(buf, format="PNG")
    return buf.getvalue()


def make_app(service: Service) -> web.Application:
    async def health(_: web.Request) -> web.Response:
        return web.Response(text="ok")

    async def sub(request: web.Request) -> web.Response:
        user = service.db.user_by_token(request.match_info["token"])
        if not user:
            raise web.HTTPNotFound()
        links = service.links(user, request.headers.get("User-Agent", "")) if user["enabled"] else []
        sub_url = service.sub_url(user)
        if request.query.get("qr"):
            return web.Response(body=qr_png(sub_url), content_type="image/png")

        accept = request.headers.get("Accept", "")
        if "text/html" in accept:
            status = "активна" if user["enabled"] else "отключена"
            expire = time.strftime("%d.%m.%Y", time.localtime(user["expire_at"])) if user["expire_at"] else "бессрочно"
            limit = fmt_bytes(user["limit_bytes"]) if user["limit_bytes"] else "без лимита"
            info = (f"Статус: <b>{status}</b><br>Действует до: {expire}<br>"
                    f"Трафик: {fmt_bytes(user['up'] + user['down'])} / {limit}")
            keys = "".join(f"<p><code>{html.escape(link)}</code></p>" for link in links) or "<p>—</p>"
            body = PAGE.format(title=html.escape(user["name"]), info=info, sub=html.escape(sub_url), keys=keys)
            return web.Response(text=body, content_type="text/html")

        headers = {
            "profile-title": "base64:" + base64.b64encode(f"VPN {user['name']}".encode()).decode(),
            "profile-update-interval": "12",
            "subscription-userinfo": (f"upload={user['up']}; download={user['down']}; "
                                      f"total={user['limit_bytes'] or 0}; expire={user['expire_at'] or 0}"),
            "content-disposition": f'attachment; filename="{user["name"]}"',
        }
        payload = base64.b64encode("\n".join(links).encode()).decode()
        return web.Response(text=payload, headers=headers)

    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/sub/{token}", sub)
    return app
