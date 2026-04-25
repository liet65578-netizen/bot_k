"""
Database: split architecture for minimal storage
─────────────────────────────────────────────────
data/
  global.db                  ← events, knowledge, user/submission indexes, signups
  users/{telegram_id}/
      data.db                ← profile, settings, submissions (Telegram file_id only)

Media is stored as Telegram file_id references — never actual file bytes.
This keeps the database size minimal regardless of media volume.
"""

import sqlite3
import json
import logging
import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from config import KNOWLEDGE_ITEMS_BY_LANG, KNOWLEDGE_LANG_FALLBACK_ORDER

# ── Paths (patched in tests) ─────────────────────────────────────────────────
DATA_DIR = Path(os.environ["BOT_DATA_DIR"]) if "BOT_DATA_DIR" in os.environ else Path(__file__).parent / "data"
GLOBAL_DB = DATA_DIR / "global.db"
USERS_DIR = DATA_DIR / "users"

logger = logging.getLogger(__name__)

# ── SQL Schemas ───────────────────────────────────────────────────────────────

_GLOBAL_SCHEMA = """
CREATE TABLE IF NOT EXISTS schedule_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    date_str    TEXT NOT NULL,
    time_str    TEXT,
    location    TEXT,
    description TEXT,
    created_by  INTEGER
);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id         TEXT NOT NULL,
    lang       TEXT NOT NULL,
    icon       TEXT NOT NULL,
    title      TEXT NOT NULL,
    text       TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (id, lang)
);

CREATE TABLE IF NOT EXISTS user_index (
    telegram_id    INTEGER PRIMARY KEY,
    username       TEXT,
    full_name      TEXT NOT NULL,
    class_name     TEXT NOT NULL,
    specs          TEXT NOT NULL,
    software       TEXT,
    registered_at  TEXT NOT NULL,
    status         TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS submission_index (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id    INTEGER NOT NULL,
    submitter_name TEXT,
    content_type   TEXT NOT NULL,
    file_type      TEXT,
    location       TEXT,
    submitted_at   TEXT NOT NULL,
    status         TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS signups (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id  INTEGER NOT NULL,
    event_id     INTEGER NOT NULL,
    signed_up_at TEXT NOT NULL,
    UNIQUE(telegram_id, event_id)
);
"""

_USER_SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    telegram_id    INTEGER PRIMARY KEY,
    username       TEXT,
    full_name      TEXT NOT NULL,
    class_name     TEXT NOT NULL,
    specs          TEXT NOT NULL,
    software       TEXT,
    registered_at  TEXT NOT NULL,
    status         TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS submissions (
    id             INTEGER PRIMARY KEY,
    content_type   TEXT NOT NULL,
    description    TEXT,
    location       TEXT,
    file_id        TEXT,
    file_unique_id TEXT,
    file_type      TEXT,
    file_size      INTEGER,
    mime_type      TEXT,
    text_content   TEXT,
    submitted_at   TEXT NOT NULL,
    status         TEXT DEFAULT 'new'
);
"""

# ── Connection helpers ────────────────────────────────────────────────────────

def _apply_pragmas(conn: sqlite3.Connection) -> None:
    """Per-connection pragmas for WAL performance."""
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")


def _optimize_db(conn: sqlite3.Connection) -> None:
    """One-time production SQLite settings. Safe to call repeatedly."""
    jm = conn.execute("PRAGMA journal_mode").fetchone()[0]
    if jm.lower() != "wal":
        conn.execute("PRAGMA journal_mode=WAL")
        logger.info("SQLite WAL enabled for %s", conn)
    av = conn.execute("PRAGMA auto_vacuum").fetchone()[0]
    if av == 0:
        conn.execute("PRAGMA auto_vacuum=INCREMENTAL")
        conn.execute("VACUUM")
        logger.info("SQLite auto_vacuum=INCREMENTAL set for %s", conn)


@contextmanager
def _get_global_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(GLOBAL_DB)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_user_db(telegram_id: int) -> Path:
    user_dir = USERS_DIR / str(telegram_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    db_path = user_dir / "data.db"
    if not db_path.exists():
        conn = sqlite3.connect(db_path)
        _apply_pragmas(conn)
        conn.executescript(_USER_SCHEMA)
        _optimize_db(conn)
        conn.close()
    return db_path


@contextmanager
def _get_user_conn(telegram_id: int):
    db_path = _ensure_user_db(telegram_id)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _apply_pragmas(conn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Init ──────────────────────────────────────────────────────────────────────

def init_db() -> None:
    with _get_global_conn() as conn:
        _optimize_db(conn)
        conn.executescript(_GLOBAL_SCHEMA)
        # Performance indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_status ON user_index(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_status ON submission_index(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sub_tid ON submission_index(telegram_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signups_tid ON signups(telegram_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_signups_eid ON signups(event_id)")
        _seed_demo_events(conn)
        _migrate_knowledge_items_lang(conn)
        _seed_knowledge_items(conn)
    # Migrate existing user DBs to WAL
    if USERS_DIR.exists():
        for d in USERS_DIR.iterdir():
            if d.is_dir() and (d / "data.db").exists():
                try:
                    c = sqlite3.connect(d / "data.db")
                    _optimize_db(c)
                    c.close()
                except Exception:
                    pass
    old_db = Path(__file__).parent / "klasyk.db"
    if old_db.exists():
        logger.warning("Old DB found: %s — not auto-migrated", old_db)
    logger.info("DB ready: %s", DATA_DIR)


def _seed_demo_events(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM schedule_events").fetchone()[0]
    if count == 0:
        events = []
        if events:
            conn.executemany(
                "INSERT INTO schedule_events (title, date_str, time_str, location, description) VALUES (?,?,?,?,?)",
                events,
            )


def _seed_knowledge_items(conn: sqlite3.Connection) -> None:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    for lang, items in KNOWLEDGE_ITEMS_BY_LANG.items():
        for item in items:
            # Seed if missing; never overwrite existing edits.
            exists = conn.execute(
                "SELECT 1 FROM knowledge_items WHERE id=? AND lang=?",
                (item["id"], lang),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT INTO knowledge_items (id, lang, icon, title, text, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (item["id"], lang, item["icon"], item["title"], item["text"], now),
            )


def _migrate_knowledge_items_lang(conn: sqlite3.Connection) -> None:
    """
    Migrate legacy knowledge_items schema (id as PK, no lang) to the new (id, lang) composite PK.
    Existing rows are preserved as lang='ru'.
    """
    cols = [r[1] for r in conn.execute("PRAGMA table_info(knowledge_items)").fetchall()]
    if "lang" in cols:
        return
    # Legacy schema detected → migrate.
    conn.execute("ALTER TABLE knowledge_items RENAME TO knowledge_items_legacy")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id         TEXT NOT NULL,
            lang       TEXT NOT NULL,
            icon       TEXT NOT NULL,
            title      TEXT NOT NULL,
            text       TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (id, lang)
        );
        """
    )
    rows = conn.execute("SELECT id, icon, title, text, updated_at FROM knowledge_items_legacy").fetchall()
    for r in rows:
        conn.execute(
            "INSERT INTO knowledge_items (id, lang, icon, title, text, updated_at) VALUES (?, 'ru', ?, ?, ?, ?)",
            (r["id"], r["icon"], r["title"], r["text"], r["updated_at"]),
        )
    conn.execute("DROP TABLE knowledge_items_legacy")


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
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    specs_json = json.dumps(specs, ensure_ascii=False) if isinstance(specs, list) else specs
    params = (telegram_id, username, full_name, class_name, specs_json, software, now)
    upsert_sql = """
        INSERT INTO {table} (telegram_id, username, full_name, class_name, specs, software, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username=excluded.username, full_name=excluded.full_name,
            class_name=excluded.class_name, specs=excluded.specs,
            software=excluded.software
    """
    with _get_global_conn() as conn:
        conn.execute(upsert_sql.format(table="user_index"), params)
    with _get_user_conn(telegram_id) as conn:
        conn.execute(upsert_sql.format(table="profile"), params)


def get_user(telegram_id: int) -> sqlite3.Row | None:
    with _get_global_conn() as conn:
        return conn.execute(
            "SELECT * FROM user_index WHERE telegram_id=?", (telegram_id,)
        ).fetchone()


def is_registered(telegram_id: int) -> bool:
    return get_user(telegram_id) is not None


def get_user_status(telegram_id: int) -> str | None:
    """Return 'pending', 'active', 'inactive' or None if user not in DB."""
    row = get_user(telegram_id)
    return row["status"] if row else None


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
    file_unique_id: str | None = None,
    file_size: int | None = None,
    mime_type: str | None = None,
    text_content: str | None = None,
) -> int:
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    # 1. Global index → canonical ID
    with _get_global_conn() as conn:
        cur = conn.execute(
            """INSERT INTO submission_index
                (telegram_id, submitter_name, content_type, file_type, location, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (telegram_id, submitter_name, content_type, file_type, location, now),
        )
        sub_id = cur.lastrowid
    # 2. Per-user DB — full data with file_id (no file bytes)
    with _get_user_conn(telegram_id) as conn:
        conn.execute(
            """INSERT INTO submissions
                (id, content_type, description, location, file_id, file_unique_id,
                 file_type, file_size, mime_type, text_content, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sub_id, content_type, description, location, file_id, file_unique_id,
             file_type, file_size, mime_type, text_content, now),
        )
    return sub_id


# ──────────────────────────────────────────────
# SCHEDULE
# ──────────────────────────────────────────────

def get_upcoming_events() -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        return conn.execute(
            "SELECT * FROM schedule_events ORDER BY id ASC LIMIT 10"
        ).fetchall()


def get_event(event_id: int) -> sqlite3.Row | None:
    with _get_global_conn() as conn:
        return conn.execute(
            "SELECT * FROM schedule_events WHERE id=?", (event_id,)
        ).fetchone()


def signup_for_event(telegram_id: int, event_id: int) -> bool:
    try:
        with _get_global_conn() as conn:
            conn.execute(
                "INSERT INTO signups (telegram_id, event_id, signed_up_at) VALUES (?,?,?)",
                (telegram_id, event_id, datetime.now().strftime("%d.%m.%Y %H:%M")),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_signups(telegram_id: int) -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        return conn.execute(
            """SELECT se.* FROM schedule_events se
            JOIN signups s ON s.event_id = se.id
            WHERE s.telegram_id = ?""",
            (telegram_id,),
        ).fetchall()


# ──────────────────────────────────────────────
# ADMIN — Пользователи
# ──────────────────────────────────────────────

def get_all_users() -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        return conn.execute(
            "SELECT * FROM user_index ORDER BY registered_at DESC"
        ).fetchall()


def get_users_count() -> dict:
    with _get_global_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM user_index GROUP BY status"
        ).fetchall()
    counts = {"total": 0, "pending": 0, "active": 0, "inactive": 0}
    for row in rows:
        s = row["status"]
        if s in counts:
            counts[s] = row["cnt"]
        counts["total"] += row["cnt"]
    return counts


def set_user_status(telegram_id: int, status: str) -> bool:
    with _get_global_conn() as conn:
        cur = conn.execute(
            "UPDATE user_index SET status=? WHERE telegram_id=?", (status, telegram_id)
        )
        changed = cur.rowcount > 0
    db_path = USERS_DIR / str(telegram_id) / "data.db"
    if db_path.exists():
        with _get_user_conn(telegram_id) as conn:
            conn.execute("UPDATE profile SET status=? WHERE telegram_id=?", (status, telegram_id))
    return changed


def delete_user(telegram_id: int) -> bool:
    with _get_global_conn() as conn:
        conn.execute("DELETE FROM signups WHERE telegram_id=?", (telegram_id,))
        conn.execute("DELETE FROM submission_index WHERE telegram_id=?", (telegram_id,))
        cur = conn.execute("DELETE FROM user_index WHERE telegram_id=?", (telegram_id,))
        deleted = cur.rowcount > 0
    user_dir = USERS_DIR / str(telegram_id)
    if user_dir.exists():
        shutil.rmtree(user_dir)
    return deleted


def get_users_by_status(status: str) -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        return conn.execute(
            "SELECT * FROM user_index WHERE status=? ORDER BY registered_at DESC",
            (status,),
        ).fetchall()


def get_active_user_ids() -> list[int]:
    with _get_global_conn() as conn:
        rows = conn.execute("SELECT telegram_id FROM user_index WHERE status = 'active'").fetchall()
        return [r["telegram_id"] for r in rows]


# ──────────────────────────────────────────────
# ADMIN — Контент-заявки
# ──────────────────────────────────────────────

def get_all_submissions(status: str | None = None, limit: int = 20) -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        if status:
            return conn.execute(
                "SELECT * FROM submission_index WHERE status=? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return conn.execute(
            "SELECT * FROM submission_index ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def get_submission(sub_id: int) -> dict | None:
    """Full submission data: global index + file_id from user's DB."""
    with _get_global_conn() as conn:
        idx = conn.execute(
            "SELECT * FROM submission_index WHERE id=?", (sub_id,)
        ).fetchone()
    if not idx:
        return None
    result = dict(idx)
    # Enrich with file data from per-user DB
    tid = idx["telegram_id"]
    db_path = USERS_DIR / str(tid) / "data.db"
    if db_path.exists():
        with _get_user_conn(tid) as uconn:
            row = uconn.execute(
                "SELECT * FROM submissions WHERE id=?", (sub_id,)
            ).fetchone()
        if row:
            result["description"] = row["description"]
            result["file_id"] = row["file_id"]
            result["file_unique_id"] = row["file_unique_id"]
            result["file_size"] = row["file_size"]
            result["mime_type"] = row["mime_type"]
            result["text_content"] = row["text_content"]
    result.setdefault("description", "")
    result.setdefault("file_id", None)
    result.setdefault("file_unique_id", None)
    result.setdefault("file_size", None)
    result.setdefault("mime_type", None)
    result.setdefault("text_content", None)
    return result


def set_submission_status(sub_id: int, status: str) -> bool:
    with _get_global_conn() as conn:
        cur = conn.execute(
            "UPDATE submission_index SET status=? WHERE id=?", (status, sub_id)
        )
        changed = cur.rowcount > 0
        row = conn.execute(
            "SELECT telegram_id FROM submission_index WHERE id=?", (sub_id,)
        ).fetchone()
    if row:
        db_path = USERS_DIR / str(row["telegram_id"]) / "data.db"
        if db_path.exists():
            with _get_user_conn(row["telegram_id"]) as uconn:
                uconn.execute("UPDATE submissions SET status=? WHERE id=?", (status, sub_id))
    return changed


def get_submissions_count() -> dict:
    with _get_global_conn() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM submission_index GROUP BY status"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM submission_index").fetchone()[0]
    counts = {"total": total, "new": 0, "approved": 0, "rejected": 0}
    for row in rows:
        s = row["status"]
        if s in counts:
            counts[s] = row["cnt"]
    return counts


# ──────────────────────────────────────────────
# ADMIN — События
# ──────────────────────────────────────────────

def add_event(title: str, date_str: str, time_str: str, location: str, description: str, created_by: int) -> int:
    with _get_global_conn() as conn:
        cur = conn.execute(
            "INSERT INTO schedule_events (title, date_str, time_str, location, description, created_by) VALUES (?,?,?,?,?,?)",
            (title, date_str, time_str, location, description, created_by),
        )
        return cur.lastrowid


def delete_event(event_id: int) -> bool:
    with _get_global_conn() as conn:
        conn.execute("DELETE FROM signups WHERE event_id=?", (event_id,))
        cur = conn.execute("DELETE FROM schedule_events WHERE id=?", (event_id,))
        return cur.rowcount > 0


def get_event_signups(event_id: int) -> list[sqlite3.Row]:
    with _get_global_conn() as conn:
        return conn.execute(
            """SELECT ui.full_name, ui.class_name, ui.telegram_id, ui.username, s.signed_up_at
            FROM signups s
            JOIN user_index ui ON ui.telegram_id = s.telegram_id
            WHERE s.event_id = ?
            ORDER BY s.signed_up_at""",
            (event_id,),
        ).fetchall()


def get_events_count() -> int:
    with _get_global_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM schedule_events").fetchone()[0]


def get_signups_count() -> int:
    with _get_global_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM signups").fetchone()[0]


# ──────────────────────────────────────────────
# KNOWLEDGE BASE
# ──────────────────────────────────────────────

def get_knowledge_items(lang: str) -> list[sqlite3.Row]:
    """
    Return knowledge items for requested lang. If empty, fall back to the first available language
    from KNOWLEDGE_LANG_FALLBACK_ORDER.
    """
    order = [lang] + [l for l in KNOWLEDGE_LANG_FALLBACK_ORDER if l != lang]
    with _get_global_conn() as conn:
        for l in order:
            rows = conn.execute(
                "SELECT * FROM knowledge_items WHERE lang=? ORDER BY rowid ASC",
                (l,),
            ).fetchall()
            if rows:
                return rows
        return []


def get_knowledge_item(item_id: str, lang: str) -> sqlite3.Row | None:
    order = [lang] + [l for l in KNOWLEDGE_LANG_FALLBACK_ORDER if l != lang]
    with _get_global_conn() as conn:
        for l in order:
            row = conn.execute(
                "SELECT * FROM knowledge_items WHERE id=? AND lang=?",
                (item_id, l),
            ).fetchone()
            if row:
                return row
        return None


def update_knowledge_item(item_id: str, lang: str, text: str) -> bool:
    with _get_global_conn() as conn:
        cur = conn.execute(
            "UPDATE knowledge_items SET text=?, updated_at=? WHERE id=? AND lang=?",
            (text, datetime.now().strftime("%d.%m.%Y %H:%M"), item_id, lang),
        )
        return cur.rowcount > 0


# ──────────────────────────────────────────────
# USER SETTINGS (language) — per-user DB
# ──────────────────────────────────────────────

def get_user_lang(telegram_id: int) -> str | None:
    db_path = USERS_DIR / str(telegram_id) / "data.db"
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT value FROM settings WHERE key='lang'").fetchone()
        return row["value"] if row else None
    finally:
        conn.close()


def set_user_lang(telegram_id: int, lang: str) -> None:
    with _get_user_conn(telegram_id) as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('lang', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (lang,),
        )


# ──────────────────────────────────────────────
# STORAGE MONITORING
# ──────────────────────────────────────────────

def _dir_size(path: Path) -> int:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                pass
    return total


def get_storage_stats() -> dict:
    """Storage overview scoped to the bot's own directory."""
    stats: dict = {}

    bot_dir = Path(__file__).resolve().parent

    # Bot code (handlers, locales, py files — excluding venv and data)
    code_size = 0
    for f in bot_dir.iterdir():
        if f.name in ("venv", "data", "data_test", "logs", "logs_test"):
            continue
        if f.is_file():
            try:
                code_size += f.stat().st_size
            except OSError:
                pass
        elif f.is_dir():
            code_size += _dir_size(f)
    stats["code_size"] = code_size

    # venv
    venv_dir = bot_dir / "venv"
    stats["venv_size"] = _dir_size(venv_dir) if venv_dir.exists() else 0

    # Data directory
    stats["data_size"] = _dir_size(DATA_DIR) if DATA_DIR.exists() else 0

    # Global DB
    stats["global_db_size"] = GLOBAL_DB.stat().st_size if GLOBAL_DB.exists() else 0

    # Global DB journal_mode
    try:
        with _get_global_conn() as conn:
            stats["journal_mode"] = conn.execute("PRAGMA journal_mode").fetchone()[0]
    except Exception:
        stats["journal_mode"] = "?"

    # User DBs
    user_count = 0
    user_db_total = 0
    if USERS_DIR.exists():
        for d in USERS_DIR.iterdir():
            if d.is_dir():
                user_count += 1
                db = d / "data.db"
                if db.exists():
                    user_db_total += db.stat().st_size
    stats["user_count"] = user_count
    stats["user_db_total"] = user_db_total

    # Logs (current env only)
    env = os.getenv("BOT_ENV", "")
    logs_dir = bot_dir / (f"logs_{env}" if env else "logs")
    stats["logs_size"] = _dir_size(logs_dir) if logs_dir.exists() else 0

    # Both log dirs (prod + test) if we're looking at the folder
    stats["all_logs_size"] = sum(
        _dir_size(d) for d in bot_dir.iterdir()
        if d.is_dir() and d.name.startswith("logs")
    )

    # Bot total = code + venv + all data dirs + all logs
    stats["bot_total"] = (
        code_size + stats["venv_size"] +
        sum(_dir_size(d) for d in bot_dir.iterdir()
            if d.is_dir() and (d.name.startswith("data") or d.name.startswith("logs")))
    )

    # Table row counts
    with _get_global_conn() as conn:
        stats["rows_users"] = conn.execute("SELECT COUNT(*) FROM user_index").fetchone()[0]
        stats["rows_submissions"] = conn.execute("SELECT COUNT(*) FROM submission_index").fetchone()[0]
        stats["rows_events"] = conn.execute("SELECT COUNT(*) FROM schedule_events").fetchone()[0]
        stats["rows_signups"] = conn.execute("SELECT COUNT(*) FROM signups").fetchone()[0]
        stats["rows_knowledge"] = conn.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()[0]

    return stats


def get_top_users_by_storage(limit: int = 10) -> list[dict]:
    """Top users by their database file size."""
    users: list[dict] = []
    if not USERS_DIR.exists():
        return users
    for d in USERS_DIR.iterdir():
        if d.is_dir():
            db = d / "data.db"
            size = db.stat().st_size if db.exists() else 0
            try:
                tid = int(d.name)
            except ValueError:
                continue
            users.append({"telegram_id": tid, "size": size})
    users.sort(key=lambda x: x["size"], reverse=True)
    return users[:limit]


def get_users_over_threshold(threshold_bytes: int = 1_073_741_824) -> list[dict]:
    """Users whose data directory exceeds threshold (default 1 GB)."""
    result: list[dict] = []
    if not USERS_DIR.exists():
        return result
    for d in USERS_DIR.iterdir():
        if d.is_dir():
            dir_size = _dir_size(d)
            if dir_size > threshold_bytes:
                try:
                    tid = int(d.name)
                except ValueError:
                    continue
                result.append({"telegram_id": tid, "size": dir_size})
    return result
