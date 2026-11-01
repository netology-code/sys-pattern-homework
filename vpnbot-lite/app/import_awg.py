"""Import AmneziaWG from the old vpnbot (mercurykd/vpnbot) so existing clients keep working unchanged.

    python -m app.import_awg SERVER_CONF [CLIENTS_JSON] [--apply]

Without --apply only prints a summary (no keys). Takes the server key, obfuscation parameters and every peer
(public key, preshared key, address, name; private key and name from clients.json when present).
"""
import base64
import ipaddress
import json
import re
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

from . import config
from .cores import AWG_PARAMS
from .db import DB

NAME_RE = re.compile(r"[^A-Za-z0-9_.\-]")


def public_key(private_b64: str) -> str:
    key = X25519PrivateKey.from_private_bytes(base64.b64decode(private_b64))
    return base64.b64encode(key.public_key().public_bytes(serialization.Encoding.Raw,
                                                          serialization.PublicFormat.Raw)).decode()


def parse_conf(text: str) -> list[dict]:
    """[Interface]/[Peer] sections. Old vpnbot comments out disabled peers ('# PublicKey = ...') and keeps
    names as '## name = <name><unix time>'."""
    sections: list[dict] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.fullmatch(r"#*\s*\[(\w+)\]", line)
        if m:
            sections.append({"kind": m.group(1).lower(), "values": {}, "disabled": line.startswith("#")})
            continue
        if "=" not in line or not sections:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        section = sections[-1]
        if key.startswith("#"):
            bare = key.lstrip("#").strip()
            if bare.lower() == "name":
                section["name"] = value
                continue
            section["disabled"] = True
            key = bare
        section["values"][key] = value
    return sections


def clean_name(name: str | None, ip: str) -> str:
    name = re.sub(r"\d{10}$", "", name or "")  # old vpnbot appends time() to names
    name = NAME_RE.sub("_", name).strip("_.-")[:32]
    return name or f"awg-{ip.replace('.', '-')}"


def load(server_conf: Path, clients_json: Path | None) -> dict:
    sections = parse_conf(server_conf.read_text())
    iface = next(s["values"] for s in sections if s["kind"] == "interface")
    server_net = ipaddress.ip_interface(iface["Address"].split(",")[0].strip())
    clients = {}
    if clients_json and clients_json.exists():
        for c in json.loads(clients_json.read_text() or "[]") or []:
            ci = c.get("interface", {})
            if ci.get("PrivateKey"):
                clients[public_key(ci["PrivateKey"])] = ci
    peers = []
    for s in sections:
        if s["kind"] != "peer" or "PublicKey" not in s["values"]:
            continue
        v = s["values"]
        ip = v.get("AllowedIPs", "").split(",")[0].split("/")[0].strip()
        client = clients.get(v["PublicKey"], {})
        peers.append({
            "name": clean_name(s.get("name") or client.get("## name"), ip),
            "public": v["PublicKey"], "psk": v.get("PresharedKey"), "ip": ip,
            "private": client.get("PrivateKey"), "enabled": not s["disabled"],
        })
    # DNS servers the clients were given that lived only on the old server (AdGuard in Docker): redirect them
    dns = set()
    for ci in clients.values():
        for d in (ci.get("DNS") or "").split(","):
            d = d.strip()
            try:
                if d and ipaddress.ip_address(d).is_private and ipaddress.ip_address(d) != server_net.ip:
                    dns.add(d)
            except ValueError:
                pass
    return {
        "private": iface["PrivateKey"],
        "port": int(iface.get("ListenPort", 51820)),
        "subnet": str(server_net.network),
        "server_ip": str(server_net.ip),
        "params": {k: iface[k] for k in AWG_PARAMS if iface.get(k)},
        "peers": peers,
        "dns_redirect": sorted(dns),
    }


def summary(data: dict) -> str:
    lines = [
        f"Порт: {data['port']}/udp",
        f"Подсеть: {data['subnet']} (сервер {data['server_ip']})",
        "Маскировка: " + (", ".join(f"{k}={v}" for k, v in data["params"].items()) or "нет (обычный WireGuard)"),
        f"DNS старого сервера (будут перенаправлены на 1.1.1.1): {', '.join(data['dns_redirect']) or 'нет'}",
        f"Клиенты: {len(data['peers'])}",
    ]
    for p in data["peers"]:
        lines.append(f"  - {p['name']}: {p['ip']}, {'включён' if p['enabled'] else 'ОТКЛЮЧЁН'}, "
                     f"{'с приватным ключом' if p['private'] else 'без приватного ключа'}, "
                     f"{'с PresharedKey' if p['psk'] else 'без PresharedKey'}")
    if data["server_ip"] != str(next(ipaddress.ip_network(data["subnet"]).hosts())):
        lines.append(f"!!! Сервер не на первом адресе подсети ({data['server_ip']}) — импорт не поддерживается")
    return "\n".join(lines)


def apply(data: dict, db: DB) -> int:
    db.set("awg_private", data["private"])
    db.set("awg_public", public_key(data["private"]))
    for k in AWG_PARAMS:
        db.conn.execute("DELETE FROM settings WHERE key=?", (f"awg_{k.lower()}",))
    for k, v in data["params"].items():
        db.set(f"awg_{k.lower()}", v)
    db.set("awg_dns_redirect", ",".join(data["dns_redirect"]))
    db.set("awg_enabled", "1")
    known = {r["awg_public"] for r in db.conn.execute("SELECT awg_public FROM users")}
    added = 0
    for p in data["peers"]:
        if p["public"] in known:
            continue
        name, n = p["name"], 2
        while db.user_by_name(name):
            name, n = f"{p['name'][:29]}-{n}", n + 1
        user_id = db.add_user(name)
        db.update_user(user_id, awg_public=p["public"], awg_private=p["private"], awg_psk=p["psk"],
                       awg_ip=p["ip"], enabled=int(p["enabled"]))
        added += 1
    return added


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    data = load(Path(args[0]), Path(args[1]) if len(args) > 1 else None)
    print(summary(data))
    print(f"ENV AWG_PORT={data['port']}")
    print(f"ENV AWG_SUBNET={data['subnet']}")
    if "--apply" in argv:
        if data["server_ip"] != str(next(ipaddress.ip_network(data["subnet"]).hosts())):
            return 1
        added = apply(data, DB(config.DATA_DIR / "vpnbot.db"))
        print(f"Перенесено клиентов: {added}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
