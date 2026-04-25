"""
i18n — Internationalization module for Klasyk Media Hub Bot.
Loads translations from locales/*.json files.
Supports: Polish (pl), English (en), Russian (ru), Ukrainian (uk).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

# ── Language registry (order matters for the selection keyboard) ──────────────
LANGUAGES = {
    "pl": "🇵🇱 Polski",
    "en": "🇬🇧 English",
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
}

DEFAULT_LANG = "en"

# ── Mapping from Telegram language_code → our lang code ──────────────────────
_TG_LANG_MAP: dict[str, str] = {
    "pl": "pl",
    "en": "en",
    "ru": "ru",
    "uk": "uk",
    "be": "ru",      # Belarusian → Russian fallback
    "uk-UA": "uk",
    "ru-RU": "ru",
    "en-US": "en",
    "en-GB": "en",
    "pl-PL": "pl",
}

# ── Load translations from JSON ──────────────────────────────────────────────
_LOCALES_DIR = Path(__file__).parent / "locales"

_TEXTS: dict[str, dict[str, str]] = {}

for _code in LANGUAGES:
    _path = _LOCALES_DIR / f"{_code}.json"
    if _path.exists():
        with open(_path, "r", encoding="utf-8") as _f:
            _TEXTS[_code] = json.load(_f)
    else:
        _TEXTS[_code] = {}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Get translated text. Falls back to English, then returns [key]."""
    text = (
        _TEXTS.get(lang, {}).get(key)
        or _TEXTS.get(DEFAULT_LANG, {}).get(key)
        or f"[{key}]"
    )
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


# Markdown v1 special characters
_MD_ESCAPE_RE = re.compile(r'([_*`\[\]])')


def esc_md(text) -> str:
    """Escape Markdown v1 special chars in user-provided data."""
    return _MD_ESCAPE_RE.sub(r'\\\1', str(text))


def get_all_values(key: str) -> list[str]:
    """Get all language variants for a translation key."""
    values: list[str] = []
    for lang_data in _TEXTS.values():
        v = lang_data.get(key)
        if v and v not in values:
            values.append(v)
    return values


def menu_button_re(key: str) -> str:
    """Build a regex pattern that matches all language variants of a menu button."""
    variants = get_all_values(key)
    return "^(" + "|".join(re.escape(v) for v in variants) + ")$"


def all_menu_texts() -> set[str]:
    """Return a set of ALL menu button texts in ALL languages."""
    keys = [
        "menu_team", "menu_content", "menu_schedule", "menu_knowledge",
        "menu_profile", "menu_admin", "menu_lang",
    ]
    result: set[str] = set()
    for k in keys:
        result.update(get_all_values(k))
    return result


def is_menu_button(text: str) -> bool:
    """Check if text matches any known menu button in any language."""
    return text in all_menu_texts()


def identify_menu_key(text: str) -> str | None:
    """Identify which menu key a button text corresponds to."""
    keys = [
        "menu_team", "menu_content", "menu_schedule", "menu_knowledge",
        "menu_profile", "menu_admin", "menu_lang",
    ]
    for k in keys:
        if text in get_all_values(k):
            return k
    return None


def detect_lang_from_telegram(language_code: str | None) -> str:
    """Map Telegram user.language_code to one of our supported languages.

    Returns DEFAULT_LANG if the code is unknown or None.
    """
    if not language_code:
        return DEFAULT_LANG
    # Exact match first
    code = language_code.strip()
    if code in _TG_LANG_MAP:
        return _TG_LANG_MAP[code]
    # Try base (e.g. "en-US" → "en")
    base = code.split("-")[0].lower()
    if base in _TG_LANG_MAP:
        return _TG_LANG_MAP[base]
    if base in LANGUAGES:
        return base
    return DEFAULT_LANG


async def get_lang(update, context) -> str:
    """Get user's language from context cache → DB → Telegram API → default."""
    # 1. Context cache (fastest)
    if context and context.user_data and "lang" in context.user_data:
        return context.user_data["lang"]

    user = update.effective_user if update else None
    user_id = user.id if user else None

    # 2. Database
    if user_id:
        from database import get_user_lang
        db_lang = get_user_lang(user_id)
        if db_lang:
            if context and context.user_data is not None:
                context.user_data["lang"] = db_lang
            return db_lang

    # 3. Telegram language_code auto-detection
    if user and user.language_code:
        detected = detect_lang_from_telegram(user.language_code)
        if context and context.user_data is not None:
            context.user_data["lang"] = detected
        return detected

    # 4. Default
    if context and context.user_data is not None:
        context.user_data["lang"] = DEFAULT_LANG
    return DEFAULT_LANG


def set_lang_cached(context, lang: str) -> None:
    """Cache language in context.user_data."""
    if context and context.user_data is not None:
        context.user_data["lang"] = lang
