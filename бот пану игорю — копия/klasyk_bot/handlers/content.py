"""
Раздел «Предложить контент» — воронка приёма материалов
Шаги: Тип → Файл/Текст → Описание → Локация → Готово
"""

import logging
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

from config import CONTENT_TYPES, LOCATIONS, ADMIN_GROUP_ID
from database import save_submission, get_user
from handlers.main_menu import MAIN_KEYBOARD, MENU_CONTENT, cancel

logger = logging.getLogger(__name__)

# ─── Состояния ───────────────────────────────────────────────────────────────
(
    CON_TYPE,
    CON_FILE,
    CON_DESCRIPTION,
    CON_LOCATION,
) = range(10, 14)

CONTENT_STATES = {
    "CON_TYPE": CON_TYPE,
    "CON_FILE": CON_FILE,
    "CON_DESCRIPTION": CON_DESCRIPTION,
    "CON_LOCATION": CON_LOCATION,
}


def _type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t, callback_data=f"con_type_{t}")] for t in CONTENT_TYPES
    ])


def _location_keyboard() -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(loc, callback_data=f"con_loc_{loc}")] for loc in LOCATIONS]
    return InlineKeyboardMarkup(rows)


# ─── Точка входа ─────────────────────────────────────────────────────────────

async def content_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["con"] = {}
    await update.message.reply_text(
        "📥 *Предложить контент*\n\n"
        "Отлично! Давай загрузим материал.\n\n"
        "📌 *Шаг 1/4* — Выбери *тип контента*:",
        parse_mode="Markdown",
        reply_markup=_type_keyboard(),
    )
    return CON_TYPE


# ─── Шаг 1: Тип ──────────────────────────────────────────────────────────────

async def con_got_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ctype = query.data.replace("con_type_", "")
    context.user_data["con"]["type"] = ctype

    if ctype == "📝 Текст / Новость":
        await query.message.edit_text(
            f"✅ Тип: *{ctype}*\n\n"
            f"📌 *Шаг 2/4* — Напиши текст своей новости или идеи.\n"
            f"_Можно несколько абзацев — пиши как хочется!_",
            parse_mode="Markdown",
        )
    else:
        await query.message.edit_text(
            f"✅ Тип: *{ctype}*\n\n"
            f"📌 *Шаг 2/4* — Загрузи файл.\n\n"
            f"📎 *Отправь как документ* (скрепка) — без потери качества\n"
            f"или обычным сообщением — быстрее, но сжатое",
            parse_mode="Markdown",
        )
    return CON_FILE


# ─── Шаг 2: Файл или текст ───────────────────────────────────────────────────

async def con_got_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    con = context.user_data["con"]

    if update.message.document:
        con["file_id"] = update.message.document.file_id
        con["file_type"] = "document"
        label = "📎 Файл получен (документ, без потери качества)"
    elif update.message.photo:
        con["file_id"] = update.message.photo[-1].file_id
        con["file_type"] = "photo"
        label = "📷 Фото получено"
    elif update.message.video:
        con["file_id"] = update.message.video.file_id
        con["file_type"] = "video"
        label = "🎬 Видео получено"
    elif update.message.text:
        con["file_id"] = None
        con["file_type"] = "text"
        con["text_content"] = update.message.text
        label = "📝 Текст получен"
    else:
        await update.message.reply_text(
            "⚠️ Пришли фото, видео, документ или текст новости."
        )
        return CON_FILE

    await update.message.reply_text(
        f"✅ {label}\n\n"
        f"📌 *Шаг 3/4* — Напиши *описание*:\n"
        f"Что происходит? Кто в кадре? Какое событие?\n"
        f"_Чем подробнее — тем лучше!_",
        parse_mode="Markdown",
    )
    return CON_DESCRIPTION


# ─── Шаг 3: Описание ─────────────────────────────────────────────────────────

async def con_got_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    desc = update.message.text.strip()
    if len(desc) < 5:
        await update.message.reply_text("⚠️ Пожалуйста, опиши подробнее — хотя бы несколько слов.")
        return CON_DESCRIPTION

    context.user_data["con"]["description"] = desc
    await update.message.reply_text(
        f"✅ Описание записано!\n\n"
        f"📌 *Шаг 4/4* — Укажи *место / событие*:",
        parse_mode="Markdown",
        reply_markup=_location_keyboard(),
    )
    return CON_LOCATION


# ─── Шаг 4: Локация → Отправка ───────────────────────────────────────────────

async def con_got_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    location = query.data.replace("con_loc_", "")
    con = context.user_data["con"]
    con["location"] = location

    user = update.effective_user
    db_user = get_user(user.id)
    submitter_name = db_user["full_name"] if db_user else (user.full_name or user.username or str(user.id))

    # Сохраняем в БД
    sub_id = save_submission(
        telegram_id=user.id,
        submitter_name=submitter_name,
        content_type=con["type"],
        description=con["description"],
        location=location,
        file_id=con.get("file_id"),
        file_type=con.get("file_type", "unknown"),
    )

    # Уведомление в группу
    admin_text = (
        f"📥 *Новая заявка #{sub_id}*\n\n"
        f"👤 {submitter_name}"
        f" (@{user.username or '—'})\n"
        f"📌 Тип: {con['type']}\n"
        f"📍 Место: {location}\n"
        f"📝 Описание: {con['description']}\n"
    )
    bot = query.get_bot()

    try:
        if con.get("file_type") == "photo" and con.get("file_id"):
            await bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=con["file_id"],
                caption=admin_text,
                parse_mode="Markdown",
            )
        elif con.get("file_type") == "video" and con.get("file_id"):
            await bot.send_video(
                chat_id=ADMIN_GROUP_ID,
                video=con["file_id"],
                caption=admin_text,
                parse_mode="Markdown",
            )
        elif con.get("file_type") == "document" and con.get("file_id"):
            await bot.send_document(
                chat_id=ADMIN_GROUP_ID,
                document=con["file_id"],
                caption=admin_text,
                parse_mode="Markdown",
            )
        else:
            await bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=admin_text + (f"\n\n📄 Текст:\n{con.get('text_content', '')}"),
                parse_mode="Markdown",
            )
    except Exception as e:
        logger.warning("Не удалось отправить материал в группу: %s", e)

    await query.message.edit_text(
        f"🎉 *Спасибо! Материал отправлен в редакцию.*\n\n"
        f"📋 Заявка #{sub_id}\n"
        f"📌 {con['type']} | 📍 {location}\n\n"
        f"Редакторы рассмотрят и свяжутся с тобой, если потребуется что-то уточнить.",
        parse_mode="Markdown",
    )
    await query.message.reply_text(
        "Возвращаемся в меню 👇",
        reply_markup=MAIN_KEYBOARD,
    )

    context.user_data.pop("con", None)
    return ConversationHandler.END


# ─── ConversationHandler ─────────────────────────────────────────────────────

content_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(f"^{MENU_CONTENT}$"), content_start),
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
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)
