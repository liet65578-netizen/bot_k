"""
Main menu — navigation, keyboards, cancel, access control.
All text via i18n.
"""
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from config import ADMIN_IDS
from database import is_registered, set_user_lang, get_user_status
from i18n import t, get_lang, set_lang_cached, detect_lang_from_telegram, LANGUAGES, DEFAULT_LANG, is_menu_button, identify_menu_key

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_main_keyboard(user_id: int, lang: str = DEFAULT_LANG):
    status = get_user_status(user_id)
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
    if status == "active":
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton(t("menu_team", lang)), KeyboardButton(t("menu_content", lang))],
                [KeyboardButton(t("menu_schedule", lang)), KeyboardButton(t("menu_knowledge", lang))],
                [KeyboardButton(t("menu_profile", lang)), KeyboardButton(t("menu_lang", lang))],
            ],
            resize_keyboard=True,
            input_field_placeholder=t("menu_placeholder", lang),
        )
    # Unregistered, pending, or inactive — minimal keyboard
    buttons = []
    if not status:
        # Not registered yet
        buttons.append([KeyboardButton(t("menu_team", lang))])
    buttons.append([KeyboardButton(t("menu_lang", lang))])
    return ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True,
        input_field_placeholder=t("menu_placeholder", lang),
    )


def language_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"set_lang_{code}")]
        for code, name in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(buttons)


async def ensure_active_or_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Return True only for admins and active users. Block everyone else with an appropriate message."""
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    status = get_user_status(user_id)
    if status == "active":
        return True

    lang = await get_lang(update, context)
    target = update.callback_query.message if update.callback_query else update.message
    if not target:
        return False

    if status == "inactive":
        msg_key = "access_deactivated"
    elif status == "pending":
        msg_key = "access_pending"
    else:
        msg_key = "access_denied"

    await target.reply_text(
        t(msg_key, lang),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(user_id, lang),
    )
    return False


# Legacy alias — some handlers import this name
ensure_registered_or_reject = ensure_active_or_reject


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    from database import get_user_lang
    db_lang = get_user_lang(user_id)
    if db_lang is None:
        lang = detect_lang_from_telegram(user.language_code)
        set_user_lang(user_id, lang)
        set_lang_cached(context, lang)
    else:
        lang = await get_lang(update, context)
    keyboard = get_main_keyboard(user_id, lang)

    status = get_user_status(user_id)
    if status == "pending":
        await update.message.reply_text(
            t("access_pending", lang), parse_mode="Markdown", reply_markup=keyboard)
        return
    if status == "inactive":
        await update.message.reply_text(
            t("access_deactivated", lang), parse_mode="Markdown", reply_markup=keyboard)
        return

    await update.message.reply_text(
        t("welcome", lang),
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await get_lang(update, context)
    user_id = update.effective_user.id

    if not await ensure_active_or_reject(update, context):
        return

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
    user_id = update.effective_user.id

    if query:
        await query.answer()
        data = query.data
        if data == "main_menu":
            if not await ensure_active_or_reject(update, context):
                return
            keyboard = get_main_keyboard(user_id, lang)
            await query.message.reply_text(
                t("main_menu", lang),
                reply_markup=keyboard,
            )
        return

    if not text:
        return

    menu_key = identify_menu_key(text)

    # Language switch is always allowed
    if menu_key == "menu_lang":
        await update.message.reply_text(
            t("lang_choose", lang),
            parse_mode="Markdown",
            reply_markup=language_keyboard(),
        )
        return

    # Admin panel — only for admins, checked inside admin_cmd
    if menu_key == "menu_admin":
        from handlers.admin import admin_cmd
        await admin_cmd(update, context)
        return

    # "Хочу в команду" — allow for unregistered only; block for inactive
    if menu_key == "menu_team":
        status = get_user_status(user_id)
        if status == "inactive":
            await update.message.reply_text(
                t("access_deactivated", lang),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(user_id, lang),
            )
            return
        # For unregistered/pending — let registration ConversationHandler handle it
        # (it's registered above this handler in priority, so this is a fallback)
        return

    # Everything else requires active status
    if not await ensure_active_or_reject(update, context):
        return

    if menu_key == "menu_schedule":
        from handlers.schedule import show_schedule
        await show_schedule(update, context)
    elif menu_key == "menu_knowledge":
        from handlers.knowledge import show_knowledge_menu
        await show_knowledge_menu(update, context)
    elif menu_key == "menu_profile":
        if is_admin(user_id):
            await update.message.reply_text(
                t("admin_profile_text", lang),
                parse_mode="Markdown",
                reply_markup=get_main_keyboard(user_id, lang),
            )
        else:
            from handlers.profile import show_profile
            await show_profile(update, context)
    elif menu_key == "menu_content":
        # Handled by content ConversationHandler entry_point
        pass
    else:
        keyboard = get_main_keyboard(user_id, lang)
        await update.message.reply_text(
            t("use_buttons", lang),
            reply_markup=keyboard,
        )
