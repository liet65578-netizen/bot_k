"""
Раздел «👤 Мой профиль» — информация об участнике
"""

import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_user, get_user_signups
from handlers.main_menu import MAIN_KEYBOARD


STATUS_LABELS = {
    "pending": "⏳ На рассмотрении",
    "active":  "✅ Активный участник",
    "inactive": "❌ Неактивный",
}


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    row = get_user(user_id)

    if not row:
        await update.message.reply_text(
            "👤 *Профиль не найден*\n\n"
            "Ты ещё не зарегистрирован(а) в команде.\n"
            "Нажми *«🎥 Хочу в команду!»* чтобы заполнить анкету.",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    specs = json.loads(row["specs"])
    signups = get_user_signups(user_id)
    status = STATUS_LABELS.get(row["status"], row["status"])

    signup_text = ""
    if signups:
        signup_text = "\n\n📋 *Мои записи на съёмку:*\n"
        for ev in signups:
            signup_text += f"• {ev['title']} — {ev['date_str']}\n"

    text = (
        f"👤 *Мой профиль*\n\n"
        f"📛 *{row['full_name']}*\n"
        f"🏫 Класс: {row['class_name']}\n"
        f"🎯 Специализация: {', '.join(specs)}\n"
        f"💻 Программы: {row['software'] or '—'}\n"
        f"📅 В команде с: {row['registered_at']}\n"
        f"🔖 Статус: {status}"
        f"{signup_text}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Обновить анкету", callback_data="profile_edit")]
        ]),
    )


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "profile_edit":
        await query.message.reply_text(
            "✏️ Чтобы обновить данные — нажми *«🎥 Хочу в команду!»* в меню.\n"
            "Анкета перезапишется.",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
