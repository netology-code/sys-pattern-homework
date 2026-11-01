"""Keeping the server reachable: DuckDNS follows the server's IP, check-host.net shows whether Russia can reach it."""
import asyncio
import logging
import time

import aiohttp

log = logging.getLogger(__name__)

CHECK_HOST = "https://check-host.net"
ABROAD = ("de", "nl", "fi", "fr", "pl")  # control nodes: if these fail too, the server itself is down
HEADERS = {"Accept": "application/json"}


async def public_ip(session: aiohttp.ClientSession) -> str | None:
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    return (await r.text()).strip()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            continue
    return None


async def duckdns_update(session: aiohttp.ClientSession, domain: str, token: str, ip: str) -> bool:
    """Point <name>.duckdns.org at ip. DuckDNS answers OK or KO."""
    name = domain.removesuffix(".duckdns.org")
    try:
        async with session.get("https://www.duckdns.org/update", params={"domains": name, "token": token, "ip": ip},
                               timeout=aiohttp.ClientTimeout(total=15)) as r:
            return (await r.text()).strip() == "OK"
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        log.warning("duckdns: %s", e)
        return False


class Reachability:
    """Ping and TCP to the server from check-host.net nodes in Russia (plus a few abroad as a control)."""

    def __init__(self) -> None:
        self._nodes: tuple[float, dict] = (0.0, {})

    async def _get(self, session: aiohttp.ClientSession, path: str, **params) -> dict:
        async with session.get(CHECK_HOST + path, params=params, headers=HEADERS,
                               timeout=aiohttp.ClientTimeout(total=20)) as r:
            return await r.json(content_type=None)

    async def nodes(self, session: aiohttp.ClientSession) -> dict:
        loaded, nodes = self._nodes
        if not nodes or time.time() - loaded > 86400:
            nodes = (await self._get(session, "/nodes/hosts")).get("nodes", {})
            self._nodes = (time.time(), nodes)
        return nodes

    async def check(self, session: aiohttp.ClientSession, host: str, port: int) -> dict:
        """{'state': ok|partial|blocked|down|error, 'ru': [(asn, ping_ok, tcp_ok)], 'abroad': n_ok/n}."""
        try:
            nodes = await self.nodes(session)
            ru = [n for n, info in nodes.items() if info.get("location", [""])[0] == "ru"]
            abroad = [n for n, info in nodes.items() if info.get("location", [""])[0] in ABROAD][:4]
            if not ru:
                return {"state": "error", "error": "у check-host.net сейчас нет узлов в России"}
            picked = [("node", n) for n in ru + abroad]
            ids = {}
            for kind, target in (("ping", host), ("tcp", f"{host}:{port}")):
                async with session.get(f"{CHECK_HOST}/check-{kind}", params=[("host", target), *picked],
                                       headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as r:
                    ids[kind] = (await r.json(content_type=None))["request_id"]
            results = {}
            for _ in range(10):  # nodes report within ~5–20 s
                await asyncio.sleep(3)
                results = {k: await self._get(session, f"/check-result/{rid}") for k, rid in ids.items()}
                if all(v is not None for res in results.values() for v in res.values()):
                    break
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError) as e:
            return {"state": "error", "error": f"check-host.net недоступен: {e}"}

        def ok(kind: str, node: str) -> bool:
            res = results.get(kind, {}).get(node)
            if not res or not res[0]:
                return False
            if kind == "ping":
                return any(x and x[0] == "OK" for x in res[0])
            return isinstance(res[0], dict) and "time" in res[0]

        ru_rows = [(nodes[n].get("asn", "?"), nodes[n].get("location", ["", "", "?"])[2], ok("ping", n), ok("tcp", n))
                   for n in ru]
        abroad_ok = sum(ok("tcp", n) for n in abroad)
        ru_ok = sum(1 for _, _, p, t in ru_rows if t)
        if abroad and not abroad_ok:
            state = "down"
        elif ru_ok == len(ru_rows):
            state = "ok"
        elif ru_ok:
            state = "partial"
        else:
            state = "blocked"
        return {"state": state, "ru": ru_rows, "abroad": f"{abroad_ok}/{len(abroad)}", "time": int(time.time())}


STATE_TEXT = {
    "ok": "🟢 доступен из России",
    "partial": "🟡 из России доступен не у всех провайдеров — похоже на начало блокировки",
    "blocked": "🔴 недоступен из России — IP, видимо, заблокирован",
    "down": "⚫️ не отвечает ниоткуда — сервер или сеть хостера недоступны",
    "error": "⚪️ проверить не удалось",
}


def describe(result: dict, host: str, port: int) -> str:
    lines = [f"<b>Доступность {host}</b>: {STATE_TEXT.get(result['state'], result['state'])}"]
    if result.get("error"):
        lines.append(result["error"])
    for asn, city, ping_ok, tcp_ok in result.get("ru", []):
        lines.append(f"{city} {asn}: ping {'✅' if ping_ok else '❌'}, порт {port} {'✅' if tcp_ok else '❌'}")
    if result.get("abroad"):
        lines.append(f"Из-за рубежа (контроль): {result['abroad']} узлов отвечают")
    return "\n".join(lines)
