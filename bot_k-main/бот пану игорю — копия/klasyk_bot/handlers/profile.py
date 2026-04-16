"""
Profile handler with i18n.
"""
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_user, get_user_signups
from handlers.main_menu import get_main_keyboard, ensure_registered_or_reject
from i18n import t, get_lang


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_registered_or_reject(update, context):
        return
    lang = await get_lang(update, context)
    user_id = update.effective_user.id
    row = get_user(user_id)

    if not row:
        await update.message.reply_text(
            t("profile_not_found", lang),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(user_id, lang),
        )
        return

    specs = json.loads(row["specs"])
    signups = get_user_signups(user_id)
    status = t(f"status_{row['status']}", lang)

    signup_text = ""
    if signups:
        signup_text = t("profile_signups", lang)
        for ev in signups:
            signup_text += f"• {ev['title']} — {ev['date_str']}\n"

    text = t("profile_title", lang) + t("profile_info", lang,
        full_name=row["full_name"],
        class_name=row["class_name"],
        specs=", ".join(specs),
        software=row["software"] or "—",
        registered_at=row["registered_at"],
        status=status,
    ) + signup_text

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t("profile_edit_btn", lang), callback_data="profile_edit")]
        ]),
    )


async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    lang = await get_lang(update, context)

    if query.data == "profile_edit":
        await query.message.reply_text(
            t("profile_edit_instruction", lang),
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(update.effective_user.id, lang),
        )
