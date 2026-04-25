"""
Admin panel — full management via Telegram with i18n.
"""
import asyncio
import json
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
)

from config import ADMIN_IDS
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
    get_storage_stats,
    get_top_users_by_storage,
    get_users_over_threshold,
)
from i18n import t, get_lang, DEFAULT_LANG, esc_md

logger = logging.getLogger(__name__)

# ConversationHandler states
(
    ADM_EVENT_TITLE,
    ADM_EVENT_DATE,
    ADM_EVENT_TIME,
    ADM_EVENT_LOCATION,
    ADM_EVENT_DESC,
    ADM_EVENT_NOTIFY_CONFIRM,
    ADM_BROADCAST_TEXT,
    ADM_BROADCAST_CONFIRM,
) = range(100, 108)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _admin_reply_kb(lang: str = DEFAULT_LANG):
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(t("menu_admin", lang))],
            [KeyboardButton(t("menu_schedule", lang)), KeyboardButton(t("menu_knowledge", lang))],
            [KeyboardButton(t("menu_profile", lang)), KeyboardButton(t("menu_lang", lang))],
        ],
        resize_keyboard=True,
        input_field_placeholder=t("menu_placeholder", lang),
    )


def _admin_main_kb(lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("adm_stats_btn", lang), callback_data="adm_stats")],
        [
            InlineKeyboardButton(t("adm_users_btn", lang), callback_data="adm_users"),
            InlineKeyboardButton(t("adm_subs_btn", lang), callback_data="adm_subs"),
        ],
        [
            InlineKeyboardButton(t("adm_events_btn", lang), callback_data="adm_events"),
            InlineKeyboardButton(t("adm_event_add_btn", lang), callback_data="adm_event_add"),
        ],
        [
            InlineKeyboardButton(t("adm_broadcast_btn", lang), callback_data="adm_broadcast"),
            InlineKeyboardButton(t("adm_edit_kb_btn", lang), callback_data="adm_edit_knowledge"),
        ],
        [InlineKeyboardButton(t("adm_storage_btn", lang), callback_data="adm_storage")],
    ])


def _back_kb(lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("adm_back_btn", lang), callback_data="adm_back")]
    ])


# ---- Entry ----

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id):
        lang = await get_lang(update, context)
        await update.message.reply_text(t("adm_no_access", lang))
        return
    lang = await get_lang(update, context)
    await update.message.reply_text(t("adm_updated", lang), reply_markup=_admin_reply_kb(lang))
    await update.message.reply_text(t("adm_title", lang), parse_mode="Markdown", reply_markup=_admin_main_kb(lang))


# ---- Callback router ----

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer(t("adm_no_access_short", "ru"), show_alert=True)
        return
    await query.answer()
    data = query.data
    lang = await get_lang(update, context)

    if data == "adm_back":
        await query.message.edit_text(t("adm_title", lang), parse_mode="Markdown", reply_markup=_admin_main_kb(lang))
        return
    if data == "adm_stats":
        await _show_stats(query, lang)
        return
    if data == "adm_storage":
        await _show_storage(query, lang)
        return
    if data == "adm_users":
        await _show_users_menu(query, lang)
        return
    if data.startswith("adm_users_"):
        await _handle_users(query, data, lang)
        return
    if data.startswith("adm_user_"):
        await _handle_user_action(query, data, lang)
        return
    if data == "adm_subs":
        await _show_subs_menu(query, lang)
        return
    if data.startswith("adm_subs_"):
        await _handle_subs_list(query, data, lang)
        return
    if data.startswith("adm_sub_"):
        await _handle_sub_action(query, data, context, lang)
        return
    if data == "adm_events":
        await _show_events_admin(query, lang)
        return
    if data.startswith("adm_ev_"):
        await _handle_event_action(query, data, lang)
        return

    # Fallback: unknown adm_ pattern — answer silently so button spinner stops
    logger.warning("Unhandled admin callback: %s", data)


# ---- Stats ----

async def _show_stats(query, lang) -> None:
    uc = get_users_count()
    sc = get_submissions_count()
    ec = get_events_count()
    su = get_signups_count()
    text = t("adm_stats", lang,
             total=uc["total"], active=uc["active"], pending=uc["pending"], inactive=uc["inactive"],
             sub_total=sc["total"], sub_new=sc["new"], sub_approved=sc["approved"], sub_rejected=sc["rejected"],
             events=ec, signups=su)
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=_back_kb(lang))


# ---- Storage monitor ----

def _fmt_size(b: int) -> str:
    """Human-readable size: 1.5 GB, 200 MB, 36 KB, 512 B."""
    if b >= 1_073_741_824:
        return f"{b / 1_073_741_824:.1f} GB"
    if b >= 1_048_576:
        return f"{b / 1_048_576:.1f} MB"
    if b >= 1024:
        return f"{b / 1024:.0f} KB"
    return f"{b} B"


async def _show_storage(query, lang) -> None:
    s = get_storage_stats()

    lines = [
        t("adm_storage_title", lang),
        "",
        t("adm_storage_total", lang, size=_fmt_size(s["bot_total"])),
        "",
        t("adm_storage_breakdown_title", lang),
        t("adm_storage_breakdown_code", lang, size=_fmt_size(s["code_size"])),
        t("adm_storage_breakdown_venv", lang, size=_fmt_size(s["venv_size"])),
        t("adm_storage_breakdown_data", lang, size=_fmt_size(s["data_size"])),
        t(
            "adm_storage_breakdown_global_db",
            lang,
            size=_fmt_size(s["global_db_size"]),
            wal=s["journal_mode"],
        ),
        t(
            "adm_storage_breakdown_user_dbs",
            lang,
            size=_fmt_size(s["user_db_total"]),
            users=s["user_count"],
        ),
        t("adm_storage_breakdown_logs", lang, size=_fmt_size(s["all_logs_size"])),
        "",
        t("adm_storage_tables_title", lang),
        t("adm_storage_tables_users_subs", lang, users=s["rows_users"], subs=s["rows_submissions"]),
        t("adm_storage_tables_events_signups", lang, events=s["rows_events"], signups=s["rows_signups"]),
        t("adm_storage_tables_kb", lang, kb=s["rows_knowledge"]),
    ]

    top = get_top_users_by_storage(5)
    if top:
        lines.append("")
        lines.append(t("adm_storage_top_title", lang))
        for i, u in enumerate(top, 1):
            user = get_user(u["telegram_id"])
            name = esc_md(user["full_name"]) if user else str(u["telegram_id"])
            lines.append(t("adm_storage_top_row", lang, n=i, name=name, size=_fmt_size(u["size"])))

    alerts = get_users_over_threshold()
    if alerts:
        lines.append("")
        lines.append(t("adm_storage_alerts_title", lang))
        for a in alerts:
            user = get_user(a["telegram_id"])
            name = esc_md(user["full_name"]) if user else str(a["telegram_id"])
            lines.append(t("adm_storage_alerts_row", lang, name=name, size=_fmt_size(a["size"])))
    else:
        lines.append("")
        lines.append(t("adm_storage_no_anomalies", lang))

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n_\\.\\.\\. truncated_"
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=_back_kb(lang))


# ---- Users ----

async def _show_users_menu(query, lang) -> None:
    uc = get_users_count()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("adm_users_all", lang, count=uc["total"]), callback_data="adm_users_all")],
        [InlineKeyboardButton(t("adm_users_pending", lang, count=uc["pending"]), callback_data="adm_users_pending")],
        [InlineKeyboardButton(t("adm_users_active", lang, count=uc["active"]), callback_data="adm_users_active")],
        [InlineKeyboardButton(t("adm_users_inactive", lang, count=uc["inactive"]), callback_data="adm_users_inactive")],
        [InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_back")],
    ])
    await query.message.edit_text(t("adm_users_title", lang), parse_mode="Markdown", reply_markup=kb)


async def _handle_users(query, data, lang) -> None:
    status_map = {"adm_users_all": None, "adm_users_pending": "pending",
                  "adm_users_active": "active", "adm_users_inactive": "inactive"}
    status = status_map.get(data)
    users = get_users_by_status(status) if status else get_all_users()
    if not users:
        await query.message.edit_text(
            t("adm_users_empty", lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_users")]]),
        )
        return

    status_icons = {"pending": "⏳", "active": "✅", "inactive": "❌"}
    text = t("adm_users_list", lang)
    buttons = []
    for u in users[:20]:
        icon = status_icons.get(u["status"], "❔")
        specs = json.loads(u["specs"])
        text += f"{icon} *{esc_md(u['full_name'])}* | {esc_md(u['class_name'])}\n    🎯 {esc_md(', '.join(specs))}\n    📅 {u['registered_at']}\n\n"
        buttons.append([InlineKeyboardButton(f"⚙️ {u['full_name'][:25]}", callback_data=f"adm_user_view_{u['telegram_id']}")])
    buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_users")])
    if len(text) > 4000:
        text = text[:4000] + "\n\n_...truncated_"
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def _handle_user_action(query, data, lang) -> None:
    parts = data.split("_")
    action = parts[2]
    uid = int(parts[3])

    if action == "view":
        user = get_user(uid)
        if not user:
            await query.message.edit_text(t("adm_user_not_found", lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_users")]]))
            return
        specs = json.loads(user["specs"])
        status_icons = {"pending": "⏳", "active": "✅", "inactive": "❌"}
        status_label = t(f"status_{user['status']}", lang)
        text = t("adm_user_card", lang,
                 full_name=esc_md(user["full_name"]), class_name=esc_md(user["class_name"]),
                 specs=esc_md(", ".join(specs)), software=esc_md(user["software"] or "—"),
                 registered_at=user["registered_at"], status=f"{status_icons.get(user['status'],'')} {status_label}",
                 username=esc_md(user["username"] or "—"), uid=uid)
        buttons = []
        if user["status"] != "active":
            buttons.append([InlineKeyboardButton(t("adm_user_activate_btn", lang), callback_data=f"adm_user_activate_{uid}")])
        if user["status"] != "inactive":
            buttons.append([InlineKeyboardButton(t("adm_user_deactivate_btn", lang), callback_data=f"adm_user_deactivate_{uid}")])
        if user["status"] == "pending":
            buttons.append([InlineKeyboardButton(t("adm_user_delete_btn", lang), callback_data=f"adm_user_delete_{uid}")])
        buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_users")])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if action == "activate":
        set_user_status(uid, "active")
        from database import get_user_lang
        u_lang = get_user_lang(uid) or DEFAULT_LANG
        try:
            await query.get_bot().send_message(chat_id=uid, text=t("adm_user_activated_notify", u_lang), parse_mode="Markdown")
        except Exception as e:
            logger.warning("Notify user %s error: %s", uid, e)
        await query.answer(t("adm_user_activated", lang), show_alert=True)
        await _handle_user_action(query, f"adm_user_view_{uid}", lang)
        return

    if action == "deactivate":
        set_user_status(uid, "inactive")
        from database import get_user_lang
        u_lang = get_user_lang(uid) or DEFAULT_LANG
        try:
            await query.get_bot().send_message(chat_id=uid, text=t("adm_user_deactivated_notify", u_lang), parse_mode="Markdown")
        except Exception as e:
            logger.warning("Notify user %s error: %s", uid, e)
        await query.answer(t("adm_user_deactivated", lang), show_alert=True)
        await _handle_user_action(query, f"adm_user_view_{uid}", lang)
        return

    if action == "delete":
        user = get_user(uid)
        name = user["full_name"] if user else str(uid)
        from database import get_user_lang
        u_lang = get_user_lang(uid) or DEFAULT_LANG
        delete_user(uid)
        try:
            await query.get_bot().send_message(chat_id=uid, text=t("adm_user_deleted_notify", u_lang))
        except Exception as e:
            logger.warning("Notify user %s error: %s", uid, e)
        await query.message.edit_text(
            t("adm_user_deleted", lang, name=esc_md(name)), parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_users")]]))
        return


# ---- Submissions ----

async def _show_subs_menu(query, lang) -> None:
    sc = get_submissions_count()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("adm_subs_new", lang, count=sc["new"]), callback_data="adm_subs_new")],
        [InlineKeyboardButton(t("adm_subs_approved", lang, count=sc["approved"]), callback_data="adm_subs_approved")],
        [InlineKeyboardButton(t("adm_subs_rejected", lang, count=sc["rejected"]), callback_data="adm_subs_rejected")],
        [InlineKeyboardButton(t("adm_subs_all", lang, count=sc["total"]), callback_data="adm_subs_all")],
        [InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_back")],
    ])
    await query.message.edit_text(t("adm_subs_title", lang), parse_mode="Markdown", reply_markup=kb)


async def _handle_subs_list(query, data, lang) -> None:
    status_map = {"adm_subs_new": "new", "adm_subs_approved": "approved",
                  "adm_subs_rejected": "rejected", "adm_subs_all": None}
    status = status_map.get(data)
    subs = get_all_submissions(status=status)
    if not subs:
        await query.message.edit_text(t("adm_subs_empty", lang),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_subs")]]))
        return

    status_icons = {"new": "🆕", "approved": "✅", "rejected": "❌"}
    text = t("adm_subs_list", lang)
    buttons = []
    for s in subs[:15]:
        icon = status_icons.get(s["status"], "❔")
        text += f"{icon} *#{s['id']}* — {esc_md(s['content_type'])}\n    👤 {esc_md(s['submitter_name'])} | 📍 {esc_md(s['location'])}\n    📅 {s['submitted_at']}\n\n"
        buttons.append([InlineKeyboardButton(f"👁 #{s['id']}", callback_data=f"adm_sub_view_{s['id']}")])
    buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_subs")])
    if len(text) > 4000:
        text = text[:4000] + "\n\n_...truncated_"
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def _handle_sub_action(query, data, context, lang) -> None:
    parts = data.split("_")
    action = parts[2]
    sub_id = int(parts[3])

    if action == "view":
        sub = get_submission(sub_id)
        if not sub:
            await query.message.edit_text(t("adm_sub_not_found", lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_subs")]]))
            return
        status_labels = {"new": "🆕", "approved": "✅", "rejected": "❌"}
        file_info = f"{'Есть (' + sub['file_type'] + ')' if sub['file_id'] else 'Нет (текст)'}"
        text = t("adm_sub_card", lang, sub_id=sub["id"], submitter=esc_md(sub["submitter_name"]),
                 ctype=esc_md(sub["content_type"]), location=esc_md(sub["location"]),
                 description=esc_md(sub["description"]),
                 file_info=file_info, date=sub["submitted_at"],
                 status=f"{status_labels.get(sub['status'],'')} {sub['status']}")
        buttons = []
        if sub["file_id"]:
            buttons.append([InlineKeyboardButton(t("adm_sub_show_file", lang), callback_data=f"adm_sub_file_{sub_id}")])
        if sub["status"] != "approved":
            buttons.append([InlineKeyboardButton(t("adm_sub_approve_btn", lang), callback_data=f"adm_sub_approve_{sub_id}")])
        if sub["status"] != "rejected":
            buttons.append([InlineKeyboardButton(t("adm_sub_reject_btn", lang), callback_data=f"adm_sub_reject_{sub_id}")])
        buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_subs")])
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        return

    if action == "file":
        sub = get_submission(sub_id)
        if not sub or not sub["file_id"]:
            await query.answer(t("adm_sub_file_not_found", lang), show_alert=True)
            return
        bot = query.get_bot()
        try:
            cap = f"📥 #{sub_id} — {sub['submitter_name']}"
            if sub["file_type"] == "photo":
                await bot.send_photo(chat_id=query.from_user.id, photo=sub["file_id"], caption=cap)
            elif sub["file_type"] == "video":
                await bot.send_video(chat_id=query.from_user.id, video=sub["file_id"], caption=cap)
            else:
                await bot.send_document(chat_id=query.from_user.id, document=sub["file_id"], caption=cap)
        except Exception as e:
            logger.warning("File send error: %s", e)
            await query.answer(t("adm_sub_file_error", lang), show_alert=True)
        return

    if action == "approve":
        sub = get_submission(sub_id)
        set_submission_status(sub_id, "approved")
        if sub:
            from database import get_user_lang
            u_lang = get_user_lang(sub["telegram_id"]) or DEFAULT_LANG
            try:
                await query.get_bot().send_message(chat_id=sub["telegram_id"],
                    text=t("adm_sub_approved_notify", u_lang, sub_id=sub_id,
                           ctype=sub["content_type"], location=sub["location"]),
                    parse_mode="Markdown")
            except Exception as e:
                logger.warning("Notify submission author error: %s", e)
        await query.answer(t("adm_sub_approved", lang), show_alert=True)
        await _handle_sub_action(query, f"adm_sub_view_{sub_id}", context, lang)
        return

    if action == "reject":
        sub = get_submission(sub_id)
        set_submission_status(sub_id, "rejected")
        if sub:
            from database import get_user_lang
            u_lang = get_user_lang(sub["telegram_id"]) or DEFAULT_LANG
            try:
                await query.get_bot().send_message(chat_id=sub["telegram_id"],
                    text=t("adm_sub_rejected_notify", u_lang, sub_id=sub_id,
                           ctype=sub["content_type"], location=sub["location"]),
                    parse_mode="Markdown")
            except Exception as e:
                logger.warning("Notify submission author error: %s", e)
        await query.answer(t("adm_sub_rejected", lang), show_alert=True)
        await _handle_sub_action(query, f"adm_sub_view_{sub_id}", context, lang)
        return


# ---- Events ----

async def _show_events_admin(query, lang) -> None:
    events = get_upcoming_events()
    if not events:
        await query.message.edit_text(t("adm_events_empty", lang),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("adm_event_create_btn", lang), callback_data="adm_event_add")],
                [InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_back")],
            ]))
        return

    text = t("adm_events_title", lang)
    buttons = []
    for ev in events:
        signups = get_event_signups(ev["id"])
        text += t("adm_event_row", lang, title=esc_md(ev["title"]), date=ev["date_str"],
                  time=ev["time_str"] or "—", location=esc_md(ev["location"]), signups=len(signups))
        buttons.append([
            InlineKeyboardButton(f"👁 {ev['title'][:25]}", callback_data=f"adm_ev_view_{ev['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"adm_ev_del_{ev['id']}"),
        ])
    buttons.append([InlineKeyboardButton(t("adm_event_add_btn", lang), callback_data="adm_event_add")])
    buttons.append([InlineKeyboardButton(t("adm_back_short", lang), callback_data="adm_back")])
    if len(text) > 4000:
        text = text[:4000] + "\n\n_...truncated_"
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def _handle_event_action(query, data, lang) -> None:
    parts = data.split("_")
    action = parts[2]
    ev_id = int(parts[3])

    if action == "view":
        ev = get_event(ev_id)
        if not ev:
            await query.answer(t("sched_event_not_found", lang), show_alert=True)
            return
        signups = get_event_signups(ev_id)
        text = t("adm_event_view", lang, title=esc_md(ev["title"]), date=ev["date_str"],
                 time=ev["time_str"] or "—", location=esc_md(ev["location"]),
                 description=esc_md(ev["description"] or "—"))
        if signups:
            text += t("adm_event_signups", lang, count=len(signups))
            for s in signups:
                text += f"  • {esc_md(s['full_name'])} ({esc_md(s['class_name'])}) — @{esc_md(s['username'] or '—')}\n"
        else:
            text += t("adm_event_no_signups", lang)
        await query.message.edit_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("adm_event_delete_btn", lang), callback_data=f"adm_ev_del_{ev_id}")],
                [InlineKeyboardButton(t("adm_event_back", lang), callback_data="adm_events")],
            ]))
        return

    if action == "del":
        ev = get_event(ev_id)
        title = ev["title"] if ev else f"#{ev_id}"
        delete_event(ev_id)
        await query.answer(t("adm_event_deleted", lang, title=title), show_alert=True)
        await _show_events_admin(query, lang)
        return


# ---- Event creation ConversationHandler ----

async def event_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer(t("adm_no_access_short", "ru"), show_alert=True)
        return ConversationHandler.END
    await query.answer()
    lang = await get_lang(update, context)
    context.user_data["adm_event"] = {}
    await query.message.reply_text(t("adm_event_add_title", lang), parse_mode="Markdown")
    return ADM_EVENT_TITLE


async def event_got_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    title = update.message.text.strip()
    context.user_data["adm_event"]["title"] = title
    await update.message.reply_text(t("adm_event_step2", lang, title=esc_md(title)), parse_mode="Markdown")
    return ADM_EVENT_DATE


async def event_got_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    date_str = update.message.text.strip()
    parts = date_str.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        await update.message.reply_text(t("adm_event_date_invalid", lang))
        return ADM_EVENT_DATE
    context.user_data["adm_event"]["date"] = date_str
    await update.message.reply_text(t("adm_event_step3", lang, date=date_str), parse_mode="Markdown")
    return ADM_EVENT_TIME


async def event_got_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    time_str = update.message.text.strip()
    context.user_data["adm_event"]["time"] = time_str if time_str != "—" else None
    await update.message.reply_text(t("adm_event_step4", lang, time=esc_md(time_str)), parse_mode="Markdown")
    return ADM_EVENT_LOCATION


async def event_got_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    location = update.message.text.strip()
    context.user_data["adm_event"]["location"] = location
    await update.message.reply_text(t("adm_event_step5", lang, location=esc_md(location)), parse_mode="Markdown")
    return ADM_EVENT_DESC


async def event_got_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    desc = update.message.text.strip()
    ev = context.user_data["adm_event"]

    event_id = add_event(
        title=ev["title"], date_str=ev["date"], time_str=ev.get("time"),
        location=ev["location"], description=desc, created_by=update.effective_user.id,
    )

    ev["description"] = desc
    ev["id"] = event_id

    count = len(get_active_user_ids())
    await update.message.reply_text(
        t("adm_event_created", lang, event_id=event_id, title=esc_md(ev["title"]),
          date=ev["date"], time=ev.get("time") or "\u2014",
          location=esc_md(ev["location"]), description=esc_md(desc)),
        parse_mode="Markdown",
    )
    await update.message.reply_text(
        t("adm_event_notify_prompt", lang, count=count),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t("adm_event_notify_yes", lang), callback_data="adm_evnotify_yes")],
            [InlineKeyboardButton(t("adm_event_notify_no", lang), callback_data="adm_evnotify_no")],
        ]),
    )
    return ADM_EVENT_NOTIFY_CONFIRM


async def event_notify_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)
    ev = context.user_data.get("adm_event", {})

    if query.data == "adm_evnotify_no":
        await query.message.edit_text(t("adm_event_notify_skipped", lang))
        context.user_data.pop("adm_event", None)
        return ConversationHandler.END

    # Send notification to all users
    from handlers.schedule import notify_new_event
    await notify_new_event(context, ev)

    user_ids = get_active_user_ids()
    await query.message.edit_text(
        t("adm_event_notify_done", lang, count=len(user_ids)),
        parse_mode="Markdown",
    )
    context.user_data.pop("adm_event", None)
    return ConversationHandler.END


# ---- Broadcast ConversationHandler ----

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer(t("adm_no_access_short", "ru"), show_alert=True)
        return ConversationHandler.END
    await query.answer()
    lang = await get_lang(update, context)
    user_ids = get_active_user_ids()
    context.user_data["adm_broadcast_count"] = len(user_ids)
    await query.message.reply_text(t("adm_broadcast_title", lang, count=len(user_ids)), parse_mode="Markdown")
    return ADM_BROADCAST_TEXT


async def broadcast_got_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    text = update.message.text.strip()
    context.user_data["adm_broadcast_text"] = text
    count = context.user_data.get("adm_broadcast_count", 0)
    await update.message.reply_text(
        t("adm_broadcast_preview", lang, text=esc_md(text), count=count),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(t("adm_broadcast_send_btn", lang), callback_data="adm_bcast_yes"),
            InlineKeyboardButton(t("adm_broadcast_cancel_btn", lang), callback_data="adm_bcast_no"),
        ]]),
    )
    return ADM_BROADCAST_CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)

    if query.data == "adm_bcast_no":
        await query.message.edit_text(t("adm_broadcast_cancelled", lang))
        context.user_data.pop("adm_broadcast_text", None)
        context.user_data.pop("adm_broadcast_count", None)
        return ConversationHandler.END

    bcast_text = context.user_data.get("adm_broadcast_text", "")
    user_ids = get_active_user_ids()
    bot = query.get_bot()

    async def _send(uid):
        try:
            from database import get_user_lang
            u_lang = get_user_lang(uid) or DEFAULT_LANG
            await bot.send_message(chat_id=uid,
                text=t("notify_broadcast", u_lang, text=esc_md(bcast_text)), parse_mode="Markdown")
            return True
        except Exception:
            return False

    results = await asyncio.gather(*[_send(uid) for uid in user_ids])
    sent = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)

    await query.message.edit_text(
        t("adm_broadcast_done", lang, sent=sent, failed=failed), parse_mode="Markdown",
    )
    context.user_data.pop("adm_broadcast_text", None)
    context.user_data.pop("adm_broadcast_count", None)
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = await get_lang(update, context)
    context.user_data.pop("adm_event", None)
    context.user_data.pop("adm_broadcast_text", None)
    context.user_data.pop("adm_broadcast_count", None)
    await update.message.reply_text(t("adm_action_cancelled", lang))
    return ConversationHandler.END


# ---- ConversationHandlers ----

event_add_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(event_add_start, pattern="^adm_event_add$")],
    states={
        ADM_EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_title)],
        ADM_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_date)],
        ADM_EVENT_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_time)],
        ADM_EVENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_location)],
        ADM_EVENT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, event_got_desc)],
        ADM_EVENT_NOTIFY_CONFIRM: [CallbackQueryHandler(event_notify_confirm, pattern="^adm_evnotify_")],
    },
    fallbacks=[CommandHandler("cancel", admin_cancel)],
    allow_reentry=True,
    per_message=False,
    conversation_timeout=600,
)

broadcast_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(broadcast_start, pattern="^adm_broadcast$")],
    states={
        ADM_BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_got_text)],
        ADM_BROADCAST_CONFIRM: [CallbackQueryHandler(broadcast_confirm, pattern="^adm_bcast_")],
    },
    fallbacks=[CommandHandler("cancel", admin_cancel)],
    allow_reentry=True,
    per_message=False,
    conversation_timeout=600,
)
