"""
Панель администратора — управление ботом через Telegram
Доступ: /admin (только для MAIN_ADMIN_ID)
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

from config import MAIN_ADMIN_ID
from database import (
    get_users_count,
    get_submissions_count,
    get_events_count,
    get_signups_count,
    get_all_users,
    get_users_by_status,
    get_user,
    set_user_status,
    delete_user,
    get_all_submissions,
    get_submission,
    set_submission_status,
    get_upcoming_events,
    get_event,
    get_event_signups,
    add_event,
    delete_event,
    get_active_user_ids,
)

logger = logging.getLogger(__name__)

# ─── Состояния ConversationHandler ───────────────────────────────────────────
(
    ADM_EVENT_TITLE,
    ADM_EVENT_DATE,
    ADM_EVENT_TIME,
    ADM_EVENT_LOCATION,
    ADM_EVENT_DESC,
    ADM_BROADCAST_TEXT,
    ADM_BROADCAST_CONFIRM,
) = range(100, 107)


def is_admin(user_id: int) -> bool:
    return user_id == MAIN_ADMIN_ID


# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")],
        [
            InlineKeyboardButton("👥 Пользователи", callback_data="adm_users"),
            InlineKeyboardButton("📥 Заявки", callback_data="adm_subs"),
        ],
        [
            InlineKeyboardButton("📅 События", callback_data="adm_events"),
            InlineKeyboardButton("➕ Новое событие", callback_data="adm_event_add"),
        ],
        [InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast")],
    ])


def _back_to_admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад в админ-панель", callback_data="adm_back")]
    ])


# ═════════════════════════════════════════════════════════════════════════════
# /admin — Точка входа
# ═════════════════════════════════════════════════════════════════════════════

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ У тебя нет доступа к панели администратора.")
        return

    await update.message.reply_text(
        "🔧 *Панель администратора*\n\nВыбери раздел:",
        parse_mode="Markdown",
        reply_markup=_admin_main_kb(),
    )


# ═════════════════════════════════════════════════════════════════════════════
# Callback роутер
# ═════════════════════════════════════════════════════════════════════════════

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return
    await query.answer()

    data = query.data

    # ─── Навигация ────────────────────────────────────────────────────────
    if data == "adm_back":
        await query.message.edit_text(
            "🔧 *Панель администратора*\n\nВыбери раздел:",
            parse_mode="Markdown",
            reply_markup=_admin_main_kb(),
        )
        return

    # ─── Статистика ───────────────────────────────────────────────────────
    if data == "adm_stats":
        await _show_stats(query)
        return

    # ─── Пользователи ────────────────────────────────────────────────────
    if data == "adm_users":
        await _show_users_menu(query)
        return
    if data.startswith("adm_users_"):
        await _handle_users(query, data)
        return
    if data.startswith("adm_user_"):
        await _handle_user_action(query, data)
        return

    # ─── Контент-заявки ───────────────────────────────────────────────────
    if data == "adm_subs":
        await _show_subs_menu(query)
        return
    if data.startswith("adm_subs_"):
        await _handle_subs_list(query, data)
        return
    if data.startswith("adm_sub_"):
        await _handle_sub_action(query, data, context)
        return

    # ─── События ──────────────────────────────────────────────────────────
    if data == "adm_events":
        await _show_events_admin(query)
        return
    if data.startswith("adm_ev_"):
        await _handle_event_action(query, data)
        return


# ═════════════════════════════════════════════════════════════════════════════
# 📊 Статистика
# ═════════════════════════════════════════════════════════════════════════════

async def _show_stats(query) -> None:
    uc = get_users_count()
    sc = get_submissions_count()
    ec = get_events_count()
    su = get_signups_count()

    text = (
        "📊 *Статистика Klasyk Media Hub*\n\n"
        "👥 *Пользователи:*\n"
        f"  Всего: {uc['total']}\n"
        f"  ✅ Активные: {uc['active']}\n"
        f"  ⏳ На рассмотрении: {uc['pending']}\n"
        f"  ❌ Неактивные: {uc['inactive']}\n\n"
        "📥 *Контент-заявки:*\n"
        f"  Всего: {sc['total']}\n"
        f"  🆕 Новые: {sc['new']}\n"
        f"  ✅ Одобрено: {sc['approved']}\n"
        f"  ❌ Отклонено: {sc['rejected']}\n\n"
        f"📅 Событий: {ec}\n"
        f"📋 Записей на съёмки: {su}"
    )
    await query.message.edit_text(
        text, parse_mode="Markdown", reply_markup=_back_to_admin_kb()
    )


# ═════════════════════════════════════════════════════════════════════════════
# 👥 Пользователи
# ═════════════════════════════════════════════════════════════════════════════

async def _show_users_menu(query) -> None:
    uc = get_users_count()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Все ({uc['total']})", callback_data="adm_users_all")],
        [InlineKeyboardButton(f"⏳ Ожидающие ({uc['pending']})", callback_data="adm_users_pending")],
        [InlineKeyboardButton(f"✅ Активные ({uc['active']})", callback_data="adm_users_active")],
        [InlineKeyboardButton(f"❌ Неактивные ({uc['inactive']})", callback_data="adm_users_inactive")],
        [InlineKeyboardButton("◀️ Назад", callback_data="adm_back")],
    ])
    await query.message.edit_text(
        "👥 *Управление пользователями*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def _handle_users(query, data: str) -> None:
    status_map = {
        "adm_users_all": None,
        "adm_users_pending": "pending",
        "adm_users_active": "active",
        "adm_users_inactive": "inactive",
    }
    status = status_map.get(data)
    users = get_users_by_status(status) if status else get_all_users()

    if not users:
        await query.message.edit_text(
            "👥 Нет пользователей в этой категории.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="adm_users")]
            ]),
        )
        return

    status_icons = {"pending": "⏳", "active": "✅", "inactive": "❌"}
    text = "👥 *Список пользователей:*\n\n"
    buttons = []

    for u in users[:20]:
        icon = status_icons.get(u["status"], "❔")
        specs = json.loads(u["specs"])
        text += (
            f"{icon} *{u['full_name']}* | {u['class_name']}\n"
            f"    🎯 {', '.join(specs)}\n"
            f"    📅 {u['registered_at']}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                f"⚙️ {u['full_name'][:25]}",
                callback_data=f"adm_user_view_{u['telegram_id']}"
            )
        ])

    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="adm_users")])

    # Telegram ограничивает сообщения 4096 символами
    if len(text) > 4000:
        text = text[:4000] + "\n\n_...список обрезан_"

    await query.message.edit_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def _handle_user_action(query, data: str) -> None:
    parts = data.split("_")
    # adm_user_view_123, adm_user_activate_123, etc.
    action = parts[2]
    uid = int(parts[3])

    if action == "view":
        user = get_user(uid)
        if not user:
            await query.message.edit_text(
                "⚠️ Пользователь не найден.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="adm_users")]
                ]),
            )
            return

        specs = json.loads(user["specs"])
        status_icons = {"pending": "⏳ Ожидающий", "active": "✅ Активный", "inactive": "❌ Неактивный"}
        text = (
            f"👤 *Карточка участника*\n\n"
            f"📛 *{user['full_name']}*\n"
            f"🏫 Класс: {user['class_name']}\n"
            f"🎯 Специализация: {', '.join(specs)}\n"
            f"💻 ПО: {user['software'] or '—'}\n"
            f"📅 Зарегистрирован: {user['registered_at']}\n"
            f"🔖 Статус: {status_icons.get(user['status'], user['status'])}\n"
            f"🔗 @{user['username'] or '—'} | ID: `{uid}`"
        )

        buttons = []
        if user["status"] != "active":
            buttons.append([InlineKeyboardButton(
                "✅ Активировать", callback_data=f"adm_user_activate_{uid}"
            )])
        if user["status"] != "inactive":
            buttons.append([InlineKeyboardButton(
                "❌ Деактивировать", callback_data=f"adm_user_deactivate_{uid}"
            )])
        if user["status"] == "pending":
            buttons.append([InlineKeyboardButton(
                "🗑 Отклонить и удалить", callback_data=f"adm_user_delete_{uid}"
            )])
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="adm_users")])

        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if action == "activate":
        set_user_status(uid, "active")
        try:
            await query.get_bot().send_message(
                chat_id=uid,
                text="🎉 *Отличные новости!*\n\nТвоя заявка в команду Klasyk TV одобрена! Добро пожаловать ✅",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning("Не удалось уведомить пользователя %s: %s", uid, e)
        await query.answer("✅ Пользователь активирован!", show_alert=True)
        # Перезагрузить карточку
        data_view = f"adm_user_view_{uid}"
        await _handle_user_action(query, data_view)
        return

    if action == "deactivate":
        set_user_status(uid, "inactive")
        try:
            await query.get_bot().send_message(
                chat_id=uid,
                text="ℹ️ Твой статус в команде Klasyk TV изменён на *неактивный*.\n\nОбратись к администратору, если есть вопросы.",
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning("Не удалось уведомить пользователя %s: %s", uid, e)
        await query.answer("❌ Пользователь деактивирован", show_alert=True)
        data_view = f"adm_user_view_{uid}"
        await _handle_user_action(query, data_view)
        return

    if action == "delete":
        user = get_user(uid)
        name = user["full_name"] if user else str(uid)
        delete_user(uid)
        try:
            await query.get_bot().send_message(
                chat_id=uid,
                text="ℹ️ К сожалению, твоя заявка в команду Klasyk TV была отклонена.\n\nТы можешь подать заявку повторно.",
            )
        except Exception as e:
            logger.warning("Не удалось уведомить пользователя %s: %s", uid, e)
        await query.message.edit_text(
            f"🗑 Пользователь *{name}* удалён.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ К пользователям", callback_data="adm_users")]
            ]),
        )
        return


# ═════════════════════════════════════════════════════════════════════════════
# 📥 Контент-заявки
# ═════════════════════════════════════════════════════════════════════════════

async def _show_subs_menu(query) -> None:
    sc = get_submissions_count()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🆕 Новые ({sc['new']})", callback_data="adm_subs_new")],
        [InlineKeyboardButton(f"✅ Одобренные ({sc['approved']})", callback_data="adm_subs_approved")],
        [InlineKeyboardButton(f"❌ Отклонённые ({sc['rejected']})", callback_data="adm_subs_rejected")],
        [InlineKeyboardButton(f"📋 Все ({sc['total']})", callback_data="adm_subs_all")],
        [InlineKeyboardButton("◀️ Назад", callback_data="adm_back")],
    ])
    await query.message.edit_text(
        "📥 *Управление контент-заявками*\n\nВыбери категорию:",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def _handle_subs_list(query, data: str) -> None:
    status_map = {
        "adm_subs_new": "new",
        "adm_subs_approved": "approved",
        "adm_subs_rejected": "rejected",
        "adm_subs_all": None,
    }
    status = status_map.get(data)
    subs = get_all_submissions(status=status)

    if not subs:
        await query.message.edit_text(
            "📥 Нет заявок в этой категории.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("◀️ Назад", callback_data="adm_subs")]
            ]),
        )
        return

    status_icons = {"new": "🆕", "approved": "✅", "rejected": "❌"}
    text = "📥 *Контент-заявки:*\n\n"
    buttons = []

    for s in subs[:15]:
        icon = status_icons.get(s["status"], "❔")
        text += (
            f"{icon} *#{s['id']}* — {s['content_type']}\n"
            f"    👤 {s['submitter_name']} | 📍 {s['location']}\n"
            f"    📅 {s['submitted_at']}\n\n"
        )
        buttons.append([
            InlineKeyboardButton(
                f"👁 Заявка #{s['id']}",
                callback_data=f"adm_sub_view_{s['id']}"
            )
        ])

    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="adm_subs")])

    if len(text) > 4000:
        text = text[:4000] + "\n\n_...список обрезан_"

    await query.message.edit_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def _handle_sub_action(query, data: str, context) -> None:
    parts = data.split("_")
    action = parts[2]
    sub_id = int(parts[3])

    if action == "view":
        sub = get_submission(sub_id)
        if not sub:
            await query.message.edit_text(
                "⚠️ Заявка не найдена.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="adm_subs")]
                ]),
            )
            return

        status_labels = {"new": "🆕 Новая", "approved": "✅ Одобрена", "rejected": "❌ Отклонена"}
        text = (
            f"📥 *Заявка #{sub['id']}*\n\n"
            f"👤 Автор: *{sub['submitter_name']}*\n"
            f"📌 Тип: {sub['content_type']}\n"
            f"📍 Место: {sub['location']}\n"
            f"📝 Описание: {sub['description']}\n"
            f"📎 Файл: {'Есть (' + sub['file_type'] + ')' if sub['file_id'] else 'Нет (текст)'}\n"
            f"📅 Дата: {sub['submitted_at']}\n"
            f"🔖 Статус: {status_labels.get(sub['status'], sub['status'])}"
        )

        buttons = []
        if sub["file_id"]:
            buttons.append([InlineKeyboardButton(
                "📎 Показать файл", callback_data=f"adm_sub_file_{sub_id}"
            )])
        if sub["status"] != "approved":
            buttons.append([InlineKeyboardButton(
                "✅ Одобрить", callback_data=f"adm_sub_approve_{sub_id}"
            )])
        if sub["status"] != "rejected":
            buttons.append([InlineKeyboardButton(
                "❌ Отклонить", callback_data=f"adm_sub_reject_{sub_id}"
            )])
        buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="adm_subs")])

        await query.message.edit_text(
            text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if action == "file":
        sub = get_submission(sub_id)
        if not sub or not sub["file_id"]:
            await query.answer("Файл не найден", show_alert=True)
            return
        bot = query.get_bot()
        try:
            if sub["file_type"] == "photo":
                await bot.send_photo(chat_id=query.from_user.id, photo=sub["file_id"],
                                     caption=f"📥 Заявка #{sub_id} от {sub['submitter_name']}")
            elif sub["file_type"] == "video":
                await bot.send_video(chat_id=query.from_user.id, video=sub["file_id"],
                                     caption=f"📥 Заявка #{sub_id} от {sub['submitter_name']}")
            else:
                await bot.send_document(chat_id=query.from_user.id, document=sub["file_id"],
                                        caption=f"📥 Заявка #{sub_id} от {sub['submitter_name']}")
        except Exception as e:
            logger.warning("Ошибка отправки файла: %s", e)
            await query.answer("Ошибка при отправке файла", show_alert=True)
        return

    if action == "approve":
        sub = get_submission(sub_id)
        set_submission_status(sub_id, "approved")
        if sub:
            try:
                await query.get_bot().send_message(
                    chat_id=sub["telegram_id"],
                    text=(
                        f"✅ *Твоя заявка #{sub_id} одобрена!*\n\n"
                        f"📌 {sub['content_type']} | 📍 {sub['location']}\n"
                        f"Спасибо за вклад в Klasyk TV! 🎉"
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Не удалось уведомить автора заявки: %s", e)
        await query.answer("✅ Заявка одобрена!", show_alert=True)
        data_view = f"adm_sub_view_{sub_id}"
        await _handle_sub_action(query, data_view, context)
        return

    if action == "reject":
        sub = get_submission(sub_id)
        set_submission_status(sub_id, "rejected")
        if sub:
            try:
                await query.get_bot().send_message(
                    chat_id=sub["telegram_id"],
                    text=(
                        f"❌ *Заявка #{sub_id} не прошла модерацию*\n\n"
                        f"📌 {sub['content_type']} | 📍 {sub['location']}\n"
                        f"Попробуй отправить снова с более качественным материалом."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Не удалось уведомить автора заявки: %s", e)
        await query.answer("❌ Заявка отклонена", show_alert=True)
        data_view = f"adm_sub_view_{sub_id}"
        await _handle_sub_action(query, data_view, context)
        return


# ═════════════════════════════════════════════════════════════════════════════
# 📅 События — просмотр / удаление / записи
# ═════════════════════════════════════════════════════════════════════════════

async def _show_events_admin(query) -> None:
    events = get_upcoming_events()
    if not events:
        await query.message.edit_text(
            "📅 Нет событий.\n\nНажми ➕ чтобы создать новое.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Создать событие", callback_data="adm_event_add")],
                [InlineKeyboardButton("◀️ Назад", callback_data="adm_back")],
            ]),
        )
        return

    text = "📅 *Управление событиями:*\n\n"
    buttons = []
    for ev in events:
        signups = get_event_signups(ev["id"])
        text += (
            f"*{ev['title']}*\n"
            f"📆 {ev['date_str']} 🕐 {ev['time_str'] or '—'} | 📍 {ev['location']}\n"
            f"👥 Записалось: {len(signups)} чел.\n\n"
        )
        buttons.append([
            InlineKeyboardButton(f"👁 {ev['title'][:25]}", callback_data=f"adm_ev_view_{ev['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"adm_ev_del_{ev['id']}"),
        ])

    buttons.append([InlineKeyboardButton("➕ Новое событие", callback_data="adm_event_add")])
    buttons.append([InlineKeyboardButton("◀️ Назад", callback_data="adm_back")])

    if len(text) > 4000:
        text = text[:4000] + "\n\n_...обрезано_"

    await query.message.edit_text(
        text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def _handle_event_action(query, data: str) -> None:
    parts = data.split("_")
    action = parts[2]
    ev_id = int(parts[3])

    if action == "view":
        ev = get_event(ev_id)
        if not ev:
            await query.answer("Событие не найдено", show_alert=True)
            return

        signups = get_event_signups(ev_id)
        text = (
            f"📅 *{ev['title']}*\n\n"
            f"📆 Дата: {ev['date_str']}\n"
            f"🕐 Время: {ev['time_str'] or '—'}\n"
            f"📍 Место: {ev['location']}\n"
            f"📝 Описание: {ev['description'] or '—'}\n\n"
        )

        if signups:
            text += f"👥 *Записалось ({len(signups)}):*\n"
            for s in signups:
                text += f"  • {s['full_name']} ({s['class_name']}) — @{s['username'] or '—'}\n"
        else:
            text += "👥 Пока никто не записался."

        await query.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 Удалить событие", callback_data=f"adm_ev_del_{ev_id}")],
                [InlineKeyboardButton("◀️ К событиям", callback_data="adm_events")],
            ]),
        )
        return

    if action == "del":
        ev = get_event(ev_id)
        title = ev["title"] if ev else f"#{ev_id}"
        delete_event(ev_id)
        await query.answer(f"🗑 Удалено: {title}", show_alert=True)
        await _show_events_admin(query)
        return


# ═════════════════════════════════════════════════════════════════════════════
# ➕ Создание события (ConversationHandler)
# ═════════════════════════════════════════════════════════════════════════════

async def event_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return ConversationHandler.END
    await query.answer()

    context.user_data["adm_event"] = {}
    await query.message.reply_text(
        "➕ *Создание нового события*\n\n"
        "📝 *Шаг 1/5* — Напиши *название* события\n"
        "_(например: 🏆 Финал КВН)_\n\n"
        "Отмена: /cancel",
        parse_mode="Markdown",
    )
    return ADM_EVENT_TITLE


async def event_got_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    context.user_data["adm_event"]["title"] = title
    await update.message.reply_text(
        f"✅ Название: *{title}*\n\n"
        f"📝 *Шаг 2/5* — Укажи *дату* (формат: ДД.ММ.ГГГГ)\n"
        f"_(например: 25.04.2026)_",
        parse_mode="Markdown",
    )
    return ADM_EVENT_DATE


async def event_got_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date_str = update.message.text.strip()
    # Простая валидация формата
    parts = date_str.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        await update.message.reply_text(
            "⚠️ Неверный формат. Введи дату как ДД.ММ.ГГГГ (например: 25.04.2026):"
        )
        return ADM_EVENT_DATE

    context.user_data["adm_event"]["date"] = date_str
    await update.message.reply_text(
        f"✅ Дата: *{date_str}*\n\n"
        f"📝 *Шаг 3/5* — Укажи *время* (ЧЧ:ММ)\n"
        f"_(например: 14:30, или «—» если неизвестно)_",
        parse_mode="Markdown",
    )
    return ADM_EVENT_TIME


async def event_got_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    time_str = update.message.text.strip()
    context.user_data["adm_event"]["time"] = time_str if time_str != "—" else None
    await update.message.reply_text(
        f"✅ Время: *{time_str}*\n\n"
        f"📝 *Шаг 4/5* — Укажи *место*\n"
        f"_(например: Актовый зал)_",
        parse_mode="Markdown",
    )
    return ADM_EVENT_LOCATION


async def event_got_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    location = update.message.text.strip()
    context.user_data["adm_event"]["location"] = location
    await update.message.reply_text(
        f"✅ Место: *{location}*\n\n"
        f"📝 *Шаг 5/5* — Напиши *описание / что нужно*\n"
        f"_(например: Нужны 2 оператора и фотограф)_",
        parse_mode="Markdown",
    )
    return ADM_EVENT_DESC


async def event_got_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    desc = update.message.text.strip()
    ev = context.user_data["adm_event"]

    event_id = add_event(
        title=ev["title"],
        date_str=ev["date"],
        time_str=ev.get("time"),
        location=ev["location"],
        description=desc,
        created_by=update.effective_user.id,
    )

    await update.message.reply_text(
        f"✅ *Событие создано!*\n\n"
        f"🆔 #{event_id}\n"
        f"📋 *{ev['title']}*\n"
        f"📆 {ev['date']}  🕐 {ev.get('time') or '—'}\n"
        f"📍 {ev['location']}\n"
        f"📝 {desc}\n\n"
        f"Оно уже видно участникам в «📅 План съёмок»!",
        parse_mode="Markdown",
    )
    context.user_data.pop("adm_event", None)
    return ConversationHandler.END


# ═════════════════════════════════════════════════════════════════════════════
# 📢 Рассылка (ConversationHandler)
# ═════════════════════════════════════════════════════════════════════════════

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔ Нет доступа", show_alert=True)
        return ConversationHandler.END
    await query.answer()

    user_ids = get_active_user_ids()
    context.user_data["adm_broadcast_count"] = len(user_ids)

    await query.message.reply_text(
        f"📢 *Рассылка*\n\n"
        f"Получателей: *{len(user_ids)}* пользователей\n\n"
        f"Напиши текст сообщения, которое получат все участники.\n"
        f"Поддерживается *Markdown* форматирование.\n\n"
        f"Отмена: /cancel",
        parse_mode="Markdown",
    )
    return ADM_BROADCAST_TEXT


async def broadcast_got_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    context.user_data["adm_broadcast_text"] = text
    count = context.user_data.get("adm_broadcast_count", 0)

    await update.message.reply_text(
        f"📢 *Превью рассылки:*\n\n"
        f"{text}\n\n"
        f"─────────────────\n"
        f"Будет отправлено *{count}* пользователям.\n"
        f"Подтвердить?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Отправить", callback_data="adm_bcast_yes"),
                InlineKeyboardButton("❌ Отмена", callback_data="adm_bcast_no"),
            ]
        ]),
    )
    return ADM_BROADCAST_CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "adm_bcast_no":
        await query.message.edit_text("❌ Рассылка отменена.")
        context.user_data.pop("adm_broadcast_text", None)
        context.user_data.pop("adm_broadcast_count", None)
        return ConversationHandler.END

    text = context.user_data.get("adm_broadcast_text", "")
    user_ids = get_active_user_ids()
    bot = query.get_bot()

    sent = 0
    failed = 0
    for uid in user_ids:
        try:
            await bot.send_message(
                chat_id=uid,
                text=f"📢 *Объявление от Klasyk TV*\n\n{text}",
                parse_mode="Markdown",
            )
            sent += 1
        except Exception:
            failed += 1

    await query.message.edit_text(
        f"📢 *Рассылка завершена!*\n\n"
        f"✅ Доставлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="Markdown",
    )

    context.user_data.pop("adm_broadcast_text", None)
    context.user_data.pop("adm_broadcast_count", None)
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("adm_event", None)
    context.user_data.pop("adm_broadcast_text", None)
    context.user_data.pop("adm_broadcast_count", None)
    await update.message.reply_text("❌ Действие отменено.")
    return ConversationHandler.END


# ═════════════════════════════════════════════════════════════════════════════
# ConversationHandlers
# ═════════════════════════════════════════════════════════════════════════════

event_add_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(event_add_start, pattern="^adm_event_add$"),
    ],
    states={
        ADM_EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_title)],
        ADM_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_date)],
        ADM_EVENT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_time)],
        ADM_EVENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_location)],
        ADM_EVENT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_desc)],
    },
    fallbacks=[CommandHandler("cancel", admin_cancel)],
    allow_reentry=True,
)

broadcast_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(broadcast_start, pattern="^adm_broadcast$"),
    ],
    states={
        ADM_BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_got_text)],
        ADM_BROADCAST_CONFIRM: [CallbackQueryHandler(broadcast_confirm, pattern="^adm_bcast_")],
    },
    fallbacks=[CommandHandler("cancel", admin_cancel)],
    allow_reentry=True,
)
