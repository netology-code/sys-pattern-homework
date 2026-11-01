"""Xray and Hysteria2 cores: config generation, process supervision and updates."""
import asyncio
import collections
import io
import ipaddress
import json
import logging
import os
import platform
import re
import shutil
import stat
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path

import aiohttp

from . import config

log = logging.getLogger(__name__)

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
ARCH = {"x86_64": ("64", "amd64"), "amd64": ("64", "amd64"),
        "aarch64": ("arm64-v8a", "arm64"), "arm64": ("arm64-v8a", "arm64")}


def _arch() -> tuple[str, str]:
    machine = platform.machine().lower()
    if machine not in ARCH:
        raise RuntimeError(f"Неподдерживаемая архитектура: {machine}")
    return ARCH[machine]


async def latest_tag(session: aiohttp.ClientSession, repo: str) -> str:
    """Latest release tag. Uses the API first and the HTML redirect as a fallback (no rate limit)."""
    try:
        async with session.get(f"https://api.github.com/repos/{repo}/releases/latest",
                               timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                return (await r.json())["tag_name"]
    except (aiohttp.ClientError, asyncio.TimeoutError, KeyError):
        pass
    async with session.get(f"https://github.com/{repo}/releases/latest", allow_redirects=False,
                           timeout=aiohttp.ClientTimeout(total=15)) as r:
        location = r.headers.get("Location", "")
    if "/releases/tag/" not in location:
        raise RuntimeError(f"Не удалось узнать последнюю версию {repo}")
    return location.split("/releases/tag/", 1)[1]


def plain_version(tag: str | None) -> str | None:
    if not tag:
        return None
    m = re.search(r"(\d+\.\d+\.\d+)", tag)
    return m.group(1) if m else tag


class LogBuffer(collections.deque):
    """Recent lines in memory for the bot, also written to data/logs/<name>.log for `vpn.sh doctor`."""
    MAX_FILE = 512 * 1024

    def __init__(self, name: str):
        super().__init__(maxlen=300)
        self.path = config.DATA_DIR / "logs" / f"{name}.log"

    def append(self, line: str) -> None:
        super().append(line)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and self.path.stat().st_size > self.MAX_FILE:
                os.replace(self.path, self.path.with_suffix(".log.1"))
            with self.path.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
        except OSError:
            pass  # logs must never break a core


class Core:
    name = ""
    repo = ""
    version_re = r"(\d+\.\d+\.\d+)"
    noise: re.Pattern | None = None  # log lines not worth keeping

    def __init__(self):
        self.proc: asyncio.subprocess.Process | None = None
        self.logs = LogBuffer(self.name)
        self.wanted = False          # should the process be running
        self.started_at = 0.0
        self._lock = asyncio.Lock()
        self._watch: asyncio.Task | None = None

    # --- paths ---
    @property
    def config_path(self) -> Path:
        return config.DATA_DIR / f"{self.name}.json"

    @property
    def binary(self) -> Path:
        installed = config.BIN_DIR / self.name
        return installed if installed.exists() else config.BUILTIN_BIN_DIR / self.name

    def args(self) -> list[str]:
        raise NotImplementedError

    def env(self) -> dict[str, str]:
        return dict(os.environ)

    # --- version ---
    async def version(self, binary: Path | None = None) -> str | None:
        binary = binary or self.binary
        if not binary.exists():
            return None
        try:
            proc = await asyncio.create_subprocess_exec(
                str(binary), "version", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            out, _ = await asyncio.wait_for(proc.communicate(), 10)
        except (OSError, asyncio.TimeoutError):
            return None
        m = re.search(self.version_re, out.decode(errors="replace"))
        return m.group(1) if m else None

    # --- process ---
    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    async def start(self) -> None:
        async with self._lock:
            self.wanted = True
            await self._spawn()
        if not self._watch or self._watch.done():
            self._watch = asyncio.create_task(self._watchdog())

    async def stop(self) -> None:
        async with self._lock:
            self.wanted = False
            await self._kill()

    async def restart(self) -> None:
        async with self._lock:
            self.wanted = True
            await self._kill()
            await self._spawn()
        if not self._watch or self._watch.done():
            self._watch = asyncio.create_task(self._watchdog())

    async def _spawn(self) -> None:
        self.logs.append(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.proc = await asyncio.create_subprocess_exec(
            *self.args(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=self.env())
        self.started_at = time.time()
        asyncio.create_task(self._read_output(self.proc))
        try:
            await self.after_start()
        except Exception as e:  # noqa: BLE001 - keep the supervisor alive, the error goes to the logs
            log.exception("%s after_start failed", self.name)
            self.logs.append(f"!!! ошибка настройки: {e}")

    async def _kill(self) -> None:
        if not self.running:
            return
        self.proc.terminate()
        try:
            await asyncio.wait_for(self.proc.wait(), 5)
        except asyncio.TimeoutError:
            self.proc.kill()
            await self.proc.wait()
        await self.after_stop()

    async def after_start(self) -> None:
        """Hook: configure things around a freshly started process."""

    async def after_stop(self) -> None:
        """Hook: clean up after the process is stopped."""

    async def _read_output(self, proc: asyncio.subprocess.Process) -> None:
        async for line in proc.stdout:
            text = ANSI_RE.sub("", line.decode(errors="replace")).rstrip()
            if text and not (self.noise and self.noise.search(text)):
                self.logs.append(text)

    async def _watchdog(self) -> None:
        """Restart the process if it crashes; back off when it keeps crashing."""
        delay = 2
        while True:
            await asyncio.sleep(delay)
            if not self.wanted or self.running or self._lock.locked():
                delay = 2
                continue
            self.logs.append(f"!!! {self.name} упал (код {self.proc.returncode if self.proc else '?'}), перезапуск")
            log.warning("%s exited, restarting", self.name)
            try:
                async with self._lock:
                    if self.wanted and not self.running:
                        await self._spawn()
            except OSError as e:
                self.logs.append(f"!!! не удалось запустить: {e}")
            delay = min(delay * 2, 60)

    async def check_config(self) -> str | None:
        """Return an error text if the config is invalid, None if it is fine."""
        return None

    # --- updates ---
    def asset_url(self, tag: str) -> str:
        raise NotImplementedError

    def unpack(self, payload: bytes, dest: Path) -> None:
        raise NotImplementedError

    async def install(self, session: aiohttp.ClientSession, tag: str) -> str:
        """Download release `tag`, verify it runs, swap binaries (keeping a backup) and restart."""
        async with session.get(self.asset_url(tag), timeout=aiohttp.ClientTimeout(total=300)) as r:
            r.raise_for_status()
            payload = await r.read()
        config.BIN_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=config.DATA_DIR) as tmp:
            tmp = Path(tmp)
            self.unpack(payload, tmp)
            new_bin = tmp / self.name
            new_bin.chmod(new_bin.stat().st_mode | stat.S_IEXEC)
            new_version = await self.version(new_bin)
            if not new_version:
                raise RuntimeError("Скачанный файл не запускается")
            backup = config.BIN_DIR / "backup" / self.name
            if backup.exists():
                shutil.rmtree(backup)
            backup.mkdir(parents=True)
            for f in [self.binary.parent / self.name, *self.extra_files(self.binary.parent)]:
                if f.exists():
                    shutil.copy2(f, backup / f.name)
            for f in tmp.iterdir():
                os.replace(f, config.BIN_DIR / f.name)
        await self._restart_checked()
        return new_version

    def extra_files(self, directory: Path) -> list[Path]:
        return []

    def has_backup(self) -> bool:
        return (config.BIN_DIR / "backup" / self.name / self.name).exists()

    async def rollback(self) -> str | None:
        backup = config.BIN_DIR / "backup" / self.name
        if not (backup / self.name).exists():
            raise RuntimeError("Нет сохранённой предыдущей версии")
        config.BIN_DIR.mkdir(parents=True, exist_ok=True)
        for f in backup.iterdir():
            os.replace(f, config.BIN_DIR / f.name)  # rename works even while the old binary is running
        shutil.rmtree(backup)
        await self._restart_checked()
        return await self.version()

    async def _restart_checked(self) -> None:
        if self.wanted:
            await self.restart()


class Xray(Core):
    name = "xray"
    repo = "XTLS/Xray-core"
    version_re = r"Xray (\d+\.\d+\.\d+)"
    noise = re.compile(r"proxy: (Xtls|CopyRawConn|XtlsFilterTls)|XtlsPadding|Unpadding")

    def args(self) -> list[str]:
        return [str(self.binary), "run", "-c", str(self.config_path)]

    def env(self) -> dict[str, str]:
        return {**os.environ, "XRAY_LOCATION_ASSET": str(self.binary.parent)}

    def extra_files(self, directory: Path) -> list[Path]:
        return [directory / "geoip.dat", directory / "geosite.dat"]

    def asset_url(self, tag: str) -> str:
        return f"https://github.com/{self.repo}/releases/download/{tag}/Xray-linux-{_arch()[0]}.zip"

    def unpack(self, payload: bytes, dest: Path) -> None:
        with zipfile.ZipFile(io.BytesIO(payload)) as z:
            for member in ("xray", "geoip.dat", "geosite.dat"):
                if member in z.namelist():
                    z.extract(member, dest)

    async def check_config(self) -> str | None:
        proc = await asyncio.create_subprocess_exec(
            str(self.binary), "run", "-test", "-c", str(self.config_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=self.env())
        out, _ = await asyncio.wait_for(proc.communicate(), 20)
        return None if proc.returncode == 0 else out.decode(errors="replace")[-1500:]

    def write_config(self, users, s: dict) -> None:
        clients = [{"id": u["uuid"], "email": u["name"], "flow": "xtls-rprx-vision"} for u in users]
        if s.get("self_sni"):
            # our own site: anyone who isn't a client (DPI probes, browsers) gets a real page with a real certificate
            dest, names = f"127.0.0.1:{config.DECOY_PORT}", [s["self_sni"]]
        else:
            # "" accepts clients that send no SNI: DPI can't flag a borrowed name that isn't there
            dest, names = f"{s['reality_sni']}:443", ["", s["reality_sni"]]
        reality = {
            "show": False,
            "dest": dest,
            "xver": 0,
            "serverNames": names,
            "privateKey": s["reality_private"],
            "shortIds": [s["reality_sid"]],
        }
        sniffing = {"enabled": True, "destOverride": ["http", "tls", "quic"], "routeOnly": True}
        cfg = {
            # debug: every incoming connection and REALITY handshake error goes to the logs
            "log": ({"loglevel": "info"} if s.get("debug_logs") == "1"
                    else {"loglevel": "warning", "access": "none"}),
            "api": {"tag": "api", "listen": config.XRAY_API, "services": ["StatsService", "HandlerService"]},
            "stats": {},
            "policy": {
                "levels": {"0": {"statsUserUplink": True, "statsUserDownlink": True}},
                "system": {"statsInboundUplink": True, "statsInboundDownlink": True},
            },
            "inbounds": [{
                "tag": "vless-reality",
                "listen": "0.0.0.0",
                "port": config.XRAY_PORT,
                "protocol": "vless",
                "settings": {"clients": clients, "decryption": "none"},
                "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": reality},
                "sniffing": sniffing,
            }],
            "outbounds": [
                {"tag": "direct", "protocol": "freedom"},
                {"tag": "block", "protocol": "blackhole"},
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {"type": "field", "ip": ["geoip:private"], "outboundTag": "block"},
                    {"type": "field", "protocol": ["bittorrent"], "outboundTag": "block"},
                ],
            },
        }
        if config.XHTTP_PORT and s.get("xhttp_enabled") == "1":
            # many short HTTP requests instead of one long TLS stream: survives "freeze after N KB" throttling
            cfg["inbounds"].append({
                "tag": "vless-xhttp",
                "listen": "0.0.0.0",
                "port": config.XHTTP_PORT,
                "protocol": "vless",
                "settings": {"clients": [{"id": u["uuid"], "email": u["name"]} for u in users],
                             "decryption": "none"},
                "streamSettings": {"network": "xhttp", "xhttpSettings": {"path": s["xhttp_path"], "mode": "auto",
                                                                          **XHTTP_SERVER},
                                   "security": "reality", "realitySettings": reality},
                "sniffing": sniffing,
            })
        if s.get("block_ads") == "1":
            cfg["routing"]["rules"].append(
                {"type": "field", "domain": ["geosite:category-ads-all"], "outboundTag": "block"})
        self.config_path.write_text(json.dumps(cfg, indent=2))

    async def pop_stats(self) -> dict[str, list[int]]:
        """Read and reset per-user traffic counters: {name: [up, down]}."""
        if not self.running:
            return {}
        proc = await asyncio.create_subprocess_exec(
            str(self.binary), "api", "statsquery", f"--server={config.XRAY_API}",
            "-pattern", "user>>>", "-reset",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), 10)
            data = json.loads(out or b"{}")
        except (asyncio.TimeoutError, json.JSONDecodeError):
            return {}
        result: dict[str, list[int]] = {}
        for item in data.get("stat", []) or []:
            parts = item.get("name", "").split(">>>")  # user>>>name>>>traffic>>>uplink
            if len(parts) != 4:
                continue
            value = int(item.get("value", 0))
            pair = result.setdefault(parts[1], [0, 0])
            pair[0 if parts[3] == "uplink" else 1] += value
        return result


PRIVATE_NETS = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "169.254.0.0/16",
                "100.64.0.0/10", "fc00::/7", "fe80::/10", "::1/128"]


class Hysteria(Core):
    name = "hysteria"
    repo = "apernet/hysteria"
    version_re = r"Version:\s*v?(\d+\.\d+\.\d+)"

    def args(self) -> list[str]:
        return [str(self.binary), "server", "-c", str(self.config_path), "--disable-update-check"]

    def asset_url(self, tag: str) -> str:
        return f"https://github.com/{self.repo}/releases/download/{tag}/hysteria-linux-{_arch()[1]}"

    def unpack(self, payload: bytes, dest: Path) -> None:
        (dest / self.name).write_bytes(payload)

    def write_config(self, users, s: dict) -> None:
        tls_dir = config.DATA_DIR / "hysteria-tls"
        tls_dir.mkdir(parents=True, exist_ok=True)
        (tls_dir / "cert.pem").write_text(s["hy_cert"])
        key = tls_dir / "key.pem"
        key.write_text(s["hy_key"])
        key.chmod(0o600)
        cfg = {
            "listen": f":{config.HY2_PORT}",
            "tls": {"cert": str(tls_dir / "cert.pem"), "key": str(key)},
            "auth": {"type": "userpass", "userpass": {u["name"]: u["hy_pass"] for u in users}},
            "masquerade": {"type": "proxy", "proxy": {"url": f"https://{s['hy_sni']}/", "rewriteHost": True}},
            "trafficStats": {"listen": config.HY2_STATS, "secret": s["hy_stats_secret"]},
            "acl": {"inline": [*(f"reject({net})" for net in PRIVATE_NETS), "direct(all)"]},
        }
        if s.get("hy_obfs") == "1":
            cfg["obfs"] = {"type": "salamander", "salamander": {"password": s["hy_obfs_password"]}}
        self.config_path.write_text(json.dumps(cfg, indent=2))

    async def pop_stats(self, secret: str) -> dict[str, list[int]]:
        if not self.running:
            return {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{config.HY2_STATS}/traffic?clear=1",
                                       headers={"Authorization": secret},
                                       timeout=aiohttp.ClientTimeout(total=5)) as r:
                    data = await r.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
            return {}
        # hysteria: tx = sent to client (download), rx = received from client (upload)
        return {name: [int(v.get("rx", 0)), int(v.get("tx", 0))] for name, v in (data or {}).items()}


async def run(*cmd: str) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await asyncio.wait_for(proc.communicate(), 20)
    return proc.returncode, out.decode(errors="replace").strip()


class AmneziaWG(Core):
    """Userspace AmneziaWG (amneziawg-go). Built from source with the image, updated together with the bot."""
    name = "amneziawg"
    repo = ""

    def __init__(self):
        super().__init__()
        self._last: dict[str, tuple[int, int]] = {}
        self.dns_redirect: list[str] = []  # DNS servers of imported clients that only existed on the old server

    @property
    def config_path(self) -> Path:
        return config.DATA_DIR / f"{config.AWG_IFACE}.conf"

    @property
    def binary(self) -> Path:
        return config.BUILTIN_BIN_DIR / "amneziawg-go"

    @property
    def awg(self) -> str:
        return str(config.BUILTIN_BIN_DIR / "awg")

    def args(self) -> list[str]:
        return [str(self.binary), "-f", config.AWG_IFACE]

    def env(self) -> dict[str, str]:
        return {**os.environ, "LOG_LEVEL": "error"}

    async def version(self, binary: Path | None = None) -> str | None:
        if not self.binary.exists():
            return None
        code, out = await run(str(self.binary), "--version")
        m = re.search(r"amneziawg-go v?(\S+)", out)
        return m.group(1) if m else None

    def write_config(self, users, s: dict) -> None:
        self.dns_redirect = [ip for ip in (s.get("awg_dns_redirect") or "").split(",") if ip]
        lines = ["[Interface]", f"PrivateKey = {s['awg_private']}", f"ListenPort = {config.AWG_PORT}",
                 *awg_param_lines(s)]
        for u in users:
            lines += ["", "[Peer]", f"# {u['name']}", f"PublicKey = {u['awg_public']}",
                      *([f"PresharedKey = {u['awg_psk']}"] if u["awg_psk"] else []),
                      f"AllowedIPs = {u['awg_ip']}/32"]
        self.config_path.write_text("\n".join(lines) + "\n")
        self.config_path.chmod(0o600)

    async def sync(self) -> None:
        """Apply the peer list to the running interface without dropping connections."""
        if not self.running:
            await self.start()
            return
        code, out = await run(self.awg, "syncconf", config.AWG_IFACE, str(self.config_path))
        if code != 0:
            self.logs.append(f"syncconf: {out}")
            await self.restart()

    def _rules(self) -> list[tuple[str, str, list[str]]]:
        i = config.AWG_IFACE
        clamp = ["-p", "tcp", "--tcp-flags", "SYN,RST", "SYN", "-j", "TCPMSS", "--clamp-mss-to-pmtu"]
        dns = [("nat", "PREROUTING", ["-i", i, "-d", ip, "-p", proto, "--dport", "53",
                                      "-j", "DNAT", "--to-destination", "1.1.1.1:53"])
               for ip in self.dns_redirect for proto in ("udp", "tcp")]
        return [
            *dns,
            ("nat", "POSTROUTING", ["-s", config.AWG_SUBNET, "!", "-o", i, "-j", "MASQUERADE"]),
            ("filter", "FORWARD", ["-i", i, "-j", "ACCEPT"]),
            ("filter", "FORWARD", ["-o", i, "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED", "-j", "ACCEPT"]),
            ("mangle", "FORWARD", ["-i", i, *clamp]),
            ("mangle", "FORWARD", ["-o", i, *clamp]),
        ]

    async def after_start(self) -> None:
        sock = Path(f"/var/run/amneziawg/{config.AWG_IFACE}.sock")
        for _ in range(100):
            if sock.exists() or not self.running:
                break
            await asyncio.sleep(0.1)
        if not self.running:
            return
        self._last.clear()
        net = ipaddress.ip_network(config.AWG_SUBNET, strict=False)
        steps = [
            [self.awg, "setconf", config.AWG_IFACE, str(self.config_path)],
            ["ip", "address", "replace", f"{next(net.hosts())}/{net.prefixlen}", "dev", config.AWG_IFACE],
            ["ip", "link", "set", "dev", config.AWG_IFACE, "mtu", "1420", "up"],
        ]
        for table, chain, spec in self._rules():
            if (await run("iptables", "-t", table, "-C", chain, *spec))[0] != 0:
                # insert first so the rules win over Docker/ufw DROP policies
                steps.append(["iptables", "-t", table, "-I", chain, "1", *spec])
        for cmd in steps:
            code, out = await run(*cmd)
            if code != 0:
                raise RuntimeError(f"{' '.join(cmd[:3])}: {out}")

    async def after_stop(self) -> None:
        for table, chain, spec in self._rules():
            for _ in range(5):  # remove duplicates too
                if (await run("iptables", "-t", table, "-D", chain, *spec))[0] != 0:
                    break

    async def pop_stats(self, names: dict[str, str]) -> dict[str, list[int]]:
        """Traffic since the previous call. `names` maps public key -> user name."""
        if not self.running:
            return {}
        code, out = await run(self.awg, "show", config.AWG_IFACE, "transfer")
        if code != 0:
            return {}
        result: dict[str, list[int]] = {}
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3 or parts[0] not in names:
                continue
            rx, tx = int(parts[1]), int(parts[2])
            prev_rx, prev_tx = self._last.get(parts[0], (0, 0))
            if rx < prev_rx or tx < prev_tx:  # peer was re-added, counters restarted
                prev_rx, prev_tx = 0, 0
            self._last[parts[0]] = (rx, tx)
            # rx = received from the client (upload), tx = sent to the client (download)
            result[names[parts[0]]] = [rx - prev_rx, tx - prev_tx]
        return result


# XHTTP shaping as in the old vpnbot setup that works on the target network: random padding in every request,
# bounded POST sizes/intervals and connection reuse, so traffic does not form one recognisable long stream
XHTTP_SERVER = {"xPaddingBytes": "100-1000", "noSSEHeader": True, "scMaxBufferedPosts": 30,
                "scMaxEachPostBytes": 1000000, "scStreamUpServerSecs": "20-80"}
XHTTP_CLIENT = {"xPaddingBytes": "100-1000", "noGRPCHeader": False, "scMaxEachPostBytes": 1000000,
                "scMinPostsIntervalMs": 30, "scStreamUpServerSecs": "20-80",
                "xmux": {"maxConcurrency": "16-32", "maxConnections": 0, "cMaxReuseTimes": 0,
                         "hMaxRequestTimes": "600-900", "hMaxReusableSecs": "1800-3000", "hKeepAlivePeriod": 0}}

# AmneziaWG 1.0: Jc/Jmin/Jmax/S1/S2/H1-H4; 2.0 adds S3/S4 padding and I1-I5 signature packets
AWG_PARAMS = ("Jc", "Jmin", "Jmax", "S1", "S2", "S3", "S4", "H1", "H2", "H3", "H4", "I1", "I2", "I3", "I4", "I5")


# Junk (Jc/Jmin/Jmax) and signature packets (I1-I5) are sent only by the initiator before its handshake and the
# server drops them, so every client may have its own; S1-S4 and H1-H4 must match the server for all clients.
AWG_CLIENT_ONLY = ("Jc", "Jmin", "Jmax", "I1", "I2", "I3", "I4", "I5")
# What an HTTP/3 (QUIC v1) Initial from a browser looks like: long header with version 1, an 8-byte random DCID,
# empty SCID and token, length 1182 covering the random packet number and payload — 1200 bytes, QUIC's minimum
AWG_QUIC_I1 = "<b 0xc30000000108><r 8><b 0x0000449e><r 1182>"


def awg_param_lines(s: dict) -> list[str]:
    """Obfuscation parameters that are set (the server's view)."""
    return [f"{k} = {s['awg_' + k.lower()]}" for k in AWG_PARAMS if s.get("awg_" + k.lower())]


def awg_client_lines(s: dict) -> list[str]:
    """Parameters for a new client config: the server's, with a realistic QUIC Initial as the signature packet
    unless the admin chose to copy the server's own client-side values."""
    if s.get("awg_client_profile", "quic") != "quic":
        return awg_param_lines(s)
    shared = [line for line in awg_param_lines(s) if not line.startswith(("I1 ", "I2 ", "I3 ", "I4 ", "I5 "))]
    return [*shared, f"I1 = {AWG_QUIC_I1}"]


class MTProto(Core):
    """MTProto proxy for Telegram: telemt. Its fake-TLS replays the real certificate and TLS record sizes of
    the masking site, so the server's answer looks like that site's own (synthetic answers get detected)."""
    name = "telemt"
    repo = "telemt/telemt"
    version_re = r"telemt (\d+\.\d+\.\d+)"
    # keep client connections and problems; drop the chatter about telemt's own links to Telegram
    noise = re.compile(r" TRACE |ME RTT sample|mio::poll|STUN |(DEBUG|INFO) telemt::(transport::middle_proxy|network)")

    @property
    def workdir(self) -> Path:
        path = config.DATA_DIR / "telemt"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def config_path(self) -> Path:
        return self.workdir / "telemt.toml"

    def args(self) -> list[str]:
        return [str(self.binary), str(self.config_path)]

    async def version(self, binary: Path | None = None) -> str | None:
        binary = binary or self.binary
        if not binary.exists():
            return None
        code, out = await run(str(binary), "--version")
        m = re.search(self.version_re, out)
        return m.group(1) if m else None

    def asset_url(self, tag: str) -> str:
        arch = {"64": "x86_64", "arm64-v8a": "aarch64"}[_arch()[0]]
        return f"https://github.com/{self.repo}/releases/download/{tag}/telemt-{arch}-linux-musl.tar.gz"

    def unpack(self, payload: bytes, dest: Path) -> None:
        with tarfile.open(fileobj=io.BytesIO(payload)) as tar:
            member = next(m for m in tar.getmembers() if m.isfile() and Path(m.name).name == "telemt")
            (dest / self.name).write_bytes(tar.extractfile(member).read())

    def write_config(self, s: dict, host: str) -> bool:
        """Returns True when the config changed (telemt has to be restarted to pick it up)."""
        secret = s["mtproto_secret"]  # ee + 16 bytes key + hex(domain), the same string as in the link
        domain = bytes.fromhex(secret[34:]).decode()
        text = "\n".join([
            "[general]",
            f'log_level = "{"verbose" if s.get("debug_logs") == "1" else "normal"}"',
            "disable_colors = true",
            "[general.modes]",
            "classic = false",
            "secure = false",
            "tls = true",
            "[general.links]",
            f'public_host = "{host}"',
            f"public_port = {config.MTPROTO_PORT}",
            "[server]",
            f"port = {config.MTPROTO_PORT}",
            "[server.api]",
            "enabled = false",
            "[[server.listeners]]",
            'ip = "0.0.0.0"',
            "[censorship]",
            f'tls_domain = "{domain}"',
            "mask = true",  # probes get the real site
            "tls_emulation = true",
            f'tls_front_dir = "{self.workdir / "tlsfront"}"',
            "[access.users]",
            f'proxy = "{secret[2:34]}"',
            "",
        ])
        old = self.config_path.read_text() if self.config_path.exists() else ""
        self.config_path.write_text(text)
        return text != old

    async def _spawn(self) -> None:
        # telemt keeps its caches (Telegram proxy config, TLS fronting data) relative to the working dir
        self.logs.append(f"--- start {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        self.proc = await asyncio.create_subprocess_exec(
            *self.args(), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, env=self.env(),
            cwd=self.workdir)
        self.started_at = time.time()
        asyncio.create_task(self._read_output(self.proc))
