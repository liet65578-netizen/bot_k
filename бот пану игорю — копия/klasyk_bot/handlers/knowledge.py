"""
Раздел «📚 База знаний» — шпаргалки, туториалы, чек-листы
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import KNOWLEDGE_ITEMS


def _knowledge_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"{item['icon']} {item['title']}", callback_data=f"kb_{item['id']}")]
        for item in KNOWLEDGE_ITEMS
    ]
    return InlineKeyboardMarkup(buttons)


async def show_knowledge_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📚 *База знаний Klasyk TV*\n\n"
        "Выбери раздел:",
        parse_mode="Markdown",
        reply_markup=_knowledge_menu_keyboard(),
    )


async def knowledge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data  # kb_<id> или kb_back

    if data == "kb_back":
        await query.message.edit_text(
            "📚 *База знаний Klasyk TV*\n\nВыбери раздел:",
            parse_mode="Markdown",
            reply_markup=_knowledge_menu_keyboard(),
        )
        return

    item_id = data.replace("kb_", "")
    item = next((i for i in KNOWLEDGE_ITEMS if i["id"] == item_id), None)

    if not item:
        await query.answer("Раздел не найден", show_alert=True)
        return

    await query.message.edit_text(
        item["text"],
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад к базе знаний", callback_data="kb_back")]
        ]),
        disable_web_page_preview=True,
    )
