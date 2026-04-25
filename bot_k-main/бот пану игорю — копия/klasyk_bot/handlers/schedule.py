"""
Schedule handler — event list + sign-up, with i18n.
"""
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from config import ADMIN_GROUP_ID, ADMIN_IDS
from database import get_upcoming_events, get_event, signup_for_event, get_user, get_all_users
from handlers.main_menu import ensure_registered_or_reject
from i18n import t, get_lang, DEFAULT_LANG, esc_md

logger = logging.getLogger(__name__)


async def show_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_registered_or_reject(update, context):
        return
    lang = await get_lang(update, context)
    events = get_upcoming_events()
    if not events:
        await update.message.reply_text(t("sched_empty", lang))
        return

    user_id = update.effective_user.id
    is_admin_user = user_id in ADMIN_IDS
    text = t("sched_title", lang)
    buttons = []
    for ev in events:
        text += t("sched_event_row", lang,
                  title=esc_md(ev["title"]), date=ev["date_str"],
                  time=ev["time_str"] or "—",
                  location=esc_md(ev["location"]),
                  description=esc_md(ev["description"] or ""))
        if not is_admin_user:
            buttons.append([InlineKeyboardButton(
                t("sched_signup_btn", lang, title=ev["title"][:30]),
                callback_data=f"schedule_signup_{ev['id']}"
            )])
    buttons.append([InlineKeyboardButton(t("sched_refresh_btn", lang), callback_data="schedule_refresh")])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_registered_or_reject(update, context):
        await update.callback_query.answer()
        return
    query = update.callback_query
    data = query.data
    lang = await get_lang(update, context)

    if data == "schedule_refresh":
        await query.answer()
        events = get_upcoming_events()
        user_id = update.effective_user.id
        is_admin_user = user_id in ADMIN_IDS
        text = t("sched_refresh_title", lang)
        buttons = []
        if events:
            for ev in events:
                text += t("sched_event_row_short", lang,
                          title=esc_md(ev["title"]), date=ev["date_str"],
                          time=ev["time_str"] or "",
                          description=esc_md(ev["description"] or ""),
                          location=esc_md(ev["location"]))
                if not is_admin_user:
                    buttons.append([InlineKeyboardButton(
                        t("sched_signup_btn", lang, title=ev["title"][:30]),
                        callback_data=f"schedule_signup_{ev['id']}"
                    )])
        else:
            text += t("sched_empty", lang) + "\n"
        buttons.append([InlineKeyboardButton(t("sched_refresh_btn", lang), callback_data="schedule_refresh")])
        try:
            await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        except BadRequest as e:
            if "Message is not modified" in str(e):
                return
            raise
        return

    if data.startswith("schedule_signup_"):
        event_id = int(data.replace("schedule_signup_", ""))
        user = update.effective_user

        if user.id in ADMIN_IDS:
            await query.answer(t("sched_admin_no_signup", lang), show_alert=True)
            return

        db_user = get_user(user.id)
        name = db_user["full_name"] if db_user else (user.full_name or str(user.id))
        cls = db_user["class_name"] if db_user else "—"

        ev = get_event(event_id)
        if not ev:
            await query.answer(t("sched_event_not_found", lang), show_alert=True)
            return

        already = not signup_for_event(user.id, event_id)
        if already:
            await query.answer(t("sched_already_signed", lang, title=ev["title"]), show_alert=True)
            return

        notify = t("notify_signup", "ru",
                    name=esc_md(name), cls=esc_md(cls), title=esc_md(ev["title"]),
                    date=ev["date_str"], location=esc_md(ev["location"]),
                    username=esc_md(user.username or "—"), uid=user.id)
        try:
            await query.get_bot().send_message(chat_id=ADMIN_GROUP_ID, text=notify, parse_mode="Markdown")
        except Exception as e:
            logger.warning("Signup notify error: %s", e)
        for admin_id in ADMIN_IDS:
            try:
                await query.get_bot().send_message(chat_id=admin_id, text=notify, parse_mode="Markdown")
            except Exception as e:
                logger.warning("Signup notify admin %s error: %s", admin_id, e)

        await query.answer(t("sched_signup_success", lang, title=ev["title"]), show_alert=True)
        await query.message.reply_text(
            t("sched_signup_confirm", lang, title=esc_md(ev["title"]), date=ev["date_str"], location=esc_md(ev["location"])),
            parse_mode="Markdown",
        )


async def notify_new_event(context, event):
    bot = context.bot
    users = get_all_users()
    non_admin = [u for u in users if u["telegram_id"] not in ADMIN_IDS]

    async def _send(uid):
        try:
            from database import get_user_lang
            u_lang = get_user_lang(uid) or DEFAULT_LANG
            await bot.send_message(
                chat_id=uid,
                text=t("notify_new_event", u_lang,
                       title=esc_md(event["title"]),
                       date=event.get("date") or event.get("date_str", ""),
                       time=event.get("time") or event.get("time_str") or "—",
                       location=esc_md(event["location"]),
                       description=esc_md(event.get("description") or "")),
                parse_mode="Markdown",
            )
        except Exception:
            pass

    await asyncio.gather(*[_send(u["telegram_id"]) for u in non_admin])
