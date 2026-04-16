"""
Registration handler — multi-step form with i18n.
Steps: Name -> Class -> Specialization (multi + custom "Other") -> Software -> Confirm
"""
import json
import logging
from html import escape
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import CLASSES, SPECS, ADMIN_GROUP_ID, ADMIN_IDS
from database import upsert_user, is_registered, get_user
from handlers.main_menu import get_main_keyboard, cancel
from i18n import t, get_lang, menu_button_re, is_menu_button

logger = logging.getLogger(__name__)

# --- Conversation states ---
(
    REG_NAME,
    REG_CLASS,
    REG_SPEC,
    REG_SPEC_CUSTOM,
    REG_SOFTWARE,
    REG_CONFIRM,
) = range(6)

REGISTRATION_STATES = {
    "REG_NAME": REG_NAME,
    "REG_CLASS": REG_CLASS,
    "REG_SPEC": REG_SPEC,
    "REG_SPEC_CUSTOM": REG_SPEC_CUSTOM,
    "REG_SOFTWARE": REG_SOFTWARE,
    "REG_CONFIRM": REG_CONFIRM,
}


# --- Keyboards ---

def _class_keyboard() -> InlineKeyboardMarkup:
    rows, row = [], []
    for cls in CLASSES:
        row.append(InlineKeyboardButton(cls, callback_data=f"reg_class_{cls}"))
        if len(row) == 4:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _spec_keyboard(selected: list[str], lang: str = "ru") -> InlineKeyboardMarkup:
    rows = []
    for spec in SPECS:
        mark = "✅ " if spec in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{spec}", callback_data=f"reg_spec_{spec}")])
    # Custom specs that are not in SPECS
    for spec in selected:
        if spec not in SPECS:
            rows.append([InlineKeyboardButton(f"✅ {spec}", callback_data=f"reg_spec_{spec}")])
    # "Other" button always visible
    rows.append([InlineKeyboardButton(t("reg_spec_other_btn", lang), callback_data="reg_spec_other")])
    # "Done" button — only if at least one selected
    if selected:
        rows.append([InlineKeyboardButton(t("reg_spec_done_btn", lang), callback_data="reg_spec_done")])
    return InlineKeyboardMarkup(rows)


def _confirm_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("reg_confirm_yes", lang), callback_data="reg_confirm_yes"),
            InlineKeyboardButton(t("reg_confirm_no", lang), callback_data="reg_confirm_no"),
        ]
    ])


# --- Entry point ---

async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    lang = await get_lang(update, context)

    if is_registered(user_id):
        row = get_user(user_id)
        specs = json.loads(row["specs"])
        await update.message.reply_text(
            t("reg_already", lang,
              full_name=row["full_name"],
              class_name=row["class_name"],
              specs=", ".join(specs)),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("reg_update_btn", lang), callback_data="reg_restart")]
            ]),
        )
        return ConversationHandler.END

    context.user_data["reg"] = {"specs": []}
    await update.message.reply_text(
        t("reg_welcome", lang),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return REG_NAME


async def reg_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)
    context.user_data["reg"] = {"specs": []}
    await query.message.reply_text(
        t("reg_step1", lang),
        parse_mode="Markdown",
    )
    return REG_NAME


# --- Step 1: Name ---

async def reg_got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    lang = await get_lang(update, context)

    # If user clicked a menu button instead of typing name, exit conversation
    if is_menu_button(text):
        return await _exit_to_menu(update, context, lang)

    if len(text.split()) < 2:
        await update.message.reply_text(t("reg_name_short", lang))
        return REG_NAME

    context.user_data["reg"]["full_name"] = text
    await update.message.reply_text(
        t("reg_name_ok", lang, name=text),
        parse_mode="Markdown",
        reply_markup=_class_keyboard(),
    )
    return REG_CLASS


# --- Step 2: Class ---

async def reg_got_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)
    chosen = query.data.replace("reg_class_", "")
    context.user_data["reg"]["class_name"] = chosen
    context.user_data["reg"]["specs"] = []

    await query.message.edit_text(
        t("reg_class_ok", lang, cls=chosen),
        parse_mode="Markdown",
        reply_markup=_spec_keyboard([], lang),
    )
    return REG_SPEC


# --- Step 3: Specialization (multi-select + custom "Other") ---

async def reg_toggle_spec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = await get_lang(update, context)

    if data == "reg_spec_done":
        specs = context.user_data["reg"].get("specs", [])
        if not specs:
            await query.answer(t("reg_spec_empty", lang), show_alert=True)
            return REG_SPEC
        await query.message.edit_text(
            t("reg_spec_ok", lang, specs=", ".join(specs)),
            parse_mode="Markdown",
        )
        return REG_SOFTWARE

    if data == "reg_spec_other":
        # Enter custom specialization mode
        await query.message.edit_text(
            t("reg_spec_other_prompt", lang),
            parse_mode="Markdown",
        )
        return REG_SPEC_CUSTOM

    spec = data.replace("reg_spec_", "")
    specs = context.user_data["reg"]["specs"]
    if spec in specs:
        specs.remove(spec)
    else:
        specs.append(spec)

    await query.message.edit_reply_markup(reply_markup=_spec_keyboard(specs, lang))
    return REG_SPEC


# --- Step 3b: Custom specialization text input ---

async def reg_custom_spec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    lang = await get_lang(update, context)

    # If user clicked a menu button, exit conversation
    if is_menu_button(text):
        return await _exit_to_menu(update, context, lang)

    if not text or len(text) < 2:
        await update.message.reply_text(t("reg_spec_other_prompt", lang))
        return REG_SPEC_CUSTOM

    specs = context.user_data["reg"]["specs"]
    if text not in specs:
        specs.append(text)

    await update.message.reply_text(
        t("reg_spec_other_added", lang, spec=text),
        parse_mode="Markdown",
        reply_markup=_spec_keyboard(specs, lang),
    )
    return REG_SPEC


# --- Step 4: Software ---

async def reg_got_software(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    lang = await get_lang(update, context)

    if is_menu_button(text):
        return await _exit_to_menu(update, context, lang)

    context.user_data["reg"]["software"] = text
    reg = context.user_data["reg"]

    await update.message.reply_text(
        t("reg_confirm_summary", lang,
          full_name=reg["full_name"],
          class_name=reg["class_name"],
          specs=", ".join(reg["specs"]),
          software=text),
        parse_mode="Markdown",
        reply_markup=_confirm_keyboard(lang),
    )
    return REG_CONFIRM


# --- Step 5: Confirm ---

async def reg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)

    if query.data == "reg_confirm_no":
        context.user_data["reg"] = {"specs": []}
        await query.message.reply_text(
            t("reg_restart_text", lang),
            parse_mode="Markdown",
        )
        return REG_NAME

    # Save to DB
    user = update.effective_user
    reg = context.user_data["reg"]
    upsert_user(
        telegram_id=user.id,
        username=user.username,
        full_name=reg["full_name"],
        class_name=reg["class_name"],
        specs=reg["specs"],
        software=reg["software"],
    )

    # Notify admin group (always in admin's language — Russian for group)
    admin_msg = t("notify_new_member", "ru",
                  full_name=escape(reg["full_name"]),
                  class_name=escape(reg["class_name"]),
                  specs=escape(", ".join(reg["specs"])),
                  software=escape(reg["software"]),
                  username=escape(user.username or "no username"),
                  uid=user.id)
    try:
        await query.get_bot().send_message(
            chat_id=ADMIN_GROUP_ID, text=admin_msg, parse_mode="HTML",
        )
    except Exception as e:
        logger.warning("Failed to notify admin group: %s", e)

    for admin_id in ADMIN_IDS:
        try:
            await query.get_bot().send_message(
                chat_id=admin_id, text=admin_msg, parse_mode="HTML",
            )
        except Exception as e:
            logger.warning("Failed to notify admin %s: %s", admin_id, e)

    first_name = reg["full_name"].split()[1] if len(reg["full_name"].split()) > 1 else reg["full_name"].split()[0]
    await query.message.edit_text(
        t("reg_success", lang, name=first_name),
        parse_mode="Markdown",
    )
    await query.message.reply_text(
        t("back_to_menu", lang),
        reply_markup=get_main_keyboard(user.id, lang),
    )
    context.user_data.pop("reg", None)
    return ConversationHandler.END


# --- Helper: exit conversation on menu button press ---

async def _exit_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> int:
    context.user_data.pop("reg", None)
    await update.message.reply_text(
        t("cancel", lang),
        reply_markup=get_main_keyboard(update.effective_user.id, lang),
    )
    return ConversationHandler.END


# --- Fallback: handle menu button during conversation ---

async def _menu_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    return await _exit_to_menu(update, context, lang)


# --- ConversationHandler ---

def _build_menu_filter():
    """Build a filter matching any menu button text in any language."""
    from i18n import all_menu_texts
    import re as _re
    texts = all_menu_texts()
    pattern = "^(" + "|".join(_re.escape(t_) for t_ in texts) + ")$"
    return filters.Regex(pattern)


_MENU_FILTER = None

def _get_menu_filter():
    global _MENU_FILTER
    if _MENU_FILTER is None:
        _MENU_FILTER = _build_menu_filter()
    return _MENU_FILTER


registration_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(menu_button_re("menu_team")), reg_start),
        CallbackQueryHandler(reg_restart, pattern="^reg_restart$"),
    ],
    states={
        REG_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, reg_got_name),
        ],
        REG_CLASS: [
            CallbackQueryHandler(reg_got_class, pattern="^reg_class_"),
        ],
        REG_SPEC: [
            CallbackQueryHandler(reg_toggle_spec, pattern="^reg_spec_"),
        ],
        REG_SPEC_CUSTOM: [
            CallbackQueryHandler(reg_toggle_spec, pattern="^reg_spec_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, reg_custom_spec),
        ],
        REG_SOFTWARE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, reg_got_software),
        ],
        REG_CONFIRM: [
            CallbackQueryHandler(reg_confirm, pattern="^reg_confirm_"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CommandHandler("start", cancel),
        CommandHandler("menu", cancel),
    ],
    allow_reentry=True,
)
