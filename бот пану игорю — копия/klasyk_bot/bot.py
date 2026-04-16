"""
Klasyk Media Hub — Telegram Bot
Точка входа: регистрация, предложка, план съёмок, база знаний, профиль
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import BOT_TOKEN
from database import init_db
from handlers.registration import (
    registration_handler,
    REGISTRATION_STATES,
)
from handlers.content import (
    content_handler,
    CONTENT_STATES,
)
from handlers.main_menu import (
    start,
    handle_main_menu,
    show_main_menu,
    cancel,
)
from handlers.schedule import schedule_handler
from handlers.knowledge import knowledge_handler
from handlers.profile import profile_handler
from handlers.admin import (
    admin_cmd,
    admin_callback,
    event_add_handler,
    broadcast_handler,
)

logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Админ-панель (ConversationHandler'ы первыми — у них приоритет)
    app.add_handler(event_add_handler)
    app.add_handler(broadcast_handler)

    # Регистрация
    app.add_handler(registration_handler)

    # Предложка контента
    app.add_handler(content_handler)

    # Одиночные обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("menu", show_main_menu))
    app.add_handler(CommandHandler("admin", admin_cmd))

    # Callback кнопки (inline)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))
    app.add_handler(CallbackQueryHandler(schedule_handler, pattern="^schedule"))
    app.add_handler(CallbackQueryHandler(knowledge_handler, pattern="^kb"))
    app.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile"))
    app.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^main"))

    # Главное меню (reply keyboard)
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_main_menu,
        )
    )

    logger.info("🚀 Klasyk Media Hub Bot запущен")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
