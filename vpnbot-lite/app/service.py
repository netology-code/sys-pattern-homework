"""Glue between the database and the cores: settings, links, applying configs, traffic accounting."""
import asyncio
import base64
import datetime
import hashlib
import ipaddress
import json
import logging
import random
import re
import secrets
import socket
import ssl
import time
from urllib.parse import quote, urlencode

import aiohttp
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.x509.oid import NameOID

from .watch import Reachability
from . import config
from .cores import AWG_PARAMS, XHTTP_CLIENT, AmneziaWG, Hysteria, MTProto, Xray, awg_client_lines
from .db import DB, wg_keypair

log = logging.getLogger(__name__)

DEFAULT_REALITY_SNI = "www.microsoft.com"
# Hysteria2 uses a self-signed certificate. Most clients (hysteria, sing-box, Hiddify, Streisand...) need
# insecure=1 to accept it, but Xray 26+ refuses `insecure` and accepts only a pinned certificate.
XRAY_CLIENTS = re.compile(r"happ|v2raytun|v2rayn|xray", re.IGNORECASE)
DEFAULT_HY_SNI = "www.bing.com"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def reality_keys() -> tuple[str, str]:
    key = X25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return b64url(private), b64url(public)


def self_signed_cert(cn: str) -> tuple[str, str]:
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(cn)]), critical=False)
            .sign(key, hashes.SHA256()))
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                serialization.NoEncryption()).decode()
    return cert_pem, key_pem


def cert_pin(cert_pem: str) -> str:
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    return hashlib.sha256(cert.public_bytes(serialization.Encoding.DER)).hexdigest()


def fmt_bytes(n: int | None) -> str:
    n = float(n or 0)
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if n < 1024 or unit == "ТБ":
            return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.2f} {unit}"
        n /= 1024
    return ""


class Service:
    def __init__(self):
        self.db = DB(config.DATA_DIR / "vpnbot.db")
        self.xray = Xray()
        self.hysteria = Hysteria()
        self.awg = AmneziaWG()
        self.mtproto = MTProto()
        self.reach = Reachability()
        self._apply_lock = asyncio.Lock()

    # --- settings ---
    def init_settings(self) -> None:
        db = self.db
        if not db.get("reality_private"):
            self.regenerate_reality()
        if not db.get("reality_sni"):
            db.set("reality_sni", DEFAULT_REALITY_SNI)
        if not db.get("hy_sni"):
            db.set("hy_sni", DEFAULT_HY_SNI)
        if not db.get("hy_cert"):
            cert, key = self_signed_cert(db.get("hy_sni"))
            db.set("hy_cert", cert)
            db.set("hy_key", key)
        for k, v in (("hy_stats_secret", secrets.token_hex(16)), ("hy_obfs_password", secrets.token_urlsafe(16)),
                     ("hy_obfs", "0"), ("block_ads", "0"), ("hy_enabled", "1"), ("awg_enabled", "1"),
                     ("reality_nosni", "1"), ("xhttp_enabled", "1"), ("xhttp_path", "/" + secrets.token_hex(6)),
                     ("mtproto_enabled", "0"), ("watch_enabled", "1")):
            if db.get(k) is None:
                db.set(k, v)
        if not db.get("awg_private"):
            self.regenerate_awg()
        db.ensure_awg(config.AWG_SUBNET)

    def regenerate_awg(self) -> None:
        """New server key and obfuscation parameters (all AmneziaWG configs must be re-issued)."""
        private, public = wg_keypair()
        while True:  # AmneziaWG 2.0: padded sizes of the four message types must all differ
            s1, s2, s3, s4 = random.randint(15, 150), random.randint(15, 150), random.randint(15, 64), \
                random.randint(0, 32)
            if len({148 + s1, 92 + s2, 64 + s3, 32 + s4}) == 4:
                break
        h = random.sample(range(5, 2 ** 31 - 1), 4)
        params = {"jc": 4, "jmin": 40, "jmax": 70, "s1": s1, "s2": s2, "s3": s3, "s4": s4,
                  "h1": h[0], "h2": h[1], "h3": h[2], "h4": h[3]}
        self.db.set("awg_private", private)
        self.db.set("awg_public", public)
        for k in AWG_PARAMS:  # drop 2.0 values left from an import, they belong to the old key
            self.db.conn.execute("DELETE FROM settings WHERE key=?", (f"awg_{k.lower()}",))
        for k, v in params.items():
            self.db.set(f"awg_{k}", str(v))

    def regenerate_reality(self) -> None:
        private, public = reality_keys()
        self.db.set("reality_private", private)
        self.db.set("reality_public", public)
        self.db.set("reality_sid", secrets.token_hex(8))

    def regenerate_hy_cert(self) -> None:
        cert, key = self_signed_cert(self.db.get("hy_sni"))
        self.db.set("hy_cert", cert)
        self.db.set("hy_key", key)

    def settings(self) -> dict:
        return {r["key"]: r["value"] for r in self.db.conn.execute("SELECT key, value FROM settings")}

    async def detect_host(self) -> str:
        if config.SERVER_HOST:
            return config.SERVER_HOST
        if self.db.get("host"):
            return self.db.get("host")
        async with aiohttp.ClientSession() as session:
            for url in ("https://api.ipify.org", "https://ifconfig.me/ip", "https://icanhazip.com"):
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        ip = (await r.text()).strip()
                        ipaddress.ip_address(ip)
                        self.db.set("host", ip)
                        return ip
                except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
                    continue
        raise RuntimeError("Не удалось определить внешний IP, задайте SERVER_HOST в .env")

    @property
    def host(self) -> str:
        return config.SERVER_HOST or self.db.get("host") or "127.0.0.1"

    def _host_for_url(self) -> str:
        try:
            if ipaddress.ip_address(self.host).version == 6:
                return f"[{self.host}]"
        except ValueError:
            pass
        return self.host

    async def check_sni(self, domain: str) -> str:
        """Can the server reach the REALITY target over TLS 1.3? Reality connects to it for every client."""
        lines = []
        for family, label in ((socket.AF_INET, "IPv4"), (socket.AF_INET6, "IPv6")):
            try:
                infos = await asyncio.get_running_loop().getaddrinfo(domain, 443, family=family,
                                                                     type=socket.SOCK_STREAM)
            except socket.gaierror:
                lines.append(f"{label}: нет адреса")
                continue
            ip = infos[0][4][0]
            ctx = ssl.create_default_context()
            started = time.monotonic()
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, 443, ssl=ctx, server_hostname=domain), 6)
                version = writer.get_extra_info("ssl_object").version()
                writer.close()
                ms = (time.monotonic() - started) * 1000
                mark = "✅" if version == "TLSv1.3" else "⚠️ нужен TLSv1.3,"
                lines.append(f"{label}: {mark} {version}, {ms:.0f} мс")
            except (OSError, asyncio.TimeoutError, ssl.SSLError) as e:
                lines.append(f"{label}: ❌ {type(e).__name__} {e}".strip())
        ok = any("✅" in line for line in lines)
        broken_v6 = any(line.startswith("IPv6: ❌") for line in lines)
        verdict = "годится" if ok else "НЕ годится — выберите другой сайт"
        if ok and broken_v6:
            verdict += " (но IPv6 на сервере не работает — если VLESS не подключается, выберите сайт без IPv6)"
        return f"Проверка {domain}: {verdict}\n" + "\n".join(lines)

    # --- links ---
    def sub_url(self, user) -> str:
        base = config.SUB_URL or f"http://{self._host_for_url()}:{config.SUB_PORT}"
        return f"{base}/sub/{user['token']}"

    def _reality_params(self, s: dict) -> dict:
        # without SNI the client sends no server name at all (like a direct connection to an IP)
        sni = "" if s.get("reality_nosni") == "1" else s["reality_sni"]
        return {"security": "reality", "encryption": "none", "pbk": s["reality_public"], "sid": s["reality_sid"],
                "sni": sni, "fp": "chrome"}

    def vless_link(self, user) -> str:
        s = self.settings()
        params = {"type": "tcp", "flow": "xtls-rprx-vision", **self._reality_params(s)}
        return (f"vless://{user['uuid']}@{self._host_for_url()}:{config.XRAY_PORT}"
                f"?{urlencode(params)}#{quote(user['name'] + ' Reality')}")

    def xhttp_link(self, user) -> str:
        s = self.settings()
        params = {"type": "xhttp", "path": s["xhttp_path"], "mode": "packet-up",
                  "extra": json.dumps(XHTTP_CLIENT, separators=(",", ":")), **self._reality_params(s)}
        return (f"vless://{user['uuid']}@{self._host_for_url()}:{config.XHTTP_PORT}"
                f"?{urlencode(params)}#{quote(user['name'] + ' XHTTP')}")

    def hy2_link(self, user, insecure: bool = True) -> str:
        """`pinSHA256`/`pcs` pin the self-signed certificate; `insecure=1` must be left out for Xray clients."""
        s = self.settings()
        pin = cert_pin(s["hy_cert"])
        params = {"sni": s["hy_sni"], "pinSHA256": pin, "pcs": pin}
        if insecure:
            params["insecure"] = "1"
        if s.get("hy_obfs") == "1":
            params.update({"obfs": "salamander", "obfs-password": s["hy_obfs_password"]})
        return (f"hysteria2://{quote(user['name'])}:{quote(user['hy_pass'])}@{self._host_for_url()}:"
                f"{config.HY2_PORT}/?{urlencode(params)}#{quote(user['name'] + ' Hysteria2')}")

    def links(self, user, user_agent: str = "") -> list[str]:
        links = [self.vless_link(user)]
        if config.XHTTP_PORT and self.db.get("xhttp_enabled") == "1":
            links.append(self.xhttp_link(user))
        if self.db.get("hy_enabled") == "1":
            links.append(self.hy2_link(user, insecure=not XRAY_CLIENTS.search(user_agent)))
        return links

    def mtproto_domain(self) -> str:
        """The fake-TLS name: chosen in the bot, else the server's own <ip>.nip.io (the name matches the IP)."""
        if self.db.get("mtproto_domain"):
            return self.db.get("mtproto_domain")
        try:
            ip = ipaddress.ip_address(self.host)
            if ip.version == 4:
                return f"{str(ip).replace('.', '-')}.nip.io"
        except ValueError:
            return self.host  # SERVER_HOST is a domain
        return "www.google.com"

    def regenerate_mtproto(self) -> None:
        domain = self.mtproto_domain()
        self.db.set("mtproto_secret", "ee" + secrets.token_hex(16) + domain.encode().hex())

    def mtproto_link(self) -> str:
        return (f"https://t.me/proxy?server={self.host}&port={config.MTPROTO_PORT}"
                f"&secret={self.db.get('mtproto_secret')}")

    def awg_conf(self, user) -> str | None:
        """Client config; None for clients imported without their private key."""
        if not user["awg_private"]:
            return None
        s = self.settings()
        lines = ["[Interface]", f"PrivateKey = {user['awg_private']}", f"Address = {user['awg_ip']}/32",
                 f"DNS = {config.AWG_DNS}", *awg_client_lines(s),
                 "", "[Peer]", f"PublicKey = {s['awg_public']}",
                 *([f"PresharedKey = {user['awg_psk']}"] if user["awg_psk"] else []),
                 f"Endpoint = {self._host_for_url()}:{config.AWG_PORT}",
                 "AllowedIPs = 0.0.0.0/0", "PersistentKeepalive = 25"]
        return "\n".join(lines) + "\n"

    # --- applying ---
    async def apply(self) -> str | None:
        """Regenerate configs and restart the cores. Returns an error text or None."""
        async with self._apply_lock:
            await self.collect_stats()
            users = self.db.users(only_enabled=True)
            s = self.settings()
            self.xray.write_config(users, s)
            error = await self.xray.check_config()
            if error:
                log.error("xray config error: %s", error)
                return f"Xray: {error}"
            await self.xray.restart()
            if s.get("hy_enabled") == "1" and users:
                self.hysteria.write_config(users, s)
                await self.hysteria.restart()
            else:
                await self.hysteria.stop()
            if config.MTPROTO_PORT and s.get("mtproto_enabled") == "1":
                if not s.get("mtproto_secret"):
                    self.regenerate_mtproto()
                    s = self.settings()
                if self.mtproto.write_config(s, self.host) or not self.mtproto.running:
                    await self.mtproto.restart()
            else:
                await self.mtproto.stop()
            try:
                self.db.ensure_awg(config.AWG_SUBNET)
                users = self.db.users(only_enabled=True)
                if s.get("awg_enabled") == "1" and users:
                    self.awg.write_config(users, s)
                    await self.awg.sync()
                else:
                    await self.awg.stop()
            except Exception as e:  # noqa: BLE001 - Xray/Hysteria keep working even if AWG can't start
                log.exception("amneziawg apply failed")
                return f"AmneziaWG: {e}"
            return None

    async def collect_stats(self) -> None:
        stats: dict[str, list[int]] = {}
        awg_names = {u["awg_public"]: u["name"] for u in self.db.users() if u["awg_public"]}
        for part in (await self.xray.pop_stats(),
                     await self.hysteria.pop_stats(self.db.get("hy_stats_secret", "")),
                     await self.awg.pop_stats(awg_names)):
            for name, (up, down) in part.items():
                acc = stats.setdefault(name, [0, 0])
                acc[0] += up
                acc[1] += down
        for name, (up, down) in stats.items():
            if up or down:
                self.db.add_traffic(name, up, down)

    async def enforce_limits(self) -> list[str]:
        """Disable users that are expired or out of traffic. Returns the reasons for notifications."""
        now = int(time.time())
        reasons = []
        for u in self.db.users(only_enabled=True):
            reason = None
            if u["expire_at"] and u["expire_at"] <= now:
                reason = "истёк срок"
            elif u["limit_bytes"] and u["up"] + u["down"] >= u["limit_bytes"]:
                reason = "исчерпан лимит трафика"
            if reason:
                self.db.update_user(u["id"], enabled=0)
                reasons.append(f"{u['name']}: {reason}")
        if reasons:
            await self.apply()
        return reasons

    def user_status(self, user) -> str:
        if not user["enabled"]:
            return "⏸"
        if user["expire_at"] and user["expire_at"] - time.time() < 3 * 86400:
            return "⏳"
        return "✅"
