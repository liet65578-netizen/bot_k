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
    """Create a temporary database and patch database.DB_PATH."""
    db_file = tmp_path / "test_klasyk.db"
    import database
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    return db_file
