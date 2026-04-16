"""
Раздел «📅 План съёмок» — список мероприятий + запись
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_GROUP_ID, MAIN_ADMIN_ID
from database import get_upcoming_events, get_event, signup_for_event, get_user

logger = logging.getLogger(__name__)


async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    events = get_upcoming_events()
    if not events:
        await update.message.reply_text("📅 Пока нет запланированных событий. Загляни позже!")
        return

    text = "📅 *Ближайшие события — план съёмок:*\n\n"
    buttons = []

    for ev in events:
        text += (
            f"*{ev['title']}*\n"
            f"📆 {ev['date_str']}  🕐 {ev['time_str'] or '—'}\n"
            f"📍 {ev['location']}\n"
            f"💬 {ev['description'] or ''}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                f"📋 Записаться: {ev['title'][:30]}",
                callback_data=f"schedule_signup_{ev['id']}"
            )
        ])

    buttons.append([InlineKeyboardButton("🔄 Обновить список", callback_data="schedule_refresh")])

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "schedule_refresh":
        events = get_upcoming_events()
        text = "📅 *Актуальный план съёмок:*\n\n"
        buttons = []
        for ev in events:
            text += f"*{ev['title']}* — {ev['date_str']} {ev['time_str'] or ''}\n📍 {ev['location']}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    f"📋 Записаться: {ev['title'][:30]}",
                    callback_data=f"schedule_signup_{ev['id']}"
                )
            ])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("schedule_signup_"):
        event_id = int(data.replace("schedule_signup_", ""))
        user = update.effective_user
        db_user = get_user(user.id)
        name = db_user["full_name"] if db_user else (user.full_name or user.username or str(user.id))
        cls = db_user["class_name"] if db_user else "—"

        ev = get_event(event_id)
        if not ev:
            await query.answer("⚠️ Событие не найдено", show_alert=True)
            return

        already = not signup_for_event(user.id, event_id)

        if already:
            await query.answer(f"✅ Ты уже записан(а) на: {ev['title']}", show_alert=True)
            return

        # Уведомление администратору
        notify = (
            f"📸 *Запись на съёмку!*\n\n"
            f"👤 {name} из {cls}\n"
            f"🎬 Хочет снимать: *{ev['title']}*\n"
            f"📆 {ev['date_str']}  📍 {ev['location']}\n"
            f"🔗 @{user.username or '—'} | ID: `{user.id}`"
        )
        try:
            await query.get_bot().send_message(
                chat_id=ADMIN_GROUP_ID,
                text=notify,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning("Ошибка уведомления: %s", e)

        await query.answer(f"🎉 Записал тебя на «{ev['title']}»!", show_alert=True)
        await query.message.reply_text(
            f"✅ *Готово!* Ты записан(а) на:\n"
            f"*{ev['title']}*\n"
            f"📆 {ev['date_str']}  📍 {ev['location']}\n\n"
            f"Мы напомним ближе к дате 🔔",
            parse_mode="Markdown",
        )
