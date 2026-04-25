"""
Klasyk Media Hub — Telegram Bot
Точка входа: регистрация, предложка, план съёмок, база знаний, профиль
"""

import logging
import json
import os
import sys
from pathlib import Path
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN
from database import init_db, DATA_DIR
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
    handle_lang_callback,
    show_main_menu,
    cancel,
)
from handlers.schedule import schedule_handler
from handlers.knowledge import (
    knowledge_handler,
    admin_edit_knowledge,
    admin_choose_kb_lang,
    admin_edit_item,
    admin_save_knowledge,
)
from handlers.profile import profile_handler
from handlers.admin import (
    admin_cmd,
    admin_callback,
    event_add_handler,
    broadcast_handler,
)

from logging_config import setup_logging

setup_logging(BOT_TOKEN)
logger = logging.getLogger(__name__)

def _acquire_single_instance_lock() -> None:
    """
    Предотвращаем 409 Conflict:
    Telegram запрещает параллельные getUpdates для разных экземпляров того же бота.
    """
    lock_path = DATA_DIR / "bot.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    pid = os.getpid()
    try:
        # Exclusive create
        with open(lock_path, "x", encoding="utf-8") as f:
            f.write(str(pid))
    except FileExistsError:
        # Пытаемся понять, жив ли процесс
        try:
            old_pid = int(lock_path.read_text(encoding="utf-8").strip())
        except Exception:
            old_pid = None
        if old_pid:
            try:
                # Проверка "жив/не жив" кроссплатформенно
                # На Windows os.kill(pid, 0) обычно кидает исключение, если процесса нет.
                os.kill(old_pid, 0)
                # Если исключения нет — процесс жив, выходим
                logger.error("Bot already running (pid=%s). Exiting.", old_pid)
                sys.exit(0)
            except OSError:
                # Процесс не жив: lock stale, удаляем и продолжаем старт
                try:
                    lock_path.unlink(missing_ok=True)
                except Exception:
                    pass
                with open(lock_path, "x", encoding="utf-8") as f:
                    f.write(str(pid))
                return
        # Сломанный lock: перезапишем
        try:
            lock_path.unlink(missing_ok=True)
        except Exception:
            pass
        with open(lock_path, "x", encoding="utf-8") as f:
            f.write(str(pid))


async def _log_message_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный лог сообщений (чтобы понимать, кто и что нажимает)."""
    if not update.effective_user:
        return
    msg = update.message
    if not msg:
        return
    text = msg.text or msg.caption or ""
    logger.debug(
        "UPDATE message user_id=%s username=%s chat_id=%s text=%r",
        update.effective_user.id,
        update.effective_user.username,
        msg.chat_id,
        text[:200],
    )


async def _log_callback_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный лог нажатий inline-кнопок (только логирование, НЕ отвечаем на query)."""
    if not update.effective_user or not update.callback_query:
        return
    q = update.callback_query
    logger.debug(
        "UPDATE callback user_id=%s username=%s chat_id=%s data=%r",
        update.effective_user.id,
        update.effective_user.username,
        q.message.chat_id if q.message else None,
        q.data,
    )


async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    err = context.error
    if isinstance(err, BadRequest) and "Message is not modified" in str(err):
        # Частый безопасный кейс при edit_text/edit_message_text.
        logger.debug("Ignored BadRequest (not modified): %r", err)
        return
    logger.exception("Unhandled error. update=%s error=%r", type(update).__name__, err)

edit_knowledge_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(admin_edit_knowledge, pattern="^adm_edit_knowledge$")],
    states={
        "WAIT_KNOWLEDGE_LANG": [CallbackQueryHandler(admin_choose_kb_lang, pattern="^adm_kb_lang_")],
        # Сначала админ выбирает материал (кнопки adm_edit_...),
        # затем вводит новый текст (MessageHandler).
        "WAIT_KNOWLEDGE_SELECT": [CallbackQueryHandler(admin_edit_item, pattern="^adm_edit_")],
        "WAIT_KNOWLEDGE_TEXT": [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_knowledge)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
    conversation_timeout=600,
)

def main() -> None:
    _acquire_single_instance_lock()
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Глобальный дебаг (логируем все входящие апдейты до остальных обработчиков)
    app.add_handler(
        MessageHandler(filters.ALL, _log_message_update, block=False),
        group=-10,
    )
    app.add_handler(
        CallbackQueryHandler(_log_callback_update, pattern=".*", block=False),
        group=-10,
    )

    app.add_error_handler(_error_handler)

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

    # ConversationHandler для редактирования базы знаний
    app.add_handler(edit_knowledge_conv, group=0)

    # Callback кнопки (inline)
    app.add_handler(CallbackQueryHandler(handle_lang_callback, pattern="^set_lang_"))
    app.add_handler(CallbackQueryHandler(schedule_handler, pattern="^schedule"))
    app.add_handler(CallbackQueryHandler(knowledge_handler, pattern="^kb"))
    app.add_handler(CallbackQueryHandler(profile_handler, pattern="^profile"))
    app.add_handler(CallbackQueryHandler(handle_main_menu, pattern="^main"))

    # Сначала более специфичный обработчик:
    # app.add_handler(CallbackQueryHandler(admin_edit_item, pattern="^adm_edit_"))
    # Потом общий:
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"), group=1)

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
