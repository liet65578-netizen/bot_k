"""
Главное меню: /start, постоянная клавиатура, роутинг
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

logger = logging.getLogger(__name__)

# ─── Кнопки главного меню ────────────────────────────────────────────────────
MENU_TEAM      = "🎥 Хочу в команду!"
MENU_CONTENT   = "📥 Предложить контент"
MENU_SCHEDULE  = "📅 План съёмок"
MENU_KNOWLEDGE = "📚 База знаний"
MENU_PROFILE   = "👤 Мой профиль"

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton(MENU_TEAM), KeyboardButton(MENU_CONTENT)],
        [KeyboardButton(MENU_SCHEDULE), KeyboardButton(MENU_KNOWLEDGE)],
        [KeyboardButton(MENU_PROFILE)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выбери раздел 👇",
)

WELCOME_TEXT = (
    "👋 *Привет! Добро пожаловать в Klasyk Media Hub!*\n\n"
    "Я помогаю нашей школьной редакции собирать контент, "
    "регистрировать участников и планировать съёмки.\n\n"
    "Выбери нужный раздел в меню ниже 👇"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *Главное меню*\n\nВыбери раздел:",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена любого активного диалога."""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=MAIN_KEYBOARD,
    )
    return ConversationHandler.END


async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Роутинг нажатий на главное меню."""
    text = update.message.text if update.message else None
    query = update.callback_query

    if query:
        await query.answer()
        data = query.data
        if data == "main_menu":
            await query.message.reply_text(
                "📋 Главное меню — выбери раздел:",
                reply_markup=MAIN_KEYBOARD,
            )
        return

    if text == MENU_SCHEDULE:
        from handlers.schedule import show_schedule
        await show_schedule(update, context)
    elif text == MENU_KNOWLEDGE:
        from handlers.knowledge import show_knowledge_menu
        await show_knowledge_menu(update, context)
    elif text == MENU_PROFILE:
        from handlers.profile import show_profile
        await show_profile(update, context)
    elif text in (MENU_TEAM, MENU_CONTENT):
        # Эти разделы ловятся ConversationHandler раньше
        pass
    else:
        await update.message.reply_text(
            "Используй кнопки меню 👇",
            reply_markup=MAIN_KEYBOARD,
        )
