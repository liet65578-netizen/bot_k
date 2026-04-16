"""
Content submission handler — file/text upload workflow with i18n.
Steps: Type -> File/Text -> Description -> Location -> Done
"""
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import CONTENT_TYPES, LOCATIONS, ADMIN_GROUP_ID, ADMIN_IDS
from database import save_submission, get_user
from handlers.main_menu import get_main_keyboard, cancel, ensure_registered_or_reject
from i18n import t, get_lang, menu_button_re, is_menu_button

logger = logging.getLogger(__name__)

(CON_TYPE, CON_FILE, CON_DESCRIPTION, CON_LOCATION) = range(10, 14)

CONTENT_STATES = {
    "CON_TYPE": CON_TYPE,
    "CON_FILE": CON_FILE,
    "CON_DESCRIPTION": CON_DESCRIPTION,
    "CON_LOCATION": CON_LOCATION,
}


def _type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(ct, callback_data=f"con_type_{ct}")] for ct in CONTENT_TYPES
    ])


def _location_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(loc, callback_data=f"con_loc_{loc}")] for loc in LOCATIONS
    ])


async def content_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await ensure_registered_or_reject(update, context):
        return ConversationHandler.END
    lang = await get_lang(update, context)
    context.user_data["con"] = {}
    await update.message.reply_text(
        t("con_start", lang),
        parse_mode="Markdown",
        reply_markup=_type_keyboard(),
    )
    return CON_TYPE


async def con_got_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)
    ctype = query.data.replace("con_type_", "")
    context.user_data["con"]["type"] = ctype

    if ctype == CONTENT_TYPES[2]:  # text
        await query.message.edit_text(
            t("con_type_text", lang, ctype=ctype), parse_mode="Markdown",
        )
    else:
        await query.message.edit_text(
            t("con_type_file", lang, ctype=ctype), parse_mode="Markdown",
        )
    return CON_FILE


async def con_got_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    con = context.user_data["con"]
    lang = await get_lang(update, context)

    if update.message.document:
        con["file_id"] = update.message.document.file_id
        con["file_type"] = "document"
        label = t("con_file_doc", lang)
    elif update.message.photo:
        con["file_id"] = update.message.photo[-1].file_id
        con["file_type"] = "photo"
        label = t("con_file_photo", lang)
    elif update.message.video:
        con["file_id"] = update.message.video.file_id
        con["file_type"] = "video"
        label = t("con_file_video", lang)
    elif update.message.text:
        if is_menu_button(update.message.text):
            return await _exit(update, context, lang)
        con["file_id"] = None
        con["file_type"] = "text"
        con["text_content"] = update.message.text
        label = t("con_file_text", lang)
    else:
        await update.message.reply_text(t("con_file_invalid", lang))
        return CON_FILE

    await update.message.reply_text(
        t("con_step3", lang, label=label), parse_mode="Markdown",
    )
    return CON_DESCRIPTION


async def con_got_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    desc = update.message.text.strip()
    lang = await get_lang(update, context)
    if is_menu_button(desc):
        return await _exit(update, context, lang)
    if len(desc) < 5:
        await update.message.reply_text(t("con_desc_short", lang))
        return CON_DESCRIPTION
    context.user_data["con"]["description"] = desc
    await update.message.reply_text(
        t("con_step4", lang), parse_mode="Markdown",
        reply_markup=_location_keyboard(),
    )
    return CON_LOCATION


async def con_got_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)
    location = query.data.replace("con_loc_", "")
    con = context.user_data["con"]
    con["location"] = location

    user = update.effective_user
    db_user = get_user(user.id)
    submitter_name = db_user["full_name"] if db_user else (user.full_name or str(user.id))

    sub_id = save_submission(
        telegram_id=user.id,
        submitter_name=submitter_name,
        content_type=con["type"],
        description=con["description"],
        location=location,
        file_id=con.get("file_id"),
        file_type=con.get("file_type", "unknown"),
    )

    # Notify admins
    admin_text = t("notify_new_submission", "ru",
                   sub_id=sub_id, submitter=submitter_name,
                   username=user.username or "—",
                   ctype=con["type"], location=location,
                   description=con["description"])
    bot = query.get_bot()
    try:
        if con.get("file_type") == "photo" and con.get("file_id"):
            await bot.send_photo(chat_id=ADMIN_GROUP_ID, photo=con["file_id"],
                                 caption=admin_text, parse_mode="Markdown")
        elif con.get("file_type") == "video" and con.get("file_id"):
            await bot.send_video(chat_id=ADMIN_GROUP_ID, video=con["file_id"],
                                 caption=admin_text, parse_mode="Markdown")
        elif con.get("file_type") == "document" and con.get("file_id"):
            await bot.send_document(chat_id=ADMIN_GROUP_ID, document=con["file_id"],
                                    caption=admin_text, parse_mode="Markdown")
        else:
            full_text = admin_text
            if con.get("text_content"):
                full_text += f"\n\n📄 Текст:\n{con['text_content']}"
            await bot.send_message(chat_id=ADMIN_GROUP_ID, text=full_text, parse_mode="Markdown")
    except Exception as e:
        logger.warning("Failed to send content to admin group: %s", e)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("Failed to notify admin %s: %s", admin_id, e)

    await query.message.edit_text(
        t("con_success", lang, sub_id=sub_id, ctype=con["type"], location=location),
        parse_mode="Markdown",
    )
    await query.message.reply_text(
        t("con_back_menu", lang),
        reply_markup=get_main_keyboard(user.id, lang),
    )
    context.user_data.pop("con", None)
    return ConversationHandler.END


async def _exit(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> int:
    context.user_data.pop("con", None)
    await update.message.reply_text(
        t("cancel", lang),
        reply_markup=get_main_keyboard(update.effective_user.id, lang),
    )
    return ConversationHandler.END


content_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(menu_button_re("menu_content")), content_start),
    ],
    states={
        CON_TYPE: [CallbackQueryHandler(con_got_type, pattern="^con_type_")],
        CON_FILE: [
            MessageHandler(
                (filters.PHOTO | filters.VIDEO | filters.Document.ALL | filters.TEXT)
                & ~filters.COMMAND,
                con_got_file,
            )
        ],
        CON_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, con_got_description)],
        CON_LOCATION: [CallbackQueryHandler(con_got_location, pattern="^con_loc_")],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CommandHandler("start", cancel),
        CommandHandler("menu", cancel),
    ],
    allow_reentry=True,
)
