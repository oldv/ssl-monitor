import os
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "ssl_monitor.db")
DB_PATH = os.environ.get("SSL_MONITOR_DB", DEFAULT_DB_PATH)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS domains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_id INTEGER NOT NULL,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_on DATE,
                issuer TEXT,
                days_left INTEGER,
                status TEXT CHECK(status IN ('valid', 'expired', 'error')) NOT NULL,
                error_msg TEXT,
                FOREIGN KEY (domain_id) REFERENCES domains(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_checks_domain_time
                ON checks(domain_id, check_time DESC);
            """
        )


def normalize_domain(value: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError("domain is required")

    # Strip scheme and path if present
    if "://" in value:
        parsed = urlparse(value)
        host = parsed.hostname or ""
        port = parsed.port
        if not host:
            raise ValueError("invalid domain")
        return f"{host}:{port}" if port else host

    value = value.split("/")[0]
    return value


def add_domain(domain: str):
    domain = normalize_domain(domain)
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO domains(domain, created_at) VALUES (?, ?)",
            (domain, datetime.utcnow().isoformat(sep=" ", timespec="seconds")),
        )
        return cur.lastrowid


def delete_domain(domain_id: int):
    with _connect() as conn:
        conn.execute("DELETE FROM domains WHERE id = ?", (domain_id,))


def get_all_domains():
    with _connect() as conn:
        rows = conn.execute("SELECT id, domain FROM domains ORDER BY domain").fetchall()
        return [dict(r) for r in rows]


def get_domains_with_latest_check():
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.domain,
                d.created_at,
                c.check_time,
                c.expires_on,
                c.issuer,
                c.days_left,
                c.status,
                c.error_msg
            FROM domains d
            LEFT JOIN checks c ON c.id = (
                SELECT id
                FROM checks
                WHERE domain_id = d.id
                ORDER BY check_time DESC
                LIMIT 1
            )
            ORDER BY d.domain
            """
        ).fetchall()
        return [dict(r) for r in rows]


def save_check_result(domain_id: int, result: dict):
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO checks(domain_id, expires_on, issuer, days_left, status, error_msg)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                domain_id,
                result.get("expires_on"),
                result.get("issuer"),
                result.get("days_left"),
                result.get("status"),
                result.get("error_msg"),
            ),
        )
