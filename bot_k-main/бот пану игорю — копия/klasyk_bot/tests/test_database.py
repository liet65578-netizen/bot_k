"""
Tests for the database module.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestInitDb:
    def test_init_creates_tables(self, tmp_db):
        import database
        conn = database.get_conn()
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
        for table in ["users", "user_settings", "content_submissions",
                      "schedule_events", "signups", "knowledge_items"]:
            assert table in tables, f"Missing table: {table}"
        conn.close()


class TestUserCrud:
    def test_upsert_and_get(self, tmp_db):
        import database
        database.upsert_user(
            telegram_id=123, username="testuser",
            full_name="Ivan Ivanov", class_name="1A",
            specs='["🎥 Съёмка"]', software="Premiere",
        )
        user = database.get_user(123)
        assert user is not None
        assert user["full_name"] == "Ivan Ivanov"
        assert user["class_name"] == "1A"
        assert user["status"] == "pending"

    def test_is_registered(self, tmp_db):
        import database
        assert not database.is_registered(999)
        database.upsert_user(999, "u", "Name", "2B", '["X"]', "SW")
        assert database.is_registered(999)

    def test_set_status(self, tmp_db):
        import database
        database.upsert_user(100, "u", "Name", "1C", '[]', "")
        database.set_user_status(100, "active")
        user = database.get_user(100)
        assert user["status"] == "active"

    def test_delete_user(self, tmp_db):
        import database
        database.upsert_user(200, "u", "Del", "1A", '[]', "")
        assert database.is_registered(200)
        database.delete_user(200)
        assert not database.is_registered(200)

    def test_get_all_users(self, tmp_db):
        import database
        database.upsert_user(1, "a", "A", "1A", '[]', "")
        database.upsert_user(2, "b", "B", "1B", '[]', "")
        users = database.get_all_users()
        assert len(users) >= 2

    def test_get_users_count(self, tmp_db):
        import database
        database.upsert_user(1, "a", "A", "1A", '[]', "")
        database.upsert_user(2, "b", "B", "1B", '[]', "")
        database.set_user_status(2, "active")
        counts = database.get_users_count()
        assert counts["total"] == 2
        assert counts["active"] == 1
        assert counts["pending"] == 1


class TestUserLang:
    def test_get_lang_none_for_new_user(self, tmp_db):
        import database
        assert database.get_user_lang(777) is None

    def test_set_and_get_lang(self, tmp_db):
        import database
        database.set_user_lang(555, "pl")
        assert database.get_user_lang(555) == "pl"

    def test_upsert_lang(self, tmp_db):
        import database
        database.set_user_lang(555, "en")
        database.set_user_lang(555, "uk")
        assert database.get_user_lang(555) == "uk"


class TestSubmissions:
    def test_save_and_get_submission(self, tmp_db):
        import database
        sub_id = database.save_submission(
            telegram_id=1, submitter_name="Ivan",
            content_type="📰 Новость", description="Test desc",
            location="Актовый зал", file_id=None, file_type=None,
        )
        assert sub_id > 0
        sub = database.get_submission(sub_id)
        assert sub["description"] == "Test desc"

    def test_submission_counts(self, tmp_db):
        import database
        database.save_submission(1, "A", "T", "D", "L", None, None)
        database.save_submission(2, "B", "T", "D", "L", None, None)
        counts = database.get_submissions_count()
        assert counts["total"] >= 2
        assert counts["new"] >= 2


class TestSchedule:
    def test_add_and_get_event(self, tmp_db):
        import database
        ev_id = database.add_event("Test", "01.01.2026", "14:00", "Room", "Desc", 1)
        assert ev_id > 0
        ev = database.get_event(ev_id)
        assert ev["title"] == "Test"

    def test_signup_for_event(self, tmp_db):
        import database
        ev_id = database.add_event("Ev", "01.01.2026", "10:00", "Gym", "Desc", 1)
        assert database.signup_for_event(1, ev_id) is True
        assert database.signup_for_event(1, ev_id) is False  # duplicate

    def test_get_user_signups(self, tmp_db):
        import database
        ev_id = database.add_event("Ev", "01.01.2026", "10:00", "Gym", "D", 1)
        database.signup_for_event(42, ev_id)
        signups = database.get_user_signups(42)
        assert len(signups) >= 1

    def test_delete_event(self, tmp_db):
        import database
        ev_id = database.add_event("Del", "01.01.2026", "10:00", "Room", "D", 1)
        database.delete_event(ev_id)
        assert database.get_event(ev_id) is None


class TestKnowledge:
    def test_knowledge_items_seeded(self, tmp_db):
        import database
        items = database.get_knowledge_items()
        assert len(items) > 0

    def test_update_knowledge(self, tmp_db):
        import database
        items = database.get_knowledge_items()
        if items:
            item_id = items[0]["id"]
            database.update_knowledge_item(item_id, "Updated text")
            updated = database.get_knowledge_item(item_id)
            assert updated["text"] == "Updated text"
