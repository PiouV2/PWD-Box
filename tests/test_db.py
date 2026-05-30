import sqlite3

try:
    from pwdbox.storage.db import (
        close_session,
        create_session,
        init_db,
        list_session_summaries,
        list_sessions,
        update_session_pcap,
    )
except ImportError:
    from storage.db import (
        close_session,
        create_session,
        init_db,
        list_session_summaries,
        list_sessions,
        update_session_pcap,
    )


def test_init_db_adds_session_pcap_column_for_existing_db(tmp_path) -> None:
    db_path = tmp_path / "pwd_box.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interface TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

    init_db(str(db_path))

    conn = sqlite3.connect(db_path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()]
    conn.close()

    assert "pcap_path" in columns


def test_session_pcap_path_is_returned_in_queries(tmp_path) -> None:
    db_path = tmp_path / "pwd_box.sqlite"
    init_db(str(db_path))

    session_id = create_session("wlan1", db_path=str(db_path))
    update_session_pcap(session_id, "/tmp/session-test.pcap", db_path=str(db_path))
    close_session(session_id, db_path=str(db_path))

    sessions = list_sessions(limit=5, db_path=str(db_path))
    summaries = list_session_summaries(limit=5, db_path=str(db_path))

    assert sessions[0]["pcap_path"] == "/tmp/session-test.pcap"
    assert summaries[0]["pcap_path"] == "/tmp/session-test.pcap"
