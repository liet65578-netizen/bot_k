"""
i18n — Internationalization module for Klasyk Media Hub Bot.
Supports: Russian (ru), Polish (pl), English (en), Ukrainian (uk).
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "pl": "🇵🇱 Polski",
    "en": "🇬🇧 English",
    "uk": "🇺🇦 Українська",
}

DEFAULT_LANG = "ru"

# ══════════════════════════════════════════════════════════════════════════════
# ALL TRANSLATIONS — organised by section
# Keys are flat strings. Values can use {placeholders} for .format().
# ══════════════════════════════════════════════════════════════════════════════

_TEXTS: dict[str, dict[str, str]] = {}

# ─── RUSSIAN ─────────────────────────────────────────────────────────────────
_TEXTS["ru"] = {
    # ── Menu buttons (ReplyKeyboard) ──
    "menu_team": "🎥 Хочу в команду!",
    "menu_content": "📥 Предложить контент",
    "menu_schedule": "📅 План съёмок",
    "menu_knowledge": "📚 База знаний",
    "menu_profile": "👤 Мой профиль",
    "menu_admin": "🔧 Админ-панель",
    "menu_lang": "🌐 Язык",
    "menu_placeholder": "Выбери раздел 👇",

    # ── Language selection ──
    "lang_choose": "🌐 *Выберите язык / Choose language:*",
    "lang_changed": "✅ Язык изменён: *{lang_name}*",

    # ── General ──
    "welcome": (
        "👋 *Привет! Добро пожаловать в Klasyk Media Hub!*\n\n"
        "Я помогаю нашей школьной редакции собирать контент, "
        "регистрировать участников и планировать съёмки.\n\n"
        "Выбери нужный раздел в меню ниже 👇"
    ),
    "main_menu": "📋 *Главное меню*\n\nВыбери раздел:",
    "cancel": "❌ Действие отменено. Возвращаемся в главное меню.",
    "use_buttons": "Используй кнопки меню 👇",
    "back_to_menu": "Возвращаемся в главное меню 👇",
    "access_denied": (
        "⛔ Сначала зарегистрируйся в команде.\n\n"
        "Нажми «🎥 Хочу в команду!» и заполни анкету."
    ),
    "admin_profile_text": "👤 *Ваш профиль*\n\nВы — администратор. Всё работает 👍",
    "error_generic": "⚠️ Произошла ошибка. Попробуйте позже.",

    # ── Registration ──
    "reg_already": (
        "✅ *Ты уже в нашей команде!*\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n\n"
        "Чтобы обновить данные — пройди анкету снова."
    ),
    "reg_update_btn": "🔄 Обновить анкету",
    "reg_welcome": (
        "🎥 *Добро пожаловать в команду Klasyk TV!*\n\n"
        "Заполним небольшую анкету — это займёт 1-2 минуты.\n\n"
        "📝 *Шаг 1/4* — Напиши своё *ФИО* (Фамилия Имя Отчество):"
    ),
    "reg_step1": "📝 *Шаг 1/4* — Напиши своё *ФИО*:",
    "reg_name_short": "⚠️ Пожалуйста, введи полное ФИО (минимум Фамилия и Имя):",
    "reg_name_ok": "👍 Записал: *{name}*\n\n📝 *Шаг 2/4* — Выбери свой *класс*:",
    "reg_class_ok": (
        "👍 Класс: *{cls}*\n\n"
        "📝 *Шаг 3/4* — Выбери *специализацию(и)*.\n"
        "Можно выбрать несколько! Нажми ✅ Готово когда закончишь.\n"
        "Если нужной нет — нажми ✍️ Другое."
    ),
    "reg_spec_empty": "⚠️ Выбери хотя бы одну специализацию!",
    "reg_spec_other_btn": "✍️ Другое",
    "reg_spec_done_btn": "✅ Готово",
    "reg_spec_other_prompt": "✍️ Напиши свою специализацию:",
    "reg_spec_other_added": "✅ Добавлено: *{spec}*\nМожешь выбрать ещё или нажми ✅ Готово.",
    "reg_spec_ok": (
        "👍 Специализации: *{specs}*\n\n"
        "📝 *Шаг 4/4* — Какими *программами* ты владеешь?\n"
        "_(CapCut, VN, Premiere, Photoshop, Canva и т.д. — пиши в свободной форме)_"
    ),
    "reg_confirm_summary": (
        "📋 *Проверь свою анкету:*\n\n"
        "👤 ФИО: *{full_name}*\n"
        "🏫 Класс: *{class_name}*\n"
        "🎯 Специализация: *{specs}*\n"
        "💻 Программы: *{software}*\n\n"
        "Всё верно?"
    ),
    "reg_confirm_yes": "✅ Всё верно!",
    "reg_confirm_no": "✏️ Исправить",
    "reg_restart_text": "🔄 Начнём заново!\n\n📝 *Шаг 1/4* — Напиши своё *ФИО*:",
    "reg_success": (
        "🎉 *Поздравляем, {name}!*\n\n"
        "Ты успешно зарегистрирован(а) в команде *Klasyk TV*!\n\n"
        "Мы скоро свяжемся с тобой. Следи за обновлениями в боте 🚀"
    ),

    # ── Content submission ──
    "con_start": (
        "📥 *Предложить контент*\n\n"
        "Отлично! Давай загрузим материал.\n\n"
        "📌 *Шаг 1/4* — Выбери *тип контента*:"
    ),
    "con_type_text": (
        "✅ Тип: *{ctype}*\n\n"
        "📌 *Шаг 2/4* — Напиши текст своей новости или идеи.\n"
        "_Можно несколько абзацев — пиши как хочется!_"
    ),
    "con_type_file": (
        "✅ Тип: *{ctype}*\n\n"
        "📌 *Шаг 2/4* — Загрузи файл.\n\n"
        "📎 *Отправь как документ* (скрепка) — без потери качества\n"
        "или обычным сообщением — быстрее, но сжатое"
    ),
    "con_file_doc": "📎 Файл получен (документ, без потери качества)",
    "con_file_photo": "📷 Фото получено",
    "con_file_video": "🎬 Видео получено",
    "con_file_text": "📝 Текст получен",
    "con_file_invalid": "⚠️ Пришли фото, видео, документ или текст новости.",
    "con_step3": (
        "✅ {label}\n\n"
        "📌 *Шаг 3/4* — Напиши *описание*:\n"
        "Что происходит? Кто в кадре? Какое событие?\n"
        "_Чем подробнее — тем лучше!_"
    ),
    "con_desc_short": "⚠️ Пожалуйста, опиши подробнее — хотя бы несколько слов.",
    "con_step4": "✅ Описание записано!\n\n📌 *Шаг 4/4* — Укажи *место / событие*:",
    "con_success": (
        "🎉 *Спасибо! Материал отправлен в редакцию.*\n\n"
        "📋 Заявка #{sub_id}\n"
        "📌 {ctype} | 📍 {location}\n\n"
        "Редакторы рассмотрят и свяжутся с тобой, если потребуется что-то уточнить."
    ),
    "con_back_menu": "Возвращаемся в меню 👇",

    # ── Schedule ──
    "sched_title": "📅 *Ближайшие события — план съёмок:*\n\n",
    "sched_empty": "📅 Пока нет запланированных событий. Загляни позже!",
    "sched_signup_btn": "📋 Записаться: {title}",
    "sched_refresh_btn": "🔄 Обновить список",
    "sched_refresh_title": "📅 *Актуальный план съёмок:*\n\n",
    "sched_event_row": (
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
    ),
    "sched_event_row_short": (
        "*{title}* — {date} {time}\n"
        "💬 {description}\n"
        "📍 {location}\n\n"
    ),
    "sched_signup_success": "🎉 Записал тебя на «{title}»!",
    "sched_already_signed": "✅ Ты уже записан(а) на: {title}",
    "sched_event_not_found": "⚠️ Событие не найдено",
    "sched_admin_no_signup": "Ты админ — управляй процессом, а не записывайся 🙂",
    "sched_signup_confirm": (
        "✅ *Готово!* Ты записан(а) на:\n"
        "*{title}*\n"
        "📆 {date}  📍 {location}\n\n"
        "Мы напомним ближе к дате 🔔"
    ),

    # ── Knowledge base ──
    "kb_title": "📚 *База знаний Klasyk TV*\n\nВыбери раздел:",
    "kb_back": "◀️ Назад к базе знаний",
    "kb_not_found": "Раздел не найден",

    # ── Profile ──
    "profile_title": "👤 *Мой профиль*\n\n",
    "profile_not_found": (
        "👤 *Профиль не найден*\n\n"
        "Ты ещё не зарегистрирован(а) в команде.\n"
        "Нажми *«🎥 Хочу в команду!»* чтобы заполнить анкету."
    ),
    "profile_info": (
        "📛 *{full_name}*\n"
        "🏫 Класс: {class_name}\n"
        "🎯 Специализация: {specs}\n"
        "💻 Программы: {software}\n"
        "📅 В команде с: {registered_at}\n"
        "🔖 Статус: {status}"
    ),
    "profile_edit_btn": "✏️ Обновить анкету",
    "profile_edit_instruction": (
        "✏️ Чтобы обновить данные — нажми *«🎥 Хочу в команду!»* в меню.\n"
        "Анкета перезапишется."
    ),
    "profile_signups": "\n\n📋 *Мои записи на съёмку:*\n",
    "status_pending": "⏳ На рассмотрении",
    "status_active": "✅ Активный участник",
    "status_inactive": "❌ Неактивный",

    # ── Admin panel ──
    "adm_no_access": "⛔ У тебя нет доступа к панели администратора.",
    "adm_no_access_short": "⛔ Нет доступа",
    "adm_updated": "🔄 Обновил админ-меню.",
    "adm_title": "🔧 *Панель администратора*\n\nВыбери раздел:",
    "adm_stats_btn": "📊 Статистика",
    "adm_users_btn": "👥 Пользователи",
    "adm_subs_btn": "📥 Заявки",
    "adm_events_btn": "📅 События",
    "adm_event_add_btn": "➕ Новое событие",
    "adm_broadcast_btn": "📢 Рассылка",
    "adm_edit_kb_btn": "📝 Редактировать базу знаний",
    "adm_back_btn": "◀️ Назад в админ-панель",
    "adm_back_short": "◀️ Назад",
    "adm_stats": (
        "📊 *Статистика Klasyk Media Hub*\n\n"
        "👥 *Пользователи:*\n"
        "  Всего: {total}\n"
        "  ✅ Активные: {active}\n"
        "  ⏳ На рассмотрении: {pending}\n"
        "  ❌ Неактивные: {inactive}\n\n"
        "📥 *Контент-заявки:*\n"
        "  Всего: {sub_total}\n"
        "  🆕 Новые: {sub_new}\n"
        "  ✅ Одобрено: {sub_approved}\n"
        "  ❌ Отклонено: {sub_rejected}\n\n"
        "📅 Событий: {events}\n"
        "📋 Записей на съёмки: {signups}"
    ),
    "adm_users_title": "👥 *Управление пользователями*\n\nВыбери категорию:",
    "adm_users_all": "📋 Все ({count})",
    "adm_users_pending": "⏳ Ожидающие ({count})",
    "adm_users_active": "✅ Активные ({count})",
    "adm_users_inactive": "❌ Неактивные ({count})",
    "adm_users_empty": "👥 Нет пользователей в этой категории.",
    "adm_users_list": "👥 *Список пользователей:*\n\n",
    "adm_user_not_found": "⚠️ Пользователь не найден.",
    "adm_user_card": (
        "👤 *Карточка участника*\n\n"
        "📛 *{full_name}*\n"
        "🏫 Класс: {class_name}\n"
        "🎯 Специализация: {specs}\n"
        "💻 ПО: {software}\n"
        "📅 Зарегистрирован: {registered_at}\n"
        "🔖 Статус: {status}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "adm_user_activate_btn": "✅ Активировать",
    "adm_user_deactivate_btn": "❌ Деактивировать",
    "adm_user_delete_btn": "🗑 Отклонить и удалить",
    "adm_user_activated": "✅ Пользователь активирован!",
    "adm_user_activated_notify": (
        "🎉 *Отличные новости!*\n\n"
        "Твоя заявка в команду Klasyk TV одобрена! Добро пожаловать ✅"
    ),
    "adm_user_deactivated": "❌ Пользователь деактивирован",
    "adm_user_deactivated_notify": (
        "ℹ️ Твой статус в команде Klasyk TV изменён на *неактивный*.\n\n"
        "Обратись к администратору, если есть вопросы."
    ),
    "adm_user_deleted": "🗑 Пользователь *{name}* удалён.",
    "adm_user_deleted_notify": (
        "ℹ️ К сожалению, твоя заявка в команду Klasyk TV была отклонена.\n\n"
        "Ты можешь подать заявку повторно."
    ),
    "adm_subs_title": "📥 *Управление контент-заявками*\n\nВыбери категорию:",
    "adm_subs_new": "🆕 Новые ({count})",
    "adm_subs_approved": "✅ Одобренные ({count})",
    "adm_subs_rejected": "❌ Отклонённые ({count})",
    "adm_subs_all": "📋 Все ({count})",
    "adm_subs_empty": "📥 Нет заявок в этой категории.",
    "adm_subs_list": "📥 *Контент-заявки:*\n\n",
    "adm_sub_not_found": "⚠️ Заявка не найдена.",
    "adm_sub_card": (
        "📥 *Заявка #{sub_id}*\n\n"
        "👤 Автор: *{submitter}*\n"
        "📌 Тип: {ctype}\n"
        "📍 Место: {location}\n"
        "📝 Описание: {description}\n"
        "📎 Файл: {file_info}\n"
        "📅 Дата: {date}\n"
        "🔖 Статус: {status}"
    ),
    "adm_sub_show_file": "📎 Показать файл",
    "adm_sub_approve_btn": "✅ Одобрить",
    "adm_sub_reject_btn": "❌ Отклонить",
    "adm_sub_approved": "✅ Заявка одобрена!",
    "adm_sub_approved_notify": (
        "✅ *Твоя заявка #{sub_id} одобрена!*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Спасибо за вклад в Klasyk TV! 🎉"
    ),
    "adm_sub_rejected": "❌ Заявка отклонена",
    "adm_sub_rejected_notify": (
        "❌ *Заявка #{sub_id} не прошла модерацию*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Попробуй отправить снова с более качественным материалом."
    ),
    "adm_sub_file_error": "Ошибка при отправке файла",
    "adm_sub_file_not_found": "Файл не найден",
    "adm_events_title": "📅 *Управление событиями:*\n\n",
    "adm_events_empty": "📅 Нет событий.\n\nНажми ➕ чтобы создать новое.",
    "adm_event_create_btn": "➕ Создать событие",
    "adm_event_row": (
        "*{title}*\n"
        "📆 {date} 🕐 {time} | 📍 {location}\n"
        "👥 Записалось: {signups} чел.\n\n"
    ),
    "adm_event_view": (
        "📅 *{title}*\n\n"
        "📆 Дата: {date}\n"
        "🕐 Время: {time}\n"
        "📍 Место: {location}\n"
        "📝 Описание: {description}\n\n"
    ),
    "adm_event_signups": "👥 *Записалось ({count}):*\n",
    "adm_event_no_signups": "👥 Пока никто не записался.",
    "adm_event_delete_btn": "🗑 Удалить событие",
    "adm_event_deleted": "🗑 Удалено: {title}",
    "adm_event_back": "◀️ К событиям",
    "adm_event_add_title": (
        "➕ *Создание нового события*\n\n"
        "📝 *Шаг 1/5* — Напиши *название* события\n"
        "_(например: 🏆 Финал КВН)_\n\n"
        "Отмена: /cancel"
    ),
    "adm_event_step2": (
        "✅ Название: *{title}*\n\n"
        "📝 *Шаг 2/5* — Укажи *дату* (формат: ДД.ММ.ГГГГ)\n"
        "_(например: 25.04.2026)_"
    ),
    "adm_event_date_invalid": "⚠️ Неверный формат. Введи дату как ДД.ММ.ГГГГ (например: 25.04.2026):",
    "adm_event_step3": (
        "✅ Дата: *{date}*\n\n"
        "📝 *Шаг 3/5* — Укажи *время* (ЧЧ:ММ)\n"
        "_(например: 14:30, или «—» если неизвестно)_"
    ),
    "adm_event_step4": (
        "✅ Время: *{time}*\n\n"
        "📝 *Шаг 4/5* — Укажи *место*\n"
        "_(например: Актовый зал)_"
    ),
    "adm_event_step5": (
        "✅ Место: *{location}*\n\n"
        "📝 *Шаг 5/5* — Напиши *описание / что нужно*\n"
        "_(например: Нужны 2 оператора и фотограф)_"
    ),
    "adm_event_created": (
        "✅ *Событие создано!*\n\n"
        "🆔 #{event_id}\n"
        "📋 *{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "📝 {description}\n\n"
        "Оно уже видно участникам в «📅 План съёмок»!"
    ),
    "adm_broadcast_title": (
        "📢 *Рассылка*\n\n"
        "Получателей: *{count}* пользователей\n\n"
        "Напиши текст сообщения, которое получат все участники.\n"
        "Поддерживается *Markdown* форматирование.\n\n"
        "Отмена: /cancel"
    ),
    "adm_broadcast_preview": (
        "📢 *Превью рассылки:*\n\n"
        "{text}\n\n"
        "─────────────────\n"
        "Будет отправлено *{count}* пользователям.\n"
        "Подтвердить?"
    ),
    "adm_broadcast_send_btn": "✅ Отправить",
    "adm_broadcast_cancel_btn": "❌ Отмена",
    "adm_broadcast_cancelled": "❌ Рассылка отменена.",
    "adm_broadcast_done": (
        "📢 *Рассылка завершена!*\n\n"
        "✅ Доставлено: {sent}\n"
        "❌ Не доставлено: {failed}"
    ),
    "adm_action_cancelled": "❌ Действие отменено.",
    "adm_kb_edit_title": "📝 *Редактирование базы знаний*\n\nВыбери материал для редактирования:",
    "adm_kb_edit_item": (
        "📝 *Редактирование материала:*\n\n"
        "*{title}*\n\n"
        "Текущий текст:\n\n{text}\n\n"
        "✏️ *Отправьте новый текст для этого материала*:"
    ),
    "adm_kb_saved": "✅ Материал обновлён!",
    "adm_kb_not_found": "❌ Материал не найден.",

    # ── Notifications (to admin group / admins) ──
    "notify_new_member": (
        "🆕 <b>Новый участник редакции!</b>\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n"
        "💻 {software}\n"
        "🔗 @{username} | ID: <code>{uid}</code>"
    ),
    "notify_new_submission": (
        "📥 *Новая заявка #{sub_id}*\n\n"
        "👤 {submitter} (@{username})\n"
        "📌 Тип: {ctype}\n"
        "📍 Место: {location}\n"
        "📝 Описание: {description}"
    ),
    "notify_signup": (
        "📸 *Запись на съёмку!*\n\n"
        "👤 {name} из {cls}\n"
        "🎬 Хочет снимать: *{title}*\n"
        "📆 {date}  📍 {location}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "notify_new_event": (
        "🆕 Новое событие!\n\n"
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
        "Запишись в плане съёмок!"
    ),
    "notify_broadcast": "📢 *Объявление от Klasyk TV*\n\n{text}",
}

# ─── POLISH ──────────────────────────────────────────────────────────────────
_TEXTS["pl"] = {
    # ── Menu buttons ──
    "menu_team": "🎥 Dołącz do zespołu!",
    "menu_content": "📥 Zaproponuj materiał",
    "menu_schedule": "📅 Plan zdjęć",
    "menu_knowledge": "📚 Baza wiedzy",
    "menu_profile": "👤 Mój profil",
    "menu_admin": "🔧 Panel admina",
    "menu_lang": "🌐 Język",
    "menu_placeholder": "Wybierz sekcję 👇",

    # ── Language ──
    "lang_choose": "🌐 *Wybierz język / Choose language:*",
    "lang_changed": "✅ Język zmieniony: *{lang_name}*",

    # ── General ──
    "welcome": (
        "👋 *Cześć! Witamy w Klasyk Media Hub!*\n\n"
        "Pomagam naszej szkolnej redakcji zbierać materiały, "
        "rejestrować uczestników i planować zdjęcia.\n\n"
        "Wybierz sekcję w menu poniżej 👇"
    ),
    "main_menu": "📋 *Menu główne*\n\nWybierz sekcję:",
    "cancel": "❌ Działanie anulowane. Wracamy do menu głównego.",
    "use_buttons": "Użyj przycisków menu 👇",
    "back_to_menu": "Wracamy do menu głównego 👇",
    "access_denied": (
        "⛔ Najpierw zarejestruj się w zespole.\n\n"
        "Naciśnij «🎥 Dołącz do zespołu!» i wypełnij ankietę."
    ),
    "admin_profile_text": "👤 *Twój profil*\n\nJesteś administratorem. Wszystko działa 👍",
    "error_generic": "⚠️ Wystąpił błąd. Spróbuj później.",

    # ── Registration ──
    "reg_already": (
        "✅ *Jesteś już w naszym zespole!*\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n\n"
        "Aby zaktualizować dane — wypełnij ankietę ponownie."
    ),
    "reg_update_btn": "🔄 Zaktualizuj ankietę",
    "reg_welcome": (
        "🎥 *Witamy w zespole Klasyk TV!*\n\n"
        "Wypełnimy krótką ankietę — zajmie to 1-2 minuty.\n\n"
        "📝 *Krok 1/4* — Wpisz swoje *imię i nazwisko*:"
    ),
    "reg_step1": "📝 *Krok 1/4* — Wpisz swoje *imię i nazwisko*:",
    "reg_name_short": "⚠️ Proszę, wpisz pełne imię i nazwisko:",
    "reg_name_ok": "👍 Zapisano: *{name}*\n\n📝 *Krok 2/4* — Wybierz swoją *klasę*:",
    "reg_class_ok": (
        "👍 Klasa: *{cls}*\n\n"
        "📝 *Krok 3/4* — Wybierz *specjalizację(e)*.\n"
        "Możesz wybrać kilka! Naciśnij ✅ Gotowe gdy skończysz.\n"
        "Jeśli brakuje Twojej — naciśnij ✍️ Inne."
    ),
    "reg_spec_empty": "⚠️ Wybierz co najmniej jedną specjalizację!",
    "reg_spec_other_btn": "✍️ Inne",
    "reg_spec_done_btn": "✅ Gotowe",
    "reg_spec_other_prompt": "✍️ Wpisz swoją specjalizację:",
    "reg_spec_other_added": "✅ Dodano: *{spec}*\nMożesz wybrać więcej lub naciśnij ✅ Gotowe.",
    "reg_spec_ok": (
        "👍 Specjalizacje: *{specs}*\n\n"
        "📝 *Krok 4/4* — Jakie *programy* znasz?\n"
        "_(CapCut, VN, Premiere, Photoshop, Canva itp. — pisz dowolnie)_"
    ),
    "reg_confirm_summary": (
        "📋 *Sprawdź swoją ankietę:*\n\n"
        "👤 Imię i nazwisko: *{full_name}*\n"
        "🏫 Klasa: *{class_name}*\n"
        "🎯 Specjalizacja: *{specs}*\n"
        "💻 Programy: *{software}*\n\n"
        "Wszystko się zgadza?"
    ),
    "reg_confirm_yes": "✅ Wszystko OK!",
    "reg_confirm_no": "✏️ Popraw",
    "reg_restart_text": "🔄 Zaczynamy od nowa!\n\n📝 *Krok 1/4* — Wpisz swoje *imię i nazwisko*:",
    "reg_success": (
        "🎉 *Gratulacje, {name}!*\n\n"
        "Zostałeś(aś) zarejestrowany(a) w zespole *Klasyk TV*!\n\n"
        "Wkrótce się z Tobą skontaktujemy. Śledź aktualizacje w bocie 🚀"
    ),

    # ── Content submission ──
    "con_start": (
        "📥 *Zaproponuj materiał*\n\n"
        "Świetnie! Załadujmy materiał.\n\n"
        "📌 *Krok 1/4* — Wybierz *typ materiału*:"
    ),
    "con_type_text": (
        "✅ Typ: *{ctype}*\n\n"
        "📌 *Krok 2/4* — Napisz tekst swojej wiadomości lub pomysłu.\n"
        "_Można kilka akapitów — pisz jak chcesz!_"
    ),
    "con_type_file": (
        "✅ Typ: *{ctype}*\n\n"
        "📌 *Krok 2/4* — Załaduj plik.\n\n"
        "📎 *Wyślij jako dokument* (spinacz) — bez utraty jakości\n"
        "lub zwykłą wiadomością — szybciej, ale skompresowane"
    ),
    "con_file_doc": "📎 Plik otrzymany (dokument, bez utraty jakości)",
    "con_file_photo": "📷 Zdjęcie otrzymane",
    "con_file_video": "🎬 Wideo otrzymane",
    "con_file_text": "📝 Tekst otrzymany",
    "con_file_invalid": "⚠️ Wyślij zdjęcie, wideo, dokument lub tekst.",
    "con_step3": (
        "✅ {label}\n\n"
        "📌 *Krok 3/4* — Napisz *opis*:\n"
        "Co się dzieje? Kto jest w kadrze? Jakie wydarzenie?\n"
        "_Im więcej szczegółów — tym lepiej!_"
    ),
    "con_desc_short": "⚠️ Opisz bardziej szczegółowo — przynajmniej kilka słów.",
    "con_step4": "✅ Opis zapisany!\n\n📌 *Krok 4/4* — Podaj *miejsce / wydarzenie*:",
    "con_success": (
        "🎉 *Dziękujemy! Materiał wysłany do redakcji.*\n\n"
        "📋 Zgłoszenie #{sub_id}\n"
        "📌 {ctype} | 📍 {location}\n\n"
        "Redaktorzy rozpatrzą i skontaktują się, jeśli potrzebne będą wyjaśnienia."
    ),
    "con_back_menu": "Wracamy do menu 👇",

    # ── Schedule ──
    "sched_title": "📅 *Nadchodzące wydarzenia — plan zdjęć:*\n\n",
    "sched_empty": "📅 Brak zaplanowanych wydarzeń. Wróć później!",
    "sched_signup_btn": "📋 Zapisz się: {title}",
    "sched_refresh_btn": "🔄 Odśwież listę",
    "sched_refresh_title": "📅 *Aktualny plan zdjęć:*\n\n",
    "sched_event_row": (
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
    ),
    "sched_event_row_short": (
        "*{title}* — {date} {time}\n"
        "💬 {description}\n"
        "📍 {location}\n\n"
    ),
    "sched_signup_success": "🎉 Zapisałem Cię na «{title}»!",
    "sched_already_signed": "✅ Jesteś już zapisany(a) na: {title}",
    "sched_event_not_found": "⚠️ Wydarzenie nie znalezione",
    "sched_admin_no_signup": "Jesteś adminem — zarządzaj, a nie zapisuj się 🙂",
    "sched_signup_confirm": (
        "✅ *Gotowe!* Jesteś zapisany(a) na:\n"
        "*{title}*\n"
        "📆 {date}  📍 {location}\n\n"
        "Przypomnimy bliżej daty 🔔"
    ),

    # ── Knowledge base ──
    "kb_title": "📚 *Baza wiedzy Klasyk TV*\n\nWybierz sekcję:",
    "kb_back": "◀️ Powrót do bazy wiedzy",
    "kb_not_found": "Sekcja nie znaleziona",

    # ── Profile ──
    "profile_title": "👤 *Mój profil*\n\n",
    "profile_not_found": (
        "👤 *Profil nie znaleziony*\n\n"
        "Nie jesteś jeszcze zarejestrowany(a) w zespole.\n"
        "Naciśnij *«🎥 Dołącz do zespołu!»* aby wypełnić ankietę."
    ),
    "profile_info": (
        "📛 *{full_name}*\n"
        "🏫 Klasa: {class_name}\n"
        "🎯 Specjalizacja: {specs}\n"
        "💻 Programy: {software}\n"
        "📅 W zespole od: {registered_at}\n"
        "🔖 Status: {status}"
    ),
    "profile_edit_btn": "✏️ Zaktualizuj ankietę",
    "profile_edit_instruction": (
        "✏️ Aby zaktualizować dane — naciśnij *«🎥 Dołącz do zespołu!»* w menu.\n"
        "Ankieta zostanie nadpisana."
    ),
    "profile_signups": "\n\n📋 *Moje zapisy na zdjęcia:*\n",
    "status_pending": "⏳ Oczekujący",
    "status_active": "✅ Aktywny uczestnik",
    "status_inactive": "❌ Nieaktywny",

    # ── Admin panel ──
    "adm_no_access": "⛔ Nie masz dostępu do panelu administratora.",
    "adm_no_access_short": "⛔ Brak dostępu",
    "adm_updated": "🔄 Zaktualizowano menu admina.",
    "adm_title": "🔧 *Panel administratora*\n\nWybierz sekcję:",
    "adm_stats_btn": "📊 Statystyki",
    "adm_users_btn": "👥 Użytkownicy",
    "adm_subs_btn": "📥 Zgłoszenia",
    "adm_events_btn": "📅 Wydarzenia",
    "adm_event_add_btn": "➕ Nowe wydarzenie",
    "adm_broadcast_btn": "📢 Mailing",
    "adm_edit_kb_btn": "📝 Edytuj bazę wiedzy",
    "adm_back_btn": "◀️ Powrót do panelu",
    "adm_back_short": "◀️ Wstecz",
    "adm_stats": (
        "📊 *Statystyki Klasyk Media Hub*\n\n"
        "👥 *Użytkownicy:*\n"
        "  Razem: {total}\n"
        "  ✅ Aktywni: {active}\n"
        "  ⏳ Oczekujący: {pending}\n"
        "  ❌ Nieaktywni: {inactive}\n\n"
        "📥 *Zgłoszenia:*\n"
        "  Razem: {sub_total}\n"
        "  🆕 Nowe: {sub_new}\n"
        "  ✅ Zatwierdzone: {sub_approved}\n"
        "  ❌ Odrzucone: {sub_rejected}\n\n"
        "📅 Wydarzeń: {events}\n"
        "📋 Zapisów na zdjęcia: {signups}"
    ),
    "adm_users_title": "👥 *Zarządzanie użytkownikami*\n\nWybierz kategorię:",
    "adm_users_all": "📋 Wszyscy ({count})",
    "adm_users_pending": "⏳ Oczekujący ({count})",
    "adm_users_active": "✅ Aktywni ({count})",
    "adm_users_inactive": "❌ Nieaktywni ({count})",
    "adm_users_empty": "👥 Brak użytkowników w tej kategorii.",
    "adm_users_list": "👥 *Lista użytkowników:*\n\n",
    "adm_user_not_found": "⚠️ Użytkownik nie znaleziony.",
    "adm_user_card": (
        "👤 *Karta uczestnika*\n\n"
        "📛 *{full_name}*\n"
        "🏫 Klasa: {class_name}\n"
        "🎯 Specjalizacja: {specs}\n"
        "💻 Oprogramowanie: {software}\n"
        "📅 Zarejestrowany: {registered_at}\n"
        "🔖 Status: {status}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "adm_user_activate_btn": "✅ Aktywuj",
    "adm_user_deactivate_btn": "❌ Dezaktywuj",
    "adm_user_delete_btn": "🗑 Odrzuć i usuń",
    "adm_user_activated": "✅ Użytkownik aktywowany!",
    "adm_user_activated_notify": (
        "🎉 *Świetne wiadomości!*\n\n"
        "Twoje zgłoszenie do Klasyk TV zostało zatwierdzone! Witamy ✅"
    ),
    "adm_user_deactivated": "❌ Użytkownik dezaktywowany",
    "adm_user_deactivated_notify": (
        "ℹ️ Twój status w Klasyk TV zmieniony na *nieaktywny*.\n\n"
        "Skontaktuj się z administratorem, jeśli masz pytania."
    ),
    "adm_user_deleted": "🗑 Użytkownik *{name}* usunięty.",
    "adm_user_deleted_notify": (
        "ℹ️ Niestety, Twoje zgłoszenie do Klasyk TV zostało odrzucone.\n\n"
        "Możesz złożyć zgłoszenie ponownie."
    ),
    "adm_subs_title": "📥 *Zarządzanie zgłoszeniami*\n\nWybierz kategorię:",
    "adm_subs_new": "🆕 Nowe ({count})",
    "adm_subs_approved": "✅ Zatwierdzone ({count})",
    "adm_subs_rejected": "❌ Odrzucone ({count})",
    "adm_subs_all": "📋 Wszystkie ({count})",
    "adm_subs_empty": "📥 Brak zgłoszeń w tej kategorii.",
    "adm_subs_list": "📥 *Zgłoszenia:*\n\n",
    "adm_sub_not_found": "⚠️ Zgłoszenie nie znalezione.",
    "adm_sub_card": (
        "📥 *Zgłoszenie #{sub_id}*\n\n"
        "👤 Autor: *{submitter}*\n"
        "📌 Typ: {ctype}\n"
        "📍 Miejsce: {location}\n"
        "📝 Opis: {description}\n"
        "📎 Plik: {file_info}\n"
        "📅 Data: {date}\n"
        "🔖 Status: {status}"
    ),
    "adm_sub_show_file": "📎 Pokaż plik",
    "adm_sub_approve_btn": "✅ Zatwierdź",
    "adm_sub_reject_btn": "❌ Odrzuć",
    "adm_sub_approved": "✅ Zgłoszenie zatwierdzone!",
    "adm_sub_approved_notify": (
        "✅ *Twoje zgłoszenie #{sub_id} zatwierdzone!*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Dziękujemy za wkład w Klasyk TV! 🎉"
    ),
    "adm_sub_rejected": "❌ Zgłoszenie odrzucone",
    "adm_sub_rejected_notify": (
        "❌ *Zgłoszenie #{sub_id} nie przeszło moderacji*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Spróbuj wysłać ponownie z lepszym materiałem."
    ),
    "adm_sub_file_error": "Błąd wysyłania pliku",
    "adm_sub_file_not_found": "Plik nie znaleziony",
    "adm_events_title": "📅 *Zarządzanie wydarzeniami:*\n\n",
    "adm_events_empty": "📅 Brak wydarzeń.\n\nNaciśnij ➕ aby utworzyć nowe.",
    "adm_event_create_btn": "➕ Utwórz wydarzenie",
    "adm_event_row": (
        "*{title}*\n"
        "📆 {date} 🕐 {time} | 📍 {location}\n"
        "👥 Zapisanych: {signups} os.\n\n"
    ),
    "adm_event_view": (
        "📅 *{title}*\n\n"
        "📆 Data: {date}\n"
        "🕐 Czas: {time}\n"
        "📍 Miejsce: {location}\n"
        "📝 Opis: {description}\n\n"
    ),
    "adm_event_signups": "👥 *Zapisanych ({count}):*\n",
    "adm_event_no_signups": "👥 Jeszcze nikt się nie zapisał.",
    "adm_event_delete_btn": "🗑 Usuń wydarzenie",
    "adm_event_deleted": "🗑 Usunięto: {title}",
    "adm_event_back": "◀️ Do wydarzeń",
    "adm_event_add_title": (
        "➕ *Tworzenie nowego wydarzenia*\n\n"
        "📝 *Krok 1/5* — Wpisz *nazwę* wydarzenia\n"
        "_(np.: 🏆 Finał KVN)_\n\n"
        "Anuluj: /cancel"
    ),
    "adm_event_step2": (
        "✅ Nazwa: *{title}*\n\n"
        "📝 *Krok 2/5* — Podaj *datę* (format: DD.MM.RRRR)\n"
        "_(np.: 25.04.2026)_"
    ),
    "adm_event_date_invalid": "⚠️ Zły format. Wpisz datę DD.MM.RRRR (np.: 25.04.2026):",
    "adm_event_step3": (
        "✅ Data: *{date}*\n\n"
        "📝 *Krok 3/5* — Podaj *czas* (GG:MM)\n"
        "_(np.: 14:30, lub «—» jeśli nieznany)_"
    ),
    "adm_event_step4": (
        "✅ Czas: *{time}*\n\n"
        "📝 *Krok 4/5* — Podaj *miejsce*\n"
        "_(np.: Aula)_"
    ),
    "adm_event_step5": (
        "✅ Miejsce: *{location}*\n\n"
        "📝 *Krok 5/5* — Napisz *opis / co potrzeba*\n"
        "_(np.: Potrzeba 2 operatorów i fotograf)_"
    ),
    "adm_event_created": (
        "✅ *Wydarzenie utworzone!*\n\n"
        "🆔 #{event_id}\n"
        "📋 *{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "📝 {description}\n\n"
        "Już widoczne dla uczestników w «📅 Plan zdjęć»!"
    ),
    "adm_broadcast_title": (
        "📢 *Mailing*\n\n"
        "Odbiorców: *{count}* użytkowników\n\n"
        "Napisz tekst wiadomości dla wszystkich uczestników.\n"
        "Wspierane formatowanie *Markdown*.\n\n"
        "Anuluj: /cancel"
    ),
    "adm_broadcast_preview": (
        "📢 *Podgląd mailingu:*\n\n"
        "{text}\n\n"
        "─────────────────\n"
        "Zostanie wysłane do *{count}* użytkowników.\n"
        "Potwierdzić?"
    ),
    "adm_broadcast_send_btn": "✅ Wyślij",
    "adm_broadcast_cancel_btn": "❌ Anuluj",
    "adm_broadcast_cancelled": "❌ Mailing anulowany.",
    "adm_broadcast_done": (
        "📢 *Mailing zakończony!*\n\n"
        "✅ Dostarczono: {sent}\n"
        "❌ Nie dostarczono: {failed}"
    ),
    "adm_action_cancelled": "❌ Działanie anulowane.",
    "adm_kb_edit_title": "📝 *Edycja bazy wiedzy*\n\nWybierz materiał do edycji:",
    "adm_kb_edit_item": (
        "📝 *Edycja materiału:*\n\n"
        "*{title}*\n\n"
        "Obecny tekst:\n\n{text}\n\n"
        "✏️ *Wyślij nowy tekst dla tego materiału*:"
    ),
    "adm_kb_saved": "✅ Materiał zaktualizowany!",
    "adm_kb_not_found": "❌ Materiał nie znaleziony.",

    # ── Notifications ──
    "notify_new_member": (
        "🆕 <b>Nowy członek redakcji!</b>\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n"
        "💻 {software}\n"
        "🔗 @{username} | ID: <code>{uid}</code>"
    ),
    "notify_new_submission": (
        "📥 *Nowe zgłoszenie #{sub_id}*\n\n"
        "👤 {submitter} (@{username})\n"
        "📌 Typ: {ctype}\n"
        "📍 Miejsce: {location}\n"
        "📝 Opis: {description}"
    ),
    "notify_signup": (
        "📸 *Zapis na zdjęcia!*\n\n"
        "👤 {name} z {cls}\n"
        "🎬 Chce kręcić: *{title}*\n"
        "📆 {date}  📍 {location}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "notify_new_event": (
        "🆕 Nowe wydarzenie!\n\n"
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
        "Zapisz się w planie zdjęć!"
    ),
    "notify_broadcast": "📢 *Ogłoszenie od Klasyk TV*\n\n{text}",
}

# ─── ENGLISH ─────────────────────────────────────────────────────────────────
_TEXTS["en"] = {
    # ── Menu buttons ──
    "menu_team": "🎥 Join the team!",
    "menu_content": "📥 Submit content",
    "menu_schedule": "📅 Shooting plan",
    "menu_knowledge": "📚 Knowledge base",
    "menu_profile": "👤 My profile",
    "menu_admin": "🔧 Admin panel",
    "menu_lang": "🌐 Language",
    "menu_placeholder": "Choose a section 👇",

    # ── Language ──
    "lang_choose": "🌐 *Choose your language:*",
    "lang_changed": "✅ Language changed: *{lang_name}*",

    # ── General ──
    "welcome": (
        "👋 *Hi! Welcome to Klasyk Media Hub!*\n\n"
        "I help our school newsroom collect content, "
        "register participants, and plan shoots.\n\n"
        "Choose a section from the menu below 👇"
    ),
    "main_menu": "📋 *Main menu*\n\nChoose a section:",
    "cancel": "❌ Action cancelled. Returning to main menu.",
    "use_buttons": "Use the menu buttons 👇",
    "back_to_menu": "Returning to the main menu 👇",
    "access_denied": (
        "⛔ Please register first.\n\n"
        "Tap «🎥 Join the team!» and fill out the form."
    ),
    "admin_profile_text": "👤 *Your profile*\n\nYou are an administrator. Everything works 👍",
    "error_generic": "⚠️ An error occurred. Please try again later.",

    # ── Registration ──
    "reg_already": (
        "✅ *You're already on our team!*\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n\n"
        "To update your info — fill out the form again."
    ),
    "reg_update_btn": "🔄 Update profile",
    "reg_welcome": (
        "🎥 *Welcome to the Klasyk TV team!*\n\n"
        "Let's fill out a quick form — it'll take 1-2 minutes.\n\n"
        "📝 *Step 1/4* — Enter your *full name*:"
    ),
    "reg_step1": "📝 *Step 1/4* — Enter your *full name*:",
    "reg_name_short": "⚠️ Please enter your full name (first and last name):",
    "reg_name_ok": "👍 Got it: *{name}*\n\n📝 *Step 2/4* — Choose your *class*:",
    "reg_class_ok": (
        "👍 Class: *{cls}*\n\n"
        "📝 *Step 3/4* — Choose your *specialization(s)*.\n"
        "You can pick several! Tap ✅ Done when finished.\n"
        "If yours isn't listed — tap ✍️ Other."
    ),
    "reg_spec_empty": "⚠️ Select at least one specialization!",
    "reg_spec_other_btn": "✍️ Other",
    "reg_spec_done_btn": "✅ Done",
    "reg_spec_other_prompt": "✍️ Enter your specialization:",
    "reg_spec_other_added": "✅ Added: *{spec}*\nYou can pick more or tap ✅ Done.",
    "reg_spec_ok": (
        "👍 Specializations: *{specs}*\n\n"
        "📝 *Step 4/4* — What *software* do you know?\n"
        "_(CapCut, VN, Premiere, Photoshop, Canva etc. — write freely)_"
    ),
    "reg_confirm_summary": (
        "📋 *Review your form:*\n\n"
        "👤 Name: *{full_name}*\n"
        "🏫 Class: *{class_name}*\n"
        "🎯 Specialization: *{specs}*\n"
        "💻 Software: *{software}*\n\n"
        "Everything correct?"
    ),
    "reg_confirm_yes": "✅ All correct!",
    "reg_confirm_no": "✏️ Edit",
    "reg_restart_text": "🔄 Starting over!\n\n📝 *Step 1/4* — Enter your *full name*:",
    "reg_success": (
        "🎉 *Congratulations, {name}!*\n\n"
        "You're now registered with the *Klasyk TV* team!\n\n"
        "We'll contact you soon. Stay tuned for updates 🚀"
    ),

    # ── Content submission ──
    "con_start": (
        "📥 *Submit content*\n\n"
        "Great! Let's upload the material.\n\n"
        "📌 *Step 1/4* — Choose *content type*:"
    ),
    "con_type_text": (
        "✅ Type: *{ctype}*\n\n"
        "📌 *Step 2/4* — Write your news text or idea.\n"
        "_You can write multiple paragraphs!_"
    ),
    "con_type_file": (
        "✅ Type: *{ctype}*\n\n"
        "📌 *Step 2/4* — Upload a file.\n\n"
        "📎 *Send as document* (paperclip) — no quality loss\n"
        "or as a regular message — faster, but compressed"
    ),
    "con_file_doc": "📎 File received (document, no quality loss)",
    "con_file_photo": "📷 Photo received",
    "con_file_video": "🎬 Video received",
    "con_file_text": "📝 Text received",
    "con_file_invalid": "⚠️ Send a photo, video, document, or text.",
    "con_step3": (
        "✅ {label}\n\n"
        "📌 *Step 3/4* — Write a *description*:\n"
        "What's happening? Who's in the frame? What event?\n"
        "_The more detail — the better!_"
    ),
    "con_desc_short": "⚠️ Please describe in more detail — at least a few words.",
    "con_step4": "✅ Description saved!\n\n📌 *Step 4/4* — Specify *location / event*:",
    "con_success": (
        "🎉 *Thank you! Material sent to the newsroom.*\n\n"
        "📋 Submission #{sub_id}\n"
        "📌 {ctype} | 📍 {location}\n\n"
        "Editors will review and contact you if they need clarification."
    ),
    "con_back_menu": "Returning to menu 👇",

    # ── Schedule ──
    "sched_title": "📅 *Upcoming events — shooting plan:*\n\n",
    "sched_empty": "📅 No planned events yet. Check back later!",
    "sched_signup_btn": "📋 Sign up: {title}",
    "sched_refresh_btn": "🔄 Refresh list",
    "sched_refresh_title": "📅 *Current shooting plan:*\n\n",
    "sched_event_row": (
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
    ),
    "sched_event_row_short": (
        "*{title}* — {date} {time}\n"
        "💬 {description}\n"
        "📍 {location}\n\n"
    ),
    "sched_signup_success": "🎉 Signed you up for «{title}»!",
    "sched_already_signed": "✅ You're already signed up for: {title}",
    "sched_event_not_found": "⚠️ Event not found",
    "sched_admin_no_signup": "You're an admin — manage, don't sign up 🙂",
    "sched_signup_confirm": (
        "✅ *Done!* You're signed up for:\n"
        "*{title}*\n"
        "📆 {date}  📍 {location}\n\n"
        "We'll remind you closer to the date 🔔"
    ),

    # ── Knowledge base ──
    "kb_title": "📚 *Klasyk TV Knowledge Base*\n\nChoose a section:",
    "kb_back": "◀️ Back to knowledge base",
    "kb_not_found": "Section not found",

    # ── Profile ──
    "profile_title": "👤 *My profile*\n\n",
    "profile_not_found": (
        "👤 *Profile not found*\n\n"
        "You haven't registered yet.\n"
        "Tap *«🎥 Join the team!»* to fill out the form."
    ),
    "profile_info": (
        "📛 *{full_name}*\n"
        "🏫 Class: {class_name}\n"
        "🎯 Specialization: {specs}\n"
        "💻 Software: {software}\n"
        "📅 Member since: {registered_at}\n"
        "🔖 Status: {status}"
    ),
    "profile_edit_btn": "✏️ Update profile",
    "profile_edit_instruction": (
        "✏️ To update your info — tap *«🎥 Join the team!»* in the menu.\n"
        "Your form will be overwritten."
    ),
    "profile_signups": "\n\n📋 *My shooting sign-ups:*\n",
    "status_pending": "⏳ Under review",
    "status_active": "✅ Active member",
    "status_inactive": "❌ Inactive",

    # ── Admin panel ──
    "adm_no_access": "⛔ You don't have access to the admin panel.",
    "adm_no_access_short": "⛔ Access denied",
    "adm_updated": "🔄 Admin menu updated.",
    "adm_title": "🔧 *Admin Panel*\n\nChoose a section:",
    "adm_stats_btn": "📊 Statistics",
    "adm_users_btn": "👥 Users",
    "adm_subs_btn": "📥 Submissions",
    "adm_events_btn": "📅 Events",
    "adm_event_add_btn": "➕ New event",
    "adm_broadcast_btn": "📢 Broadcast",
    "adm_edit_kb_btn": "📝 Edit knowledge base",
    "adm_back_btn": "◀️ Back to admin panel",
    "adm_back_short": "◀️ Back",
    "adm_stats": (
        "📊 *Klasyk Media Hub Statistics*\n\n"
        "👥 *Users:*\n"
        "  Total: {total}\n"
        "  ✅ Active: {active}\n"
        "  ⏳ Pending: {pending}\n"
        "  ❌ Inactive: {inactive}\n\n"
        "📥 *Content submissions:*\n"
        "  Total: {sub_total}\n"
        "  🆕 New: {sub_new}\n"
        "  ✅ Approved: {sub_approved}\n"
        "  ❌ Rejected: {sub_rejected}\n\n"
        "📅 Events: {events}\n"
        "📋 Shooting sign-ups: {signups}"
    ),
    "adm_users_title": "👥 *User management*\n\nChoose a category:",
    "adm_users_all": "📋 All ({count})",
    "adm_users_pending": "⏳ Pending ({count})",
    "adm_users_active": "✅ Active ({count})",
    "adm_users_inactive": "❌ Inactive ({count})",
    "adm_users_empty": "👥 No users in this category.",
    "adm_users_list": "👥 *User list:*\n\n",
    "adm_user_not_found": "⚠️ User not found.",
    "adm_user_card": (
        "👤 *Member card*\n\n"
        "📛 *{full_name}*\n"
        "🏫 Class: {class_name}\n"
        "🎯 Specialization: {specs}\n"
        "💻 Software: {software}\n"
        "📅 Registered: {registered_at}\n"
        "🔖 Status: {status}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "adm_user_activate_btn": "✅ Activate",
    "adm_user_deactivate_btn": "❌ Deactivate",
    "adm_user_delete_btn": "🗑 Reject & delete",
    "adm_user_activated": "✅ User activated!",
    "adm_user_activated_notify": (
        "🎉 *Great news!*\n\n"
        "Your application to Klasyk TV has been approved! Welcome ✅"
    ),
    "adm_user_deactivated": "❌ User deactivated",
    "adm_user_deactivated_notify": (
        "ℹ️ Your status in Klasyk TV has been changed to *inactive*.\n\n"
        "Contact the administrator if you have questions."
    ),
    "adm_user_deleted": "🗑 User *{name}* deleted.",
    "adm_user_deleted_notify": (
        "ℹ️ Unfortunately, your application to Klasyk TV has been rejected.\n\n"
        "You can apply again."
    ),
    "adm_subs_title": "📥 *Submission management*\n\nChoose a category:",
    "adm_subs_new": "🆕 New ({count})",
    "adm_subs_approved": "✅ Approved ({count})",
    "adm_subs_rejected": "❌ Rejected ({count})",
    "adm_subs_all": "📋 All ({count})",
    "adm_subs_empty": "📥 No submissions in this category.",
    "adm_subs_list": "📥 *Submissions:*\n\n",
    "adm_sub_not_found": "⚠️ Submission not found.",
    "adm_sub_card": (
        "📥 *Submission #{sub_id}*\n\n"
        "👤 Author: *{submitter}*\n"
        "📌 Type: {ctype}\n"
        "📍 Location: {location}\n"
        "📝 Description: {description}\n"
        "📎 File: {file_info}\n"
        "📅 Date: {date}\n"
        "🔖 Status: {status}"
    ),
    "adm_sub_show_file": "📎 Show file",
    "adm_sub_approve_btn": "✅ Approve",
    "adm_sub_reject_btn": "❌ Reject",
    "adm_sub_approved": "✅ Submission approved!",
    "adm_sub_approved_notify": (
        "✅ *Your submission #{sub_id} has been approved!*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Thank you for contributing to Klasyk TV! 🎉"
    ),
    "adm_sub_rejected": "❌ Submission rejected",
    "adm_sub_rejected_notify": (
        "❌ *Submission #{sub_id} didn't pass moderation*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Try submitting again with better quality material."
    ),
    "adm_sub_file_error": "Error sending file",
    "adm_sub_file_not_found": "File not found",
    "adm_events_title": "📅 *Event management:*\n\n",
    "adm_events_empty": "📅 No events.\n\nTap ➕ to create one.",
    "adm_event_create_btn": "➕ Create event",
    "adm_event_row": (
        "*{title}*\n"
        "📆 {date} 🕐 {time} | 📍 {location}\n"
        "👥 Signed up: {signups} people\n\n"
    ),
    "adm_event_view": (
        "📅 *{title}*\n\n"
        "📆 Date: {date}\n"
        "🕐 Time: {time}\n"
        "📍 Location: {location}\n"
        "📝 Description: {description}\n\n"
    ),
    "adm_event_signups": "👥 *Signed up ({count}):*\n",
    "adm_event_no_signups": "👥 Nobody signed up yet.",
    "adm_event_delete_btn": "🗑 Delete event",
    "adm_event_deleted": "🗑 Deleted: {title}",
    "adm_event_back": "◀️ To events",
    "adm_event_add_title": (
        "➕ *Creating a new event*\n\n"
        "📝 *Step 1/5* — Enter the event *name*\n"
        "_(e.g.: 🏆 KVN Finals)_\n\n"
        "Cancel: /cancel"
    ),
    "adm_event_step2": (
        "✅ Name: *{title}*\n\n"
        "📝 *Step 2/5* — Enter the *date* (format: DD.MM.YYYY)\n"
        "_(e.g.: 25.04.2026)_"
    ),
    "adm_event_date_invalid": "⚠️ Wrong format. Enter date as DD.MM.YYYY (e.g.: 25.04.2026):",
    "adm_event_step3": (
        "✅ Date: *{date}*\n\n"
        "📝 *Step 3/5* — Enter the *time* (HH:MM)\n"
        "_(e.g.: 14:30, or «—» if unknown)_"
    ),
    "adm_event_step4": (
        "✅ Time: *{time}*\n\n"
        "📝 *Step 4/5* — Enter the *location*\n"
        "_(e.g.: Assembly hall)_"
    ),
    "adm_event_step5": (
        "✅ Location: *{location}*\n\n"
        "📝 *Step 5/5* — Write a *description / what's needed*\n"
        "_(e.g.: Need 2 camera operators and a photographer)_"
    ),
    "adm_event_created": (
        "✅ *Event created!*\n\n"
        "🆔 #{event_id}\n"
        "📋 *{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "📝 {description}\n\n"
        "It's now visible to participants in «📅 Shooting plan»!"
    ),
    "adm_broadcast_title": (
        "📢 *Broadcast*\n\n"
        "Recipients: *{count}* users\n\n"
        "Write the message text for all participants.\n"
        "*Markdown* formatting supported.\n\n"
        "Cancel: /cancel"
    ),
    "adm_broadcast_preview": (
        "📢 *Broadcast preview:*\n\n"
        "{text}\n\n"
        "─────────────────\n"
        "Will be sent to *{count}* users.\n"
        "Confirm?"
    ),
    "adm_broadcast_send_btn": "✅ Send",
    "adm_broadcast_cancel_btn": "❌ Cancel",
    "adm_broadcast_cancelled": "❌ Broadcast cancelled.",
    "adm_broadcast_done": (
        "📢 *Broadcast complete!*\n\n"
        "✅ Delivered: {sent}\n"
        "❌ Failed: {failed}"
    ),
    "adm_action_cancelled": "❌ Action cancelled.",
    "adm_kb_edit_title": "📝 *Edit knowledge base*\n\nChoose a material to edit:",
    "adm_kb_edit_item": (
        "📝 *Editing material:*\n\n"
        "*{title}*\n\n"
        "Current text:\n\n{text}\n\n"
        "✏️ *Send the new text for this material*:"
    ),
    "adm_kb_saved": "✅ Material updated!",
    "adm_kb_not_found": "❌ Material not found.",

    # ── Notifications ──
    "notify_new_member": (
        "🆕 <b>New newsroom member!</b>\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n"
        "💻 {software}\n"
        "🔗 @{username} | ID: <code>{uid}</code>"
    ),
    "notify_new_submission": (
        "📥 *New submission #{sub_id}*\n\n"
        "👤 {submitter} (@{username})\n"
        "📌 Type: {ctype}\n"
        "📍 Location: {location}\n"
        "📝 Description: {description}"
    ),
    "notify_signup": (
        "📸 *Shooting sign-up!*\n\n"
        "👤 {name} from {cls}\n"
        "🎬 Wants to shoot: *{title}*\n"
        "📆 {date}  📍 {location}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "notify_new_event": (
        "🆕 New event!\n\n"
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
        "Sign up in the shooting plan!"
    ),
    "notify_broadcast": "📢 *Announcement from Klasyk TV*\n\n{text}",
}

# ─── UKRAINIAN ───────────────────────────────────────────────────────────────
_TEXTS["uk"] = {
    # ── Menu buttons ──
    "menu_team": "🎥 Хочу до команди!",
    "menu_content": "📥 Запропонувати контент",
    "menu_schedule": "📅 План зйомок",
    "menu_knowledge": "📚 База знань",
    "menu_profile": "👤 Мій профіль",
    "menu_admin": "🔧 Адмін-панель",
    "menu_lang": "🌐 Мова",
    "menu_placeholder": "Обери розділ 👇",

    # ── Language ──
    "lang_choose": "🌐 *Оберіть мову / Choose language:*",
    "lang_changed": "✅ Мову змінено: *{lang_name}*",

    # ── General ──
    "welcome": (
        "👋 *Привіт! Ласкаво просимо до Klasyk Media Hub!*\n\n"
        "Я допомагаю нашій шкільній редакції збирати контент, "
        "реєструвати учасників та планувати зйомки.\n\n"
        "Обери потрібний розділ у меню нижче 👇"
    ),
    "main_menu": "📋 *Головне меню*\n\nОбери розділ:",
    "cancel": "❌ Дію скасовано. Повертаємося до головного меню.",
    "use_buttons": "Використовуй кнопки меню 👇",
    "back_to_menu": "Повертаємося до головного меню 👇",
    "access_denied": (
        "⛔ Спочатку зареєструйся в команді.\n\n"
        "Натисни «🎥 Хочу до команди!» та заповни анкету."
    ),
    "admin_profile_text": "👤 *Ваш профіль*\n\nВи — адміністратор. Все працює 👍",
    "error_generic": "⚠️ Сталася помилка. Спробуйте пізніше.",

    # ── Registration ──
    "reg_already": (
        "✅ *Ти вже в нашій команді!*\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n\n"
        "Щоб оновити дані — пройди анкету знову."
    ),
    "reg_update_btn": "🔄 Оновити анкету",
    "reg_welcome": (
        "🎥 *Ласкаво просимо до команди Klasyk TV!*\n\n"
        "Заповнимо невелику анкету — це займе 1-2 хвилини.\n\n"
        "📝 *Крок 1/4* — Напиши своє *ПІБ* (Прізвище Ім'я По батькові):"
    ),
    "reg_step1": "📝 *Крок 1/4* — Напиши своє *ПІБ*:",
    "reg_name_short": "⚠️ Будь ласка, введи повне ПІБ (мінімум Прізвище та Ім'я):",
    "reg_name_ok": "👍 Записав: *{name}*\n\n📝 *Крок 2/4* — Обери свій *клас*:",
    "reg_class_ok": (
        "👍 Клас: *{cls}*\n\n"
        "📝 *Крок 3/4* — Обери *спеціалізацію(ї)*.\n"
        "Можна обрати кілька! Натисни ✅ Готово коли закінчиш.\n"
        "Якщо потрібної немає — натисни ✍️ Інше."
    ),
    "reg_spec_empty": "⚠️ Обери хоча б одну спеціалізацію!",
    "reg_spec_other_btn": "✍️ Інше",
    "reg_spec_done_btn": "✅ Готово",
    "reg_spec_other_prompt": "✍️ Напиши свою спеціалізацію:",
    "reg_spec_other_added": "✅ Додано: *{spec}*\nМожеш обрати ще або натисни ✅ Готово.",
    "reg_spec_ok": (
        "👍 Спеціалізації: *{specs}*\n\n"
        "📝 *Крок 4/4* — Якими *програмами* ти володієш?\n"
        "_(CapCut, VN, Premiere, Photoshop, Canva тощо — пиши у вільній формі)_"
    ),
    "reg_confirm_summary": (
        "📋 *Перевір свою анкету:*\n\n"
        "👤 ПІБ: *{full_name}*\n"
        "🏫 Клас: *{class_name}*\n"
        "🎯 Спеціалізація: *{specs}*\n"
        "💻 Програми: *{software}*\n\n"
        "Все вірно?"
    ),
    "reg_confirm_yes": "✅ Все вірно!",
    "reg_confirm_no": "✏️ Виправити",
    "reg_restart_text": "🔄 Почнемо спочатку!\n\n📝 *Крок 1/4* — Напиши своє *ПІБ*:",
    "reg_success": (
        "🎉 *Вітаємо, {name}!*\n\n"
        "Ти успішно зареєстрований(а) в команді *Klasyk TV*!\n\n"
        "Ми скоро зв'яжемося з тобою. Слідкуй за оновленнями в боті 🚀"
    ),

    # ── Content submission ──
    "con_start": (
        "📥 *Запропонувати контент*\n\n"
        "Чудово! Давай завантажимо матеріал.\n\n"
        "📌 *Крок 1/4* — Обери *тип контенту*:"
    ),
    "con_type_text": (
        "✅ Тип: *{ctype}*\n\n"
        "📌 *Крок 2/4* — Напиши текст своєї новини чи ідеї.\n"
        "_Можна кілька абзаців — пиши як хочеш!_"
    ),
    "con_type_file": (
        "✅ Тип: *{ctype}*\n\n"
        "📌 *Крок 2/4* — Завантаж файл.\n\n"
        "📎 *Відправ як документ* (скріпка) — без втрати якості\n"
        "або звичайним повідомленням — швидше, але стиснуте"
    ),
    "con_file_doc": "📎 Файл отримано (документ, без втрати якості)",
    "con_file_photo": "📷 Фото отримано",
    "con_file_video": "🎬 Відео отримано",
    "con_file_text": "📝 Текст отримано",
    "con_file_invalid": "⚠️ Надішли фото, відео, документ або текст новини.",
    "con_step3": (
        "✅ {label}\n\n"
        "📌 *Крок 3/4* — Напиши *опис*:\n"
        "Що відбувається? Хто в кадрі? Яка подія?\n"
        "_Чим детальніше — тим краще!_"
    ),
    "con_desc_short": "⚠️ Будь ласка, опиши детальніше — хоча б кілька слів.",
    "con_step4": "✅ Опис записано!\n\n📌 *Крок 4/4* — Вкажи *місце / подію*:",
    "con_success": (
        "🎉 *Дякуємо! Матеріал відправлено до редакції.*\n\n"
        "📋 Заявка #{sub_id}\n"
        "📌 {ctype} | 📍 {location}\n\n"
        "Редактори розглянуть і зв'яжуться з тобою, якщо потрібні уточнення."
    ),
    "con_back_menu": "Повертаємося до меню 👇",

    # ── Schedule ──
    "sched_title": "📅 *Найближчі події — план зйомок:*\n\n",
    "sched_empty": "📅 Поки немає запланованих подій. Заглянь пізніше!",
    "sched_signup_btn": "📋 Записатися: {title}",
    "sched_refresh_btn": "🔄 Оновити список",
    "sched_refresh_title": "📅 *Актуальний план зйомок:*\n\n",
    "sched_event_row": (
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
    ),
    "sched_event_row_short": (
        "*{title}* — {date} {time}\n"
        "💬 {description}\n"
        "📍 {location}\n\n"
    ),
    "sched_signup_success": "🎉 Записав тебе на «{title}»!",
    "sched_already_signed": "✅ Ти вже записаний(а) на: {title}",
    "sched_event_not_found": "⚠️ Подію не знайдено",
    "sched_admin_no_signup": "Ти адмін — керуй процесом, а не записуйся 🙂",
    "sched_signup_confirm": (
        "✅ *Готово!* Ти записаний(а) на:\n"
        "*{title}*\n"
        "📆 {date}  📍 {location}\n\n"
        "Ми нагадаємо ближче до дати 🔔"
    ),

    # ── Knowledge base ──
    "kb_title": "📚 *База знань Klasyk TV*\n\nОбери розділ:",
    "kb_back": "◀️ Назад до бази знань",
    "kb_not_found": "Розділ не знайдено",

    # ── Profile ──
    "profile_title": "👤 *Мій профіль*\n\n",
    "profile_not_found": (
        "👤 *Профіль не знайдено*\n\n"
        "Ти ще не зареєстрований(а) в команді.\n"
        "Натисни *«🎥 Хочу до команди!»* щоб заповнити анкету."
    ),
    "profile_info": (
        "📛 *{full_name}*\n"
        "🏫 Клас: {class_name}\n"
        "🎯 Спеціалізація: {specs}\n"
        "💻 Програми: {software}\n"
        "📅 В команді з: {registered_at}\n"
        "🔖 Статус: {status}"
    ),
    "profile_edit_btn": "✏️ Оновити анкету",
    "profile_edit_instruction": (
        "✏️ Щоб оновити дані — натисни *«🎥 Хочу до команди!»* в меню.\n"
        "Анкета перезапишеться."
    ),
    "profile_signups": "\n\n📋 *Мої записи на зйомку:*\n",
    "status_pending": "⏳ На розгляді",
    "status_active": "✅ Активний учасник",
    "status_inactive": "❌ Неактивний",

    # ── Admin panel ──
    "adm_no_access": "⛔ У тебе немає доступу до панелі адміністратора.",
    "adm_no_access_short": "⛔ Немає доступу",
    "adm_updated": "🔄 Оновив адмін-меню.",
    "adm_title": "🔧 *Панель адміністратора*\n\nОбери розділ:",
    "adm_stats_btn": "📊 Статистика",
    "adm_users_btn": "👥 Користувачі",
    "adm_subs_btn": "📥 Заявки",
    "adm_events_btn": "📅 Події",
    "adm_event_add_btn": "➕ Нова подія",
    "adm_broadcast_btn": "📢 Розсилка",
    "adm_edit_kb_btn": "📝 Редагувати базу знань",
    "adm_back_btn": "◀️ Назад до адмін-панелі",
    "adm_back_short": "◀️ Назад",
    "adm_stats": (
        "📊 *Статистика Klasyk Media Hub*\n\n"
        "👥 *Користувачі:*\n"
        "  Всього: {total}\n"
        "  ✅ Активні: {active}\n"
        "  ⏳ На розгляді: {pending}\n"
        "  ❌ Неактивні: {inactive}\n\n"
        "📥 *Контент-заявки:*\n"
        "  Всього: {sub_total}\n"
        "  🆕 Нові: {sub_new}\n"
        "  ✅ Схвалено: {sub_approved}\n"
        "  ❌ Відхилено: {sub_rejected}\n\n"
        "📅 Подій: {events}\n"
        "📋 Записів на зйомки: {signups}"
    ),
    "adm_users_title": "👥 *Управління користувачами*\n\nОбери категорію:",
    "adm_users_all": "📋 Всі ({count})",
    "adm_users_pending": "⏳ Очікуючі ({count})",
    "adm_users_active": "✅ Активні ({count})",
    "adm_users_inactive": "❌ Неактивні ({count})",
    "adm_users_empty": "👥 Немає користувачів у цій категорії.",
    "adm_users_list": "👥 *Список користувачів:*\n\n",
    "adm_user_not_found": "⚠️ Користувача не знайдено.",
    "adm_user_card": (
        "👤 *Картка учасника*\n\n"
        "📛 *{full_name}*\n"
        "🏫 Клас: {class_name}\n"
        "🎯 Спеціалізація: {specs}\n"
        "💻 ПЗ: {software}\n"
        "📅 Зареєстрований: {registered_at}\n"
        "🔖 Статус: {status}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "adm_user_activate_btn": "✅ Активувати",
    "adm_user_deactivate_btn": "❌ Деактивувати",
    "adm_user_delete_btn": "🗑 Відхилити та видалити",
    "adm_user_activated": "✅ Користувача активовано!",
    "adm_user_activated_notify": (
        "🎉 *Чудові новини!*\n\n"
        "Твою заявку до команди Klasyk TV схвалено! Ласкаво просимо ✅"
    ),
    "adm_user_deactivated": "❌ Користувача деактивовано",
    "adm_user_deactivated_notify": (
        "ℹ️ Твій статус у команді Klasyk TV змінено на *неактивний*.\n\n"
        "Звернись до адміністратора, якщо є питання."
    ),
    "adm_user_deleted": "🗑 Користувача *{name}* видалено.",
    "adm_user_deleted_notify": (
        "ℹ️ На жаль, твою заявку до команди Klasyk TV відхилено.\n\n"
        "Ти можеш подати заявку повторно."
    ),
    "adm_subs_title": "📥 *Управління контент-заявками*\n\nОбери категорію:",
    "adm_subs_new": "🆕 Нові ({count})",
    "adm_subs_approved": "✅ Схвалені ({count})",
    "adm_subs_rejected": "❌ Відхилені ({count})",
    "adm_subs_all": "📋 Всі ({count})",
    "adm_subs_empty": "📥 Немає заявок у цій категорії.",
    "adm_subs_list": "📥 *Контент-заявки:*\n\n",
    "adm_sub_not_found": "⚠️ Заявку не знайдено.",
    "adm_sub_card": (
        "📥 *Заявка #{sub_id}*\n\n"
        "👤 Автор: *{submitter}*\n"
        "📌 Тип: {ctype}\n"
        "📍 Місце: {location}\n"
        "📝 Опис: {description}\n"
        "📎 Файл: {file_info}\n"
        "📅 Дата: {date}\n"
        "🔖 Статус: {status}"
    ),
    "adm_sub_show_file": "📎 Показати файл",
    "adm_sub_approve_btn": "✅ Схвалити",
    "adm_sub_reject_btn": "❌ Відхилити",
    "adm_sub_approved": "✅ Заявку схвалено!",
    "adm_sub_approved_notify": (
        "✅ *Твою заявку #{sub_id} схвалено!*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Дякуємо за внесок у Klasyk TV! 🎉"
    ),
    "adm_sub_rejected": "❌ Заявку відхилено",
    "adm_sub_rejected_notify": (
        "❌ *Заявка #{sub_id} не пройшла модерацію*\n\n"
        "📌 {ctype} | 📍 {location}\n"
        "Спробуй відправити знову з якіснішим матеріалом."
    ),
    "adm_sub_file_error": "Помилка відправки файлу",
    "adm_sub_file_not_found": "Файл не знайдено",
    "adm_events_title": "📅 *Управління подіями:*\n\n",
    "adm_events_empty": "📅 Немає подій.\n\nНатисни ➕ щоб створити нову.",
    "adm_event_create_btn": "➕ Створити подію",
    "adm_event_row": (
        "*{title}*\n"
        "📆 {date} 🕐 {time} | 📍 {location}\n"
        "👥 Записалось: {signups} осіб\n\n"
    ),
    "adm_event_view": (
        "📅 *{title}*\n\n"
        "📆 Дата: {date}\n"
        "🕐 Час: {time}\n"
        "📍 Місце: {location}\n"
        "📝 Опис: {description}\n\n"
    ),
    "adm_event_signups": "👥 *Записалось ({count}):*\n",
    "adm_event_no_signups": "👥 Поки ніхто не записався.",
    "adm_event_delete_btn": "🗑 Видалити подію",
    "adm_event_deleted": "🗑 Видалено: {title}",
    "adm_event_back": "◀️ До подій",
    "adm_event_add_title": (
        "➕ *Створення нової події*\n\n"
        "📝 *Крок 1/5* — Напиши *назву* події\n"
        "_(наприклад: 🏆 Фінал КВН)_\n\n"
        "Скасувати: /cancel"
    ),
    "adm_event_step2": (
        "✅ Назва: *{title}*\n\n"
        "📝 *Крок 2/5* — Вкажи *дату* (формат: ДД.ММ.РРРР)\n"
        "_(наприклад: 25.04.2026)_"
    ),
    "adm_event_date_invalid": "⚠️ Невірний формат. Введи дату ДД.ММ.РРРР (наприклад: 25.04.2026):",
    "adm_event_step3": (
        "✅ Дата: *{date}*\n\n"
        "📝 *Крок 3/5* — Вкажи *час* (ГГ:ХХ)\n"
        "_(наприклад: 14:30, або «—» якщо невідомо)_"
    ),
    "adm_event_step4": (
        "✅ Час: *{time}*\n\n"
        "📝 *Крок 4/5* — Вкажи *місце*\n"
        "_(наприклад: Актова зала)_"
    ),
    "adm_event_step5": (
        "✅ Місце: *{location}*\n\n"
        "📝 *Крок 5/5* — Напиши *опис / що потрібно*\n"
        "_(наприклад: Потрібні 2 оператори та фотограф)_"
    ),
    "adm_event_created": (
        "✅ *Подію створено!*\n\n"
        "🆔 #{event_id}\n"
        "📋 *{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "📝 {description}\n\n"
        "Вона вже видна учасникам у «📅 План зйомок»!"
    ),
    "adm_broadcast_title": (
        "📢 *Розсилка*\n\n"
        "Отримувачів: *{count}* користувачів\n\n"
        "Напиши текст повідомлення для всіх учасників.\n"
        "Підтримується форматування *Markdown*.\n\n"
        "Скасувати: /cancel"
    ),
    "adm_broadcast_preview": (
        "📢 *Попередній перегляд розсилки:*\n\n"
        "{text}\n\n"
        "─────────────────\n"
        "Буде відправлено *{count}* користувачам.\n"
        "Підтвердити?"
    ),
    "adm_broadcast_send_btn": "✅ Відправити",
    "adm_broadcast_cancel_btn": "❌ Скасувати",
    "adm_broadcast_cancelled": "❌ Розсилку скасовано.",
    "adm_broadcast_done": (
        "📢 *Розсилку завершено!*\n\n"
        "✅ Доставлено: {sent}\n"
        "❌ Не доставлено: {failed}"
    ),
    "adm_action_cancelled": "❌ Дію скасовано.",
    "adm_kb_edit_title": "📝 *Редагування бази знань*\n\nОбери матеріал для редагування:",
    "adm_kb_edit_item": (
        "📝 *Редагування матеріалу:*\n\n"
        "*{title}*\n\n"
        "Поточний текст:\n\n{text}\n\n"
        "✏️ *Надішліть новий текст для цього матеріалу*:"
    ),
    "adm_kb_saved": "✅ Матеріал оновлено!",
    "adm_kb_not_found": "❌ Матеріал не знайдено.",

    # ── Notifications ──
    "notify_new_member": (
        "🆕 <b>Новий учасник редакції!</b>\n\n"
        "👤 {full_name} | {class_name}\n"
        "🎯 {specs}\n"
        "💻 {software}\n"
        "🔗 @{username} | ID: <code>{uid}</code>"
    ),
    "notify_new_submission": (
        "📥 *Нова заявка #{sub_id}*\n\n"
        "👤 {submitter} (@{username})\n"
        "📌 Тип: {ctype}\n"
        "📍 Місце: {location}\n"
        "📝 Опис: {description}"
    ),
    "notify_signup": (
        "📸 *Запис на зйомку!*\n\n"
        "👤 {name} з {cls}\n"
        "🎬 Хоче знімати: *{title}*\n"
        "📆 {date}  📍 {location}\n"
        "🔗 @{username} | ID: `{uid}`"
    ),
    "notify_new_event": (
        "🆕 Нова подія!\n\n"
        "*{title}*\n"
        "📆 {date}  🕐 {time}\n"
        "📍 {location}\n"
        "💬 {description}\n\n"
        "Запишись у плані зйомок!"
    ),
    "notify_broadcast": "📢 *Оголошення від Klasyk TV*\n\n{text}",
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def t(key: str, lang: str = DEFAULT_LANG, **kwargs) -> str:
    """Get translated text. Falls back to Russian, then returns [key]."""
    text = _TEXTS.get(lang, {}).get(key) or _TEXTS[DEFAULT_LANG].get(key) or f"[{key}]"
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def get_all_values(key: str) -> list[str]:
    """Get all language variants for a translation key."""
    values = []
    for lang_data in _TEXTS.values():
        v = lang_data.get(key)
        if v and v not in values:
            values.append(v)
    return values


def menu_button_re(key: str) -> str:
    """Build a regex pattern that matches all language variants of a menu button."""
    variants = get_all_values(key)
    return "^(" + "|".join(re.escape(v) for v in variants) + ")$"


def all_menu_texts() -> set[str]:
    """Return a set of ALL menu button texts in ALL languages."""
    keys = ["menu_team", "menu_content", "menu_schedule", "menu_knowledge",
            "menu_profile", "menu_admin", "menu_lang"]
    result = set()
    for k in keys:
        result.update(get_all_values(k))
    return result


def is_menu_button(text: str) -> bool:
    """Check if text matches any known menu button in any language."""
    return text in all_menu_texts()


def identify_menu_key(text: str) -> str | None:
    """Identify which menu key a button text corresponds to."""
    keys = ["menu_team", "menu_content", "menu_schedule", "menu_knowledge",
            "menu_profile", "menu_admin", "menu_lang"]
    for k in keys:
        if text in get_all_values(k):
            return k
    return None


async def get_lang(update, context) -> str:
    """Get user's language from context cache or database."""
    if context and context.user_data and "lang" in context.user_data:
        return context.user_data["lang"]
    # Try DB
    from database import get_user_lang
    user_id = update.effective_user.id if update and update.effective_user else None
    if user_id:
        db_lang = get_user_lang(user_id)
        if db_lang:
            if context and context.user_data is not None:
                context.user_data["lang"] = db_lang
            return db_lang
    if context and context.user_data is not None:
        context.user_data["lang"] = DEFAULT_LANG
    return DEFAULT_LANG


def set_lang_cached(context, lang: str) -> None:
    """Cache language in context.user_data."""
    if context and context.user_data is not None:
        context.user_data["lang"] = lang
