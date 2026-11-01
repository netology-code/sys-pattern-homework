import base64
import ipaddress
import secrets
import sqlite3
import time
import uuid
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    uuid        TEXT NOT NULL,
    hy_pass     TEXT NOT NULL,
    token       TEXT UNIQUE NOT NULL,
    enabled     INTEGER NOT NULL DEFAULT 1,
    expire_at   INTEGER,
    limit_bytes INTEGER,
    up          INTEGER NOT NULL DEFAULT 0,
    down        INTEGER NOT NULL DEFAULT 0,
    created_at  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# columns added after the first release: (name, type)
MIGRATIONS = [("awg_private", "TEXT"), ("awg_public", "TEXT"), ("awg_psk", "TEXT"), ("awg_ip", "TEXT")]


def wg_keypair() -> tuple[str, str]:
    """WireGuard/AmneziaWG key pair in standard base64."""
    key = X25519PrivateKey.generate()
    private = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
                                serialization.NoEncryption())
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(private).decode(), base64.b64encode(public).decode()


def wg_psk() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


class DB:
    def __init__(self, path: Path):
        self.path = path
        self.conn: sqlite3.Connection | None = None
        self.open()

    def open(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        columns = {r["name"] for r in self.conn.execute("PRAGMA table_info(users)")}
        for name, kind in MIGRATIONS:
            if name not in columns:
                self.conn.execute(f"ALTER TABLE users ADD COLUMN {name} {kind}")

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    # --- settings ---
    def get(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )

    # --- users ---
    def users(self, only_enabled: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT * FROM users"
        if only_enabled:
            sql += " WHERE enabled=1"
        return self.conn.execute(sql + " ORDER BY name").fetchall()

    def user(self, user_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    def user_by_name(self, name: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()

    def user_by_token(self, token: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()

    def add_user(self, name: str, expire_at: int | None = None, limit_bytes: int | None = None) -> int:
        cur = self.conn.execute(
            "INSERT INTO users(name, uuid, hy_pass, token, expire_at, limit_bytes, created_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (name, str(uuid.uuid4()), secrets.token_urlsafe(16), secrets.token_urlsafe(16),
             expire_at, limit_bytes, int(time.time())),
        )
        return cur.lastrowid

    def ensure_awg(self, subnet: str) -> None:
        """Give every user AmneziaWG keys and a tunnel address (server takes the first host)."""
        net = ipaddress.ip_network(subnet, strict=False)
        hosts = [str(h) for h in net.hosts()][1:]
        users = self.conn.execute("SELECT id, awg_public, awg_ip FROM users ORDER BY id").fetchall()
        taken = {u["awg_ip"] for u in users if u["awg_ip"] in hosts}
        free = (h for h in hosts if h not in taken)
        seen: set[str] = set()
        for u in users:
            fields = {}
            if not u["awg_public"]:  # imported clients may have only the public key
                fields["awg_private"], fields["awg_public"] = wg_keypair()
                fields["awg_psk"] = wg_psk()
            ip = u["awg_ip"]
            if ip not in hosts or ip in seen:
                ip = next(free, None)
                if ip is None:
                    raise RuntimeError(f"В подсети {subnet} закончились адреса AmneziaWG")
                fields["awg_ip"] = ip
            seen.add(ip)
            if fields:
                self.update_user(u["id"], **fields)

    def update_user(self, user_id: int, **fields) -> None:
        cols = ", ".join(f"{k}=?" for k in fields)
        self.conn.execute(f"UPDATE users SET {cols} WHERE id=?", (*fields.values(), user_id))

    def delete_user(self, user_id: int) -> None:
        self.conn.execute("DELETE FROM users WHERE id=?", (user_id,))

    def add_traffic(self, name: str, up: int, down: int) -> None:
        self.conn.execute("UPDATE users SET up=up+?, down=down+? WHERE name=?", (up, down, name))

    def backup_to(self, dest: Path) -> None:
        target = sqlite3.connect(dest)
        with target:
            self.conn.backup(target)
        target.close()

    @staticmethod
    def is_valid_backup(path: Path) -> bool:
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            conn.close()
            return {"users", "settings"} <= tables
        except sqlite3.Error:
            return False
