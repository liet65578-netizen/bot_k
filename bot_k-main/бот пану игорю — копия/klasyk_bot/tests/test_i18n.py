"""
Tests for the i18n module.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from i18n import (
    t, get_all_values, menu_button_re, all_menu_texts,
    is_menu_button, identify_menu_key, LANGUAGES, DEFAULT_LANG, _TEXTS,
)


class TestTranslation:
    def test_t_returns_string(self):
        assert isinstance(t("welcome", "ru"), str)
        assert isinstance(t("welcome", "pl"), str)
        assert isinstance(t("welcome", "en"), str)
        assert isinstance(t("welcome", "uk"), str)

    def test_t_fallback_to_ru(self):
        """Unknown lang → falls back to Russian."""
        result = t("welcome", "xx")
        assert result == t("welcome", "ru")

    def test_t_missing_key(self):
        """Unknown key → returns [key]."""
        assert t("nonexistent_key", "ru") == "[nonexistent_key]"

    def test_t_format_kwargs(self):
        result = t("lang_changed", "en", lang_name="English")
        assert "English" in result

    def test_t_format_safe_on_error(self):
        """If kwargs don't match placeholders, still returns something."""
        result = t("welcome", "ru", bogus="value")
        assert isinstance(result, str)


class TestLanguageCompleteness:
    """All 4 languages should have the same keys (or at least the main ones)."""

    CRITICAL_KEYS = [
        "menu_team", "menu_content", "menu_schedule", "menu_knowledge",
        "menu_profile", "welcome", "main_menu", "cancel",
        "reg_welcome", "reg_step1", "reg_name_ok",
        "con_start", "sched_title", "kb_title", "profile_title",
    ]

    def test_all_languages_present(self):
        for code in LANGUAGES:
            assert code in _TEXTS, f"Language '{code}' missing from _TEXTS"

    def test_critical_keys_present_all_langs(self):
        for key in self.CRITICAL_KEYS:
            for lang in LANGUAGES:
                val = _TEXTS[lang].get(key)
                assert val, f"Key '{key}' missing in lang '{lang}'"


class TestMenuHelpers:
    def test_get_all_values_returns_list(self):
        vals = get_all_values("menu_team")
        assert len(vals) == len(LANGUAGES)  # 4 languages

    def test_menu_button_re(self):
        import re
        pattern = menu_button_re("menu_team")
        # Should match Russian
        assert re.match(pattern, t("menu_team", "ru"))
        # Should match English
        assert re.match(pattern, t("menu_team", "en"))
        # Should NOT match random text
        assert not re.match(pattern, "random text")

    def test_all_menu_texts_returns_set(self):
        texts = all_menu_texts()
        assert isinstance(texts, set)
        assert len(texts) >= 7 * 4  # 7 menu keys × 4 languages (some may overlap for ru/uk)

    def test_is_menu_button(self):
        assert is_menu_button(t("menu_team", "ru"))
        assert is_menu_button(t("menu_schedule", "pl"))
        assert not is_menu_button("hello")

    def test_identify_menu_key(self):
        assert identify_menu_key(t("menu_content", "en")) == "menu_content"
        assert identify_menu_key(t("menu_profile", "uk")) == "menu_profile"
        assert identify_menu_key("unknown") is None


class TestDefaultLang:
    def test_default_is_ru(self):
        assert DEFAULT_LANG == "ru"
