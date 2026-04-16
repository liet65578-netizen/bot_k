"""
Раздел «Хочу в команду!» — многошаговая регистрация
Шаги: ФИО → Класс → Специализация (мульти) → Программы → Подтверждение
"""

import json
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

from config import CLASSES, SPECS, ADMIN_GROUP_ID
from database import upsert_user, is_registered, get_user
from handlers.main_menu import MAIN_KEYBOARD, MENU_TEAM, cancel

logger = logging.getLogger(__name__)

# ─── Состояния диалога ───────────────────────────────────────────────────────
(
    REG_NAME,
    REG_CLASS,
    REG_SPEC,
    REG_SOFTWARE,
    REG_CONFIRM,
) = range(5)

REGISTRATION_STATES = {
    "REG_NAME": REG_NAME,
    "REG_CLASS": REG_CLASS,
    "REG_SPEC": REG_SPEC,
    "REG_SOFTWARE": REG_SOFTWARE,
    "REG_CONFIRM": REG_CONFIRM,
}

# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _class_keyboard() -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, cls in enumerate(CLASSES):
        row.append(InlineKeyboardButton(cls, callback_data=f"reg_class_{cls}"))
        if len(row) == 4 or cls == "Учитель / Сотрудник":
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def _spec_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for spec in SPECS:
        mark = "✅ " if spec in selected else ""
        rows.append([InlineKeyboardButton(f"{mark}{spec}", callback_data=f"reg_spec_{spec}")])
    rows.append([InlineKeyboardButton("➡️ Далее →", callback_data="reg_spec_done")])
    return InlineKeyboardMarkup(rows)


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Всё верно!", callback_data="reg_confirm_yes"),
            InlineKeyboardButton("✏️ Исправить", callback_data="reg_confirm_no"),
        ]
    ])


# ─── Точка входа ─────────────────────────────────────────────────────────────

async def reg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if is_registered(user_id):
        row = get_user(user_id)
        specs = json.loads(row["specs"])
        await update.message.reply_text(
            f"✅ *Ты уже в нашей команде!*\n\n"
            f"👤 {row['full_name']} | {row['class_name']}\n"
            f"🎯 {', '.join(specs)}\n\n"
            f"Чтобы обновить данные — пройди анкету снова.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Обновить анкету", callback_data="reg_restart")]
            ]),
        )
        return ConversationHandler.END

    context.user_data["reg"] = {"specs": []}
    await update.message.reply_text(
        "🎥 *Добро пожаловать в команду Klasyk TV!*\n\n"
        "Заполним небольшую анкету — это займёт 1-2 минуты.\n\n"
        "📝 *Шаг 1/4* — Напиши своё *ФИО* (Фамилия Имя Отчество):",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return REG_NAME


async def reg_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["reg"] = {"specs": []}
    await query.message.reply_text(
        "📝 *Шаг 1/4* — Напиши своё *ФИО*:",
        parse_mode="Markdown",
    )
    return REG_NAME


# ─── Шаг 1: ФИО ──────────────────────────────────────────────────────────────

async def reg_got_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    if len(name.split()) < 2:
        await update.message.reply_text(
            "⚠️ Пожалуйста, введи полное ФИО (минимум Фамилия и Имя):"
        )
        return REG_NAME

    context.user_data["reg"]["full_name"] = name
    await update.message.reply_text(
        f"👍 Записал: *{name}*\n\n"
        f"📝 *Шаг 2/4* — Выбери свой *класс*:",
        parse_mode="Markdown",
        reply_markup=_class_keyboard(),
    )
    return REG_CLASS


# ─── Шаг 2: Класс ────────────────────────────────────────────────────────────

async def reg_got_class(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    chosen = query.data.replace("reg_class_", "")
    context.user_data["reg"]["class_name"] = chosen
    context.user_data["reg"]["specs"] = []

    await query.message.edit_text(
        f"👍 Класс: *{chosen}*\n\n"
        f"📝 *Шаг 3/4* — Выбери *специализацию(и)*.\n"
        f"Можно выбрать несколько! Нажми ➡️ Далее когда закончишь:",
        parse_mode="Markdown",
        reply_markup=_spec_keyboard([]),
    )
    return REG_SPEC


# ─── Шаг 3: Специализация (мульти-выбор) ─────────────────────────────────────

async def reg_toggle_spec(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "reg_spec_done":
        specs = context.user_data["reg"].get("specs", [])
        if not specs:
            await query.answer("⚠️ Выбери хотя бы одну специализацию!", show_alert=True)
            return REG_SPEC

        await query.message.edit_text(
            f"👍 Специализации: *{', '.join(specs)}*\n\n"
            f"📝 *Шаг 4/4* — Какими *программами* ты владеешь?\n"
            f"_(CapCut, VN, Premiere, Photoshop, Canva и т.д. — пиши в свободной форме)_",
            parse_mode="Markdown",
        )
        return REG_SOFTWARE

    spec = data.replace("reg_spec_", "")
    specs = context.user_data["reg"]["specs"]
    if spec in specs:
        specs.remove(spec)
    else:
        specs.append(spec)

    await query.message.edit_reply_markup(reply_markup=_spec_keyboard(specs))
    return REG_SPEC


# ─── Шаг 4: Программы ────────────────────────────────────────────────────────

async def reg_got_software(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    software = update.message.text.strip()
    context.user_data["reg"]["software"] = software
    reg = context.user_data["reg"]

    summary = (
        f"📋 *Проверь свою анкету:*\n\n"
        f"👤 ФИО: *{reg['full_name']}*\n"
        f"🏫 Класс: *{reg['class_name']}*\n"
        f"🎯 Специализация: *{', '.join(reg['specs'])}*\n"
        f"💻 Программы: *{software}*\n\n"
        f"Всё верно?"
    )
    await update.message.reply_text(
        summary,
        parse_mode="Markdown",
        reply_markup=_confirm_keyboard(),
    )
    return REG_CONFIRM


# ─── Шаг 5: Подтверждение ────────────────────────────────────────────────────

async def reg_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "reg_confirm_no":
        context.user_data["reg"] = {"specs": []}
        await query.message.reply_text(
            "🔄 Начнём заново!\n\n📝 *Шаг 1/4* — Напиши своё *ФИО*:",
            parse_mode="Markdown",
        )
        return REG_NAME

    # Сохраняем в БД
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

    # Уведомляем админ-группу
    admin_msg = (
        f"🆕 *Новый участник редакции!*\n\n"
        f"👤 {reg['full_name']} | {reg['class_name']}\n"
        f"🎯 {', '.join(reg['specs'])}\n"
        f"💻 {reg['software']}\n"
        f"🔗 @{user.username or 'нет username'} | ID: `{user.id}`"
    )
    try:
        await query.get_bot().send_message(
            chat_id=ADMIN_GROUP_ID,
            text=admin_msg,
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning("Не удалось отправить уведомление в группу: %s", e)

    await query.message.edit_text(
        f"🎉 *Поздравляем, {reg['full_name'].split()[1]}!*\n\n"
        f"Ты успешно зарегистрирован(а) в команде *Klasyk TV*!\n\n"
        f"Мы скоро свяжемся с тобой. Следи за обновлениями в боте 🚀",
        parse_mode="Markdown",
    )
    await query.message.reply_text(
        "Возвращаемся в главное меню 👇",
        reply_markup=MAIN_KEYBOARD,
    )

    context.user_data.pop("reg", None)
    return ConversationHandler.END


# ─── ConversationHandler ─────────────────────────────────────────────────────

registration_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex(f"^{MENU_TEAM}$"), reg_start),
    ],
    states={
        REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_got_name)],
        REG_CLASS: [CallbackQueryHandler(reg_got_class, pattern="^reg_class_")],
        REG_SPEC: [
            CallbackQueryHandler(reg_toggle_spec, pattern="^reg_spec_"),
        ],
        REG_SOFTWARE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_got_software)],
        REG_CONFIRM: [CallbackQueryHandler(reg_confirm, pattern="^reg_confirm_")],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CallbackQueryHandler(reg_restart, pattern="^reg_restart$"),
    ],
    allow_reentry=True,
)
