"""
Knowledge base handler with i18n.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_IDS
from database import get_knowledge_items, get_knowledge_item, update_knowledge_item
from handlers.main_menu import ensure_registered_or_reject
from i18n import t, get_lang, is_menu_button, LANGUAGES

logger = logging.getLogger(__name__)


def _knowledge_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        # Namespace callback_data to avoid collisions with other handlers (e.g. adm_*)
        [InlineKeyboardButton(f"{item['icon']} {item['title']}", callback_data=f"kb:{item['id']}")]
        for item in get_knowledge_items(lang)
    ]
    return InlineKeyboardMarkup(buttons)


async def show_knowledge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_registered_or_reject(update, context):
        return
    lang = await get_lang(update, context)
    await update.message.reply_text(
        t("kb_title", lang),
        parse_mode="Markdown",
        reply_markup=_knowledge_menu_keyboard(lang),
    )


async def knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_registered_or_reject(update, context):
        return
    query = update.callback_query
    data = query.data
    lang = await get_lang(update, context)

    if data == "kb_back":
        await query.answer()
        await query.message.edit_text(
            t("kb_title", lang),
            parse_mode="Markdown",
            reply_markup=_knowledge_menu_keyboard(lang),
        )
        return

    # New format: kb:<item_id>
    # Legacy format: <item_id> (historically ids were like "kb_terms")
    item_id = data[3:] if data.startswith("kb:") else data
    item = get_knowledge_item(item_id, lang)
    if not item:
        await query.answer(t("kb_not_found", lang), show_alert=True)
        return

    await query.answer()
    await query.message.edit_text(
        item["text"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t("kb_back", lang), callback_data="kb_back")]
        ]),
        disable_web_page_preview=True,
    )


async def admin_edit_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update, context)
    if update.effective_user.id not in ADMIN_IDS:
        await update.callback_query.answer(t("adm_no_access_short", lang), show_alert=True)
        return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    # Step 1: choose language to edit
    buttons = [
        [InlineKeyboardButton(name, callback_data=f"adm_kb_lang_{code}")]
        for code, name in LANGUAGES.items()
    ]
    try:
        await query.message.edit_text(
            t("adm_kb_edit_lang_title", lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return "WAIT_KNOWLEDGE_SELECT"
        raise
    return "WAIT_KNOWLEDGE_LANG"


async def admin_choose_kb_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update, context)
    if update.effective_user.id not in ADMIN_IDS:
        await update.callback_query.answer(t("adm_no_access_short", lang), show_alert=True)
        return ConversationHandler.END
    query = update.callback_query
    await query.answer()
    target_lang = query.data.replace("adm_kb_lang_", "")
    context.user_data["edit_knowledge_lang"] = target_lang
    items = get_knowledge_items(target_lang)
    buttons = [
        [InlineKeyboardButton(f"{item['icon']} {item['title']}", callback_data=f"adm_edit_{item['id']}")]
        for item in items
    ]
    buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_back")])
    try:
        await query.message.edit_text(
            t("adm_kb_edit_title", lang),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return "WAIT_KNOWLEDGE_SELECT"
        raise
    return "WAIT_KNOWLEDGE_SELECT"


async def admin_edit_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = await get_lang(update, context)
    if update.effective_user.id not in ADMIN_IDS:
        await update.callback_query.answer(t("adm_no_access_short", lang), show_alert=True)
        return ConversationHandler.END
    query = update.callback_query
    item_id = query.data.replace("adm_edit_", "")
    target_lang = context.user_data.get("edit_knowledge_lang") or lang
    item = get_knowledge_item(item_id, target_lang)
    if not item:
        await query.answer(t("adm_kb_not_found", lang), show_alert=True)
        return
    await query.answer()
    context.user_data["edit_knowledge_id"] = item_id
    context.user_data["edit_knowledge_chat_id"] = query.message.chat_id
    context.user_data["edit_knowledge_menu_message_id"] = query.message.message_id
    try:
        await query.message.edit_text(
            t("adm_kb_edit_item", lang, title=item["title"], text=item["text"]),
            parse_mode="Markdown",
        )
    except BadRequest as e:
        if "Message is not modified" in str(e):
            return "WAIT_KNOWLEDGE_TEXT"
        raise
    return "WAIT_KNOWLEDGE_TEXT"


async def admin_save_knowledge(update, context):
    lang = await get_lang(update, context)
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(t("adm_no_access_short", lang))
        return ConversationHandler.END
    item_id = context.user_data.get("edit_knowledge_id")
    target_lang = context.user_data.get("edit_knowledge_lang") or lang
    new_text = update.message.text
    # Prevent accidental overwrites when admin presses a menu button while editing.
    if new_text and is_menu_button(new_text):
        await update.message.reply_text(t("cancel", lang))
        context.user_data.pop("edit_knowledge_id", None)
        context.user_data.pop("edit_knowledge_chat_id", None)
        context.user_data.pop("edit_knowledge_menu_message_id", None)
        return ConversationHandler.END
    item = get_knowledge_item(item_id, target_lang) if item_id else None
    if item and update_knowledge_item(item_id, target_lang, new_text):
        logger.info("Knowledge item %s updated by user %s", item_id, update.effective_user.id)
        buttons = [
            [InlineKeyboardButton(f"{i['icon']} {i['title']}", callback_data=f"adm_edit_{i['id']}")]
            for i in get_knowledge_items(target_lang)
        ]
        chat_id = context.user_data.get("edit_knowledge_chat_id", update.effective_chat.id)
        menu_msg_id = context.user_data.get("edit_knowledge_menu_message_id")
        try:
            await update.message.reply_text(t("adm_kb_saved", lang), parse_mode="Markdown")
            if menu_msg_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id, message_id=menu_msg_id,
                    text=t("adm_kb_edit_title", lang),
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            else:
                await update.message.reply_text(
                    t("adm_kb_edit_title", lang),
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        except Exception:
            await update.message.reply_text(
                t("adm_kb_edit_title", lang),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        await update.message.reply_text(t("adm_kb_not_found", lang), parse_mode="Markdown")
    context.user_data.pop("edit_knowledge_id", None)
    context.user_data.pop("edit_knowledge_lang", None)
    context.user_data.pop("edit_knowledge_chat_id", None)
    context.user_data.pop("edit_knowledge_menu_message_id", None)
    return ConversationHandler.END
