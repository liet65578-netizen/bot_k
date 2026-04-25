"""
conftest.py — shared fixtures for the Klasyk bot test suite.
"""
import os
import sys
import sqlite3
import pytest

# Make sure the bot package root is importable
BOT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BOT_ROOT not in sys.path:
    sys.path.insert(0, BOT_ROOT)


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    """Create temporary data directory and patch database paths."""
    data_dir = tmp_path / "data"
    import database
    monkeypatch.setattr(database, "DATA_DIR", data_dir)
    monkeypatch.setattr(database, "GLOBAL_DB", data_dir / "global.db")
    monkeypatch.setattr(database, "USERS_DIR", data_dir / "users")
    database.init_db()
    return data_dir
