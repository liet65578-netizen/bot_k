"""
Main menu — navigation, keyboards, cancel, access control.
All text via i18n.
"""
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
from database import is_registered, set_user_lang
from i18n import t, get_lang, set_lang_cached, LANGUAGES, is_menu_button, identify_menu_key

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_main_keyboard(user_id: int, lang: str = "ru"):
    if is_admin(user_id):
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton(t("menu_admin", lang))],
                [KeyboardButton(t("menu_schedule", lang)), KeyboardButton(t("menu_knowledge", lang))],
                [KeyboardButton(t("menu_profile", lang)), KeyboardButton(t("menu_lang", lang))],
            ],
            resize_keyboard=True,
            input_field_placeholder=t("menu_placeholder", lang),
        )
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("menu_team", lang)), KeyboardButton(t("menu_content", lang))],
            [KeyboardButton(t("menu_schedule", lang)), KeyboardButton(t("menu_knowledge", lang))],
            [KeyboardButton(t("menu_profile", lang)), KeyboardButton(t("menu_lang", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t("menu_placeholder", lang),
    )


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"set_lang_{code}")]
        for code, name in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(buttons)


async def ensure_registered_or_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_admin(user_id) or is_registered(user_id):
        return True
    lang = await get_lang(update, context)
    target = update.callback_query.message if update.callback_query else update.message
    if target:
        await target.reply_text(
            t("access_denied", lang),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user_id, lang),
        )
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await get_lang(update, context)
    user_id = update.effective_user.id
    from database import get_user_lang
    db_lang = get_user_lang(user_id)
    if db_lang is None:
        # First time user — show language selection
        await update.message.reply_text(
            t("lang_choose", lang),
            parse_mode="Markdown",
            reply_markup=language_keyboard(),
        )
        return
    keyboard = get_main_keyboard(user_id, lang)
    await update.message.reply_text(
        t("welcome", lang),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await get_lang(update, context)
    user_id = update.effective_user.id
    keyboard = get_main_keyboard(user_id, lang)
    await update.message.reply_text(
        t("main_menu", lang),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any active dialog."""
    context.user_data.clear()
    lang = await get_lang(update, context)
    await update.message.reply_text(
        t("cancel", lang),
        reply_markup=get_main_keyboard(update.effective_user.id, lang),
    )
    return ConversationHandler.END


async def handle_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection from inline keyboard."""
    query = update.callback_query
    await query.answer()
    code = query.data.replace("set_lang_", "")
    if code not in LANGUAGES:
        return
    user_id = update.effective_user.id
    set_user_lang(user_id, code)
    set_lang_cached(context, code)
    await query.message.edit_text(
        t("lang_changed", code, lang_name=LANGUAGES[code]),
        parse_mode="Markdown",
    )
    keyboard = get_main_keyboard(user_id, code)
    await query.message.reply_text(
        t("welcome", code),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text if update.message else None
    query = update.callback_query
    lang = await get_lang(update, context)

    if query:
        await query.answer()
        data = query.data
        if data == "main_menu":
            user_id = update.effective_user.id
            keyboard = get_main_keyboard(user_id, lang)
            await query.message.reply_text(
                t("main_menu", lang),
                reply_markup=keyboard,
            )
        return

    if not text:
        return

    menu_key = identify_menu_key(text)
    if menu_key == "menu_schedule":
        if not await ensure_registered_or_reject(update, context):
            return
        from handlers.schedule import show_schedule
        await show_schedule(update, context)
    elif menu_key == "menu_knowledge":
        if not await ensure_registered_or_reject(update, context):
            return
        from handlers.knowledge import show_knowledge_menu
        await show_knowledge_menu(update, context)
    elif menu_key == "menu_profile":
        user_id = update.effective_user.id
        if is_admin(user_id):
            await update.message.reply_text(
                t("admin_profile_text", lang),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(user_id, lang),
            )
        else:
            if not await ensure_registered_or_reject(update, context):
                return
            from handlers.profile import show_profile
            await show_profile(update, context)
    elif menu_key == "menu_admin":
        from handlers.admin import admin_cmd
        await admin_cmd(update, context)
    elif menu_key == "menu_lang":
        await update.message.reply_text(
            t("lang_choose", lang),
            parse_mode="Markdown",
            reply_markup=language_keyboard(),
        )
    elif menu_key == "menu_team":
        # Handled by registration ConversationHandler entry_point
        pass
    elif menu_key == "menu_content":
        if not await ensure_registered_or_reject(update, context):
            return
        # Handled by content ConversationHandler entry_point
        pass
    else:
        user_id = update.effective_user.id
        keyboard = get_main_keyboard(user_id, lang)
        await update.message.reply_text(
            t("use_buttons", lang),
            reply_markup=keyboard,
        )
