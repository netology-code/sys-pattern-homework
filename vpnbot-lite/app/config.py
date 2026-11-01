import os
from pathlib import Path


def _int(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x}

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
BIN_DIR = DATA_DIR / "bin"          # binaries installed by the bot (updates)
BUILTIN_BIN_DIR = Path(os.environ.get("BUILTIN_BIN_DIR", "/opt/bin"))  # baked into the image

SERVER_HOST = os.environ.get("SERVER_HOST", "").strip()
XRAY_PORT = _int("XRAY_PORT", 443)
HY2_PORT = _int("HY2_PORT", 443)
XHTTP_PORT = _int("XHTTP_PORT", 8443)  # VLESS XHTTP + Reality; 0 disables
SUB_PORT = _int("SUB_PORT", 2096)
SUB_LISTEN = os.environ.get("SUB_LISTEN", "0.0.0.0").strip()  # 127.0.0.1 when Caddy serves HTTPS in front
AWG_PORT = _int("AWG_PORT", 51820)
MTPROTO_PORT = _int("MTPROTO_PORT", 8444)  # MTProto proxy for Telegram; 0 disables
AWG_IFACE = "awg0"
AWG_SUBNET = os.environ.get("AWG_SUBNET", "10.66.66.0/24").strip()
AWG_DNS = os.environ.get("AWG_DNS", "1.1.1.1, 8.8.8.8").strip()
# Public base URL for subscriptions, e.g. https://sub.example.com (if behind a reverse proxy)
SUB_URL = os.environ.get("SUB_URL", "").strip().rstrip("/")
# serve subscriptions over HTTPS with an existing certificate (e.g. the old vpnbot's Let's Encrypt one)
SUB_CERT = os.environ.get("SUB_CERT", "").strip()
SUB_KEY = os.environ.get("SUB_KEY", "").strip()

# REALITY "steal oneself": SNI is the server's own domain (SERVER_HOST), and probes see a real site with a real
# certificate — Caddy serves it on 127.0.0.1:DECOY_PORT (see `./vpn.sh stealth`)
SELF_SNI = os.environ.get("SELF_SNI", "").strip() == "1"
DECOY_PORT = _int("DECOY_PORT", 9443)

# DuckDNS: the bot keeps <name>.duckdns.org pointed at the server, so a new IP needs no changes on devices
DDNS_DOMAIN = os.environ.get("DDNS_DOMAIN", "").strip()
DDNS_TOKEN = os.environ.get("DDNS_TOKEN", "").strip()

XRAY_API = "127.0.0.1:10085"
HY2_STATS = "127.0.0.1:10086"

# URL of the VERSION file of the bot in the git repository, used to check for bot updates
BOT_VERSION_URL = os.environ.get("BOT_VERSION_URL", "").strip()

VERSION = (Path(__file__).resolve().parent.parent / "VERSION").read_text().strip()
