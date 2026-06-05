"""SQLite helpers for sessions, alerts, snapshots, and settings."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "db" / "pwd_box.sqlite"


def _utc_now() -> str:
    """Return the current UTC timestamp as ISO text."""
    return datetime.now(timezone.utc).isoformat()


def _resolve_db_path(db_path: Optional[str]) -> Path:
    """Resolve a database path to an absolute location."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


@contextmanager
def _connect(db_path: Optional[str] = None):
    """Context manager for a configured SQLite connection."""
    path = _resolve_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> Path:
    """Create required tables if they do not exist."""
    path = _resolve_db_path(db_path)
    with _connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interface TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL,
                pcap_path TEXT
            )
            """
        )
        _ensure_column(conn, "sessions", "pcap_path", "TEXT")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                session_id INTEGER NOT NULL,
                details TEXT,
                pcap_path TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS networks_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id INTEGER NOT NULL,
                ssid TEXT,
                bssid TEXT,
                channel INTEGER,
                rssi INTEGER,
                encryption TEXT,
                caps TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
    return path


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    """Add a column if the database schema is behind."""
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing = {str(row[1]) for row in rows}
    if column_name in existing:
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def create_session(
    interface: Optional[str],
    start_time: Optional[str] = None,
    status: str = "running",
    db_path: Optional[str] = None,
) -> int:
    """Insert a session row and return its id."""
    start = start_time or _utc_now()
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (interface, start_time, status) VALUES (?, ?, ?)",
            (interface, start, status),
        )
        return int(cursor.lastrowid)


def close_session(
    session_id: int,
    end_time: Optional[str] = None,
    status: str = "stopped",
    db_path: Optional[str] = None,
) -> None:
    """Update a session with end time and status."""
    end_ts = end_time or _utc_now()
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE sessions SET end_time = ?, status = ? WHERE id = ?",
            (end_ts, status, session_id),
        )


def update_session_pcap(
    session_id: int,
    pcap_path: Optional[str],
    db_path: Optional[str] = None,
) -> None:
    """Attach a PCAP path to a session row."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE sessions SET pcap_path = ? WHERE id = ?",
            (pcap_path, session_id),
        )


def log_alert(
    session_id: int,
    alert_data: Dict[str, Any],
    db_path: Optional[str] = None,
) -> int:
    """Insert an alert row and return its id."""
    timestamp = alert_data.get("timestamp") or _utc_now()
    alert_type = alert_data.get("alert_type", "unknown")
    details = json.dumps(alert_data.get("details", alert_data))
    pcap_path = alert_data.get("pcap_path")
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO alerts (timestamp, alert_type, session_id, details, pcap_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, alert_type, session_id, details, pcap_path),
        )
        return int(cursor.lastrowid)


def update_alert_pcap(
    alert_id: int, pcap_path: str, db_path: Optional[str] = None
) -> None:
    """Attach a PCAP path to an alert row."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE alerts SET pcap_path = ? WHERE id = ?",
            (pcap_path, alert_id),
        )


def log_network_snapshot(
    session_id: int,
    snapshot_data: Iterable[Dict[str, Any]],
    db_path: Optional[str] = None,
) -> None:
    """Insert a batch of network snapshot rows."""
    rows = []
    for snapshot in snapshot_data:
        rows.append(
            (
                snapshot.get("timestamp") or _utc_now(),
                session_id,
                snapshot.get("ssid"),
                snapshot.get("bssid"),
                snapshot.get("channel"),
                snapshot.get("rssi"),
                snapshot.get("encryption"),
                snapshot.get("caps"),
            )
        )
    if not rows:
        return
    with _connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO networks_snapshots (
                timestamp, session_id, ssid, bssid, channel, rssi, encryption, caps
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )


def list_alert_history(
    limit: int = 50,
    session_id: Optional[int] = None,
    alert_type: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return alerts filtered by session, type, or time range."""
    clauses = []
    params: List[Any] = []
    if session_id is not None:
        clauses.append("session_id = ?")
        params.append(session_id)
    if alert_type:
        clauses.append("alert_type = ?")
        params.append(alert_type)
    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    if until:
        clauses.append("timestamp <= ?")
        params.append(until)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = (
        "SELECT id, timestamp, alert_type, session_id, details, pcap_path "
        "FROM alerts" + where + " ORDER BY timestamp DESC, id DESC LIMIT ?"
    )
    params.append(int(limit))

    with _connect(db_path) as conn:
        cursor = conn.execute(query, params)
        results = []
        for row in cursor.fetchall():
            entry = dict(row)
            entry["details"] = _parse_details(entry.get("details"))
            results.append(entry)
        return results


def list_sessions(
    limit: int = 50,
    status: Optional[str] = None,
    interface: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return session rows filtered by status or time range."""
    clauses = []
    params: List[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if interface:
        clauses.append("interface = ?")
        params.append(interface)
    if since:
        clauses.append("start_time >= ?")
        params.append(since)
    if until:
        clauses.append("start_time <= ?")
        params.append(until)

    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = (
        "SELECT id, interface, start_time, end_time, status, pcap_path "
        "FROM sessions" + where + " ORDER BY start_time DESC, id DESC LIMIT ?"
    )
    params.append(int(limit))

    with _connect(db_path) as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def list_session_summaries(
    limit: int = 50,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return sessions with joined alert counts."""
    query = (
        "SELECT s.id, s.interface, s.start_time, s.end_time, s.status, s.pcap_path, "
        "COUNT(a.id) as alert_count "
        "FROM sessions s "
        "LEFT JOIN alerts a ON a.session_id = s.id "
        "GROUP BY s.id "
        "ORDER BY s.start_time DESC, s.id DESC "
        "LIMIT ?"
    )
    with _connect(db_path) as conn:
        cursor = conn.execute(query, (int(limit),))
        return [dict(row) for row in cursor.fetchall()]


def set_setting(key: str, value: Any, db_path: Optional[str] = None) -> None:
    """Store a JSON-encoded setting value."""
    payload = json.dumps(value)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, payload, _utc_now()),
        )


def get_setting(key: str, default: Any = None, db_path: Optional[str] = None) -> Any:
    """Load a setting value or return the default."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,),
        )
        row = cursor.fetchone()
        if not row:
            return default
        return _parse_details(row["value"], default)


def _parse_details(raw: Optional[str], default: Any = None) -> Any:
    """Parse JSON detail payloads safely."""
    if raw is None:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw
