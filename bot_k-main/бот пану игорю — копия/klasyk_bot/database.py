"""
База данных: SQLite
Таблицы: users, content_submissions, schedule_events, signups, knowledge_items
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ITEMS

DB_PATH = Path(__file__).parent / "klasyk.db"
logger = logging.getLogger(__name__)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id    INTEGER PRIMARY KEY,
                username       TEXT,
                full_name      TEXT NOT NULL,
                class_name     TEXT NOT NULL,
                specs          TEXT NOT NULL,    -- JSON список
                software       TEXT,
                registered_at  TEXT NOT NULL,
                status         TEXT DEFAULT 'pending'  -- pending / active / inactive
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                telegram_id    INTEGER PRIMARY KEY,
                lang           TEXT DEFAULT 'ru'
            );

            CREATE TABLE IF NOT EXISTS content_submissions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id    INTEGER NOT NULL,
                submitter_name TEXT,
                content_type   TEXT NOT NULL,
                description    TEXT,
                location       TEXT,
                file_id        TEXT,
                file_type      TEXT,             -- photo / video / document / text
                submitted_at   TEXT NOT NULL,
                status         TEXT DEFAULT 'new'  -- new / approved / rejected
            );

            CREATE TABLE IF NOT EXISTS schedule_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                date_str    TEXT NOT NULL,
                time_str    TEXT,
                location    TEXT,
                description TEXT,
                created_by  INTEGER
            );

            CREATE TABLE IF NOT EXISTS signups (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                event_id    INTEGER NOT NULL,
                signed_up_at TEXT NOT NULL,
                UNIQUE(telegram_id, event_id)
            );

            CREATE TABLE IF NOT EXISTS knowledge_items (
                id          TEXT PRIMARY KEY,
                icon        TEXT NOT NULL,
                title       TEXT NOT NULL,
                text        TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
            """
        )
        _seed_demo_events(conn)
        _seed_knowledge_items(conn)
    logger.info("✅ БД инициализирована: %s", DB_PATH)


def _seed_demo_events(conn: sqlite3.Connection) -> None:
    """Добавить демо-мероприятия если таблица пустая."""
    count = conn.execute("SELECT COUNT(*) FROM schedule_events").fetchone()[0]
    if count == 0:
        events = [
            
        ]
        conn.executemany(
            "INSERT INTO schedule_events (title, date_str, time_str, location, description) VALUES (?,?,?,?,?)",
            events,
        )


def _seed_knowledge_items(conn: sqlite3.Connection) -> None:
    """Первичное заполнение базы знаний из config.py, если записей ещё нет."""
    count = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]
    if count == 0:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        conn.executemany(
            """
            INSERT INTO knowledge_items (id, icon, title, text, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (item["id"], item["icon"], item["title"], item["text"], now)
                for item in KNOWLEDGE_ITEMS
            ],
        )


# ──────────────────────────────────────────────
# USERS
# ──────────────────────────────────────────────

def upsert_user(
    telegram_id: int,
    username: str | None,
    full_name: str,
    class_name: str,
    specs: list[str],
    software: str,
) -> None:
    import json
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, class_name, specs, software, registered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name,
                class_name=excluded.class_name,
                specs=excluded.specs,
                software=excluded.software
            """,
            (telegram_id, username, full_name, class_name, json.dumps(specs, ensure_ascii=False), software,
             datetime.now().strftime("%d.%m.%Y %H:%M")),
        )


def get_user(telegram_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()


def is_registered(telegram_id: int) -> bool:
    return get_user(telegram_id) is not None


# ──────────────────────────────────────────────
# CONTENT SUBMISSIONS
# ──────────────────────────────────────────────

def save_submission(
    telegram_id: int,
    submitter_name: str,
    content_type: str,
    description: str,
    location: str,
    file_id: str | None,
    file_type: str,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO content_submissions
                (telegram_id, submitter_name, content_type, description, location, file_id, file_type, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, submitter_name, content_type, description, location,
             file_id, file_type, datetime.now().strftime("%d.%m.%Y %H:%M")),
        )
        return cur.lastrowid


# ──────────────────────────────────────────────
# SCHEDULE
# ──────────────────────────────────────────────

def get_upcoming_events() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM schedule_events ORDER BY id ASC LIMIT 10"
        ).fetchall()


def get_event(event_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM schedule_events WHERE id=?", (event_id,)).fetchone()


def signup_for_event(telegram_id: int, event_id: int) -> bool:
    """Записаться на съёмку. Возвращает False если уже записан."""
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO signups (telegram_id, event_id, signed_up_at) VALUES (?,?,?)",
                (telegram_id, event_id, datetime.now().strftime("%d.%m.%Y %H:%M")),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_signups(telegram_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT se.* FROM schedule_events se
            JOIN signups s ON s.event_id = se.id
            WHERE s.telegram_id = ?
            """,
            (telegram_id,),
        ).fetchall()


# ──────────────────────────────────────────────
# ADMIN — Пользователи
# ──────────────────────────────────────────────

def get_all_users() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM users ORDER BY registered_at DESC").fetchall()


def get_users_count() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM users WHERE status='pending'").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM users WHERE status='active'").fetchone()[0]
        inactive = conn.execute("SELECT COUNT(*) FROM users WHERE status='inactive'").fetchone()[0]
    return {"total": total, "pending": pending, "active": active, "inactive": inactive}


def set_user_status(telegram_id: int, status: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE users SET status=? WHERE telegram_id=?",
            (status, telegram_id),
        )
        return cur.rowcount > 0


def delete_user(telegram_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM signups WHERE telegram_id=?", (telegram_id,))
        cur = conn.execute("DELETE FROM users WHERE telegram_id=?", (telegram_id,))
        return cur.rowcount > 0


def get_users_by_status(status: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE status=? ORDER BY registered_at DESC",
            (status,),
        ).fetchall()


def get_active_user_ids() -> list[int]:
    """Все telegram_id зарегистрированных пользователей (для рассылки)."""
    with get_conn() as conn:
        rows = conn.execute("SELECT telegram_id FROM users").fetchall()
        return [r["telegram_id"] for r in rows]


# ──────────────────────────────────────────────
# ADMIN — Контент-заявки
# ──────────────────────────────────────────────

def get_all_submissions(status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    with get_conn() as conn:
        if status:
            return conn.execute(
                "SELECT * FROM content_submissions WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM content_submissions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_submission(sub_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM content_submissions WHERE id=?", (sub_id,)
        ).fetchone()


def set_submission_status(sub_id: int, status: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE content_submissions SET status=? WHERE id=?",
            (status, sub_id),
        )
        return cur.rowcount > 0


def get_submissions_count() -> dict:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM content_submissions").fetchone()[0]
        new = conn.execute("SELECT COUNT(*) FROM content_submissions WHERE status='new'").fetchone()[0]
        approved = conn.execute("SELECT COUNT(*) FROM content_submissions WHERE status='approved'").fetchone()[0]
        rejected = conn.execute("SELECT COUNT(*) FROM content_submissions WHERE status='rejected'").fetchone()[0]
    return {"total": total, "new": new, "approved": approved, "rejected": rejected}


# ──────────────────────────────────────────────
# ADMIN — События
# ──────────────────────────────────────────────

def add_event(title: str, date_str: str, time_str: str, location: str, description: str, created_by: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO schedule_events (title, date_str, time_str, location, description, created_by) VALUES (?,?,?,?,?,?)",
            (title, date_str, time_str, location, description, created_by),
        )
        return cur.lastrowid


def delete_event(event_id: int) -> bool:
    with get_conn() as conn:
        conn.execute("DELETE FROM signups WHERE event_id=?", (event_id,))
        cur = conn.execute("DELETE FROM schedule_events WHERE id=?", (event_id,))
        return cur.rowcount > 0


def get_event_signups(event_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT u.full_name, u.class_name, u.telegram_id, u.username, s.signed_up_at
            FROM signups s
            JOIN users u ON u.telegram_id = s.telegram_id
            WHERE s.event_id = ?
            ORDER BY s.signed_up_at
            """,
            (event_id,),
        ).fetchall()


def get_events_count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM schedule_events").fetchone()[0]


def get_signups_count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM signups").fetchone()[0]


# ──────────────────────────────────────────────
# KNOWLEDGE BASE
# ──────────────────────────────────────────────

def get_knowledge_items() -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM knowledge_items ORDER BY rowid ASC"
        ).fetchall()


def get_knowledge_item(item_id: str) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM knowledge_items WHERE id=?",
            (item_id,),
        ).fetchone()


def update_knowledge_item(item_id: str, text: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE knowledge_items
            SET text=?, updated_at=?
            WHERE id=?
            """,
            (text, datetime.now().strftime("%d.%m.%Y %H:%M"), item_id),
        )
        return cur.rowcount > 0


# ──────────────────────────────────────────────
# USER SETTINGS (language)
# ──────────────────────────────────────────────

def get_user_lang(telegram_id: int) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT lang FROM user_settings WHERE telegram_id=?", (telegram_id,)
        ).fetchone()
        return row["lang"] if row else None


def set_user_lang(telegram_id: int, lang: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO user_settings (telegram_id, lang) VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET lang=excluded.lang
            """,
            (telegram_id, lang),
        )
