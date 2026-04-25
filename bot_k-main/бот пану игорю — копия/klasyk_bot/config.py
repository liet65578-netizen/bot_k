"""
Конфигурация бота — вставь свои токены сюда или используй .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Supported languages for content (must match i18n.LANGUAGES keys)
SUPPORTED_LANGS = ("pl", "en", "ru", "uk")

# BOT_ENV=test  →  загружает .env.test вместо .env
_env_name = os.getenv("BOT_ENV", "")
_env_file = Path(__file__).parent / (f".env.{_env_name}" if _env_name else ".env")
load_dotenv(_env_file)

# ─── Обязательно заполнить ──────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан! Укажи его в .env файле или переменной окружения.")

# ID закрытой группы «Klasyk TV Admin» (отрицательное число, напр. -1001234567890)
ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "0"))

# ID(ы) администраторов:
# поддерживаем как старый формат MAIN_ADMIN_ID=123
# так и список MAIN_ADMIN_ID=123,456 или отдельную переменную ADMIN_IDS=123,456
_admin_ids_raw = os.getenv("ADMIN_IDS") or os.getenv("MAIN_ADMIN_ID", "0")
ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in _admin_ids_raw.split(",")
    if x.strip()
]

# Для обратной совместимости "главный админ" — первый ID из списка.
MAIN_ADMIN_ID: int = ADMIN_IDS[0] if ADMIN_IDS else 0

# ─── Списки классов ──────────────────────────────────────────────────────────
CLASSES = [
    "1A", "1B", "1C", "1D",
    "2A", "2B", "2C", "2D",
]

# ─── Специализации / списки (локализуемые) ────────────────────────────────────
SPECS_BY_LANG = {
    "ru": ["🎥 Съёмка", "✂️ Монтаж", "🎤 Ведущий / Интервьюер", "📣 Маркетинг / SMM", "✍️ Копирайтинг"],
    "uk": ["🎥 Зйомка", "✂️ Монтаж", "🎤 Ведучий / Інтерв’юер", "📣 Маркетинг / SMM", "✍️ Копірайтинг"],
    "en": ["🎥 Filming", "✂️ Editing", "🎤 Host / Interviewer", "📣 Marketing / SMM", "✍️ Copywriting"],
    "pl": ["🎥 Nagrania", "✂️ Montaż", "🎤 Prowadzący / wywiady", "📣 Marketing / SMM", "✍️ Copywriting"],
}

# ─── Типы контента ───────────────────────────────────────────────────────────
CONTENT_TYPES_BY_LANG = {
    "ru": ["📷 Фото", "🎬 Видео", "📝 Текст / Новость"],
    "uk": ["📷 Фото", "🎬 Відео", "📝 Текст / Новина"],
    "en": ["📷 Photo", "🎬 Video", "📝 Text / News"],
    "pl": ["📷 Zdjęcie", "🎬 Wideo", "📝 Tekst / aktualność"],
}

# ─── Локации / События ───────────────────────────────────────────────────────
LOCATIONS_BY_LANG = {
    "ru": ["🏟 Спортзал", "🔬 Школа", "🎭 Столовая", "🌳 Улица / Двор", "🏠 Интернат", "📌 Другое"],
    "uk": ["🏟 Спортзал", "🔬 Школа", "🎭 Їдальня", "🌳 Вулиця / Двір", "🏠 Інтернат", "📌 Інше"],
    "en": ["🏟 Gym", "🔬 School", "🎭 Cafeteria", "🌳 Outdoors / yard", "🏠 Dormitory", "📌 Other"],
    "pl": ["🏟 Sala gimnastyczna", "🔬 Szkoła", "🎭 Stołówka", "🌳 Na zewnątrz / dziedziniec", "🏠 Internat", "📌 Inne"],
}

# ─── База знаний (локализуемая) ───────────────────────────────────────────────
_KB = [
    {"id": "kb_terms", "icon": "📖"},
    {"id": "kb_capcut", "icon": "✂️"},
    {"id": "kb_hooks", "icon": "🪝"},
    {"id": "kb_checklist", "icon": "✅"},
]

KNOWLEDGE_ITEMS_BY_LANG = {
    "ru": [
        {
            **_KB[0],
            "title": "Медиа-термины",
            "text": (
                "*Медиа-словарь Klasyk TV*\n\n"
                "🎬 *B-roll* — фоновые кадры без говорящего человека\n"
                "🎙 *Stand-up* — ведущий говорит прямо в камеру\n"
                "💡 *Hook* — первые 3 секунды, которые удерживают зрителя\n"
                "✂️ *Cut* — жёсткая склейка двух кадров\n"
                "🔊 *Voice-over* — закадровый голос\n"
                "📐 *Правило третей* — главный объект на 1/3 кадра\n"
                "🎨 *Color grading* — цветокоррекция видео\n"
                "📍 *Location* — место съёмки\n"
                "🎯 *CTA* — Call To Action, призыв к действию\n"
                "📊 *Reach* — охват публикации\n"
                "💬 *Engagement* — вовлечённость (лайки+комменты+репосты)\n"
            ),
        },
        {
            **_KB[1],
            "title": "CapCut — туториалы",
            "text": (
                "*CapCut — быстрый старт*\n\n"
                "1️⃣ *Субтитры авто* → Текст → Авто-субтитры\n"
                "2️⃣ *Переходы* → между клипами → значок +\n"
                "3️⃣ *Ключевые кадры* → иконка ромб на шкале времени\n"
                "4️⃣ *Chroma key* → зелёный экран → Эффекты → Удалить фон\n"
                "5️⃣ *Экспорт* → всегда 1080p, 30fps\n\n"
                "📺 Плейлист CapCut RU: [YouTube](https://youtube.com/results?search_query=capcut+tutorial+ru)\n"
                "📺 Официальный канал: [CapCut](https://www.youtube.com/@CapCut)\n"
            ),
        },
        {
            **_KB[2],
            "title": "Маркетинговые Hooks",
            "text": (
                "*Формулы первых 3 секунд*\n\n"
                "❓ *Вопрос* — «А знаешь ли ты, что в нашей школе..?»\n"
                "😱 *Шок-факт* — «97% учеников не знают это правило»\n"
                "🤫 *Секрет* — «Мы покажем то, что обычно скрыто от камер»\n"
                "🏆 *Результат* — «Смотри, как 5А выиграли кубок с первого раза»\n"
                "⏱ *Таймер* — «За 60 секунд объясним, как работает редакция»\n\n"
                "✅ *Правило света (3-точечная схема):*\n"
                "• Key light — основной, 45° сбоку\n"
                "• Fill light — мягкий, убирает тени\n"
                "• Back light — отделяет от фона\n"
            ),
        },
        {
            **_KB[3],
            "title": "Чек-лист съёмки",
            "text": (
                "*Чек-лист перед выходом на съёмку*\n\n"
                "📱 Телефон заряжен > 80%\n"
                "💾 Свободно > 5 ГБ памяти\n"
                "🎙 Микрофон (петличка / стабилизатор)\n"
                "💡 Достаточно света (или кольцевая лампа)\n"
                "📋 Сценарий / вопросы для интервью готовы\n"
                "🔕 Режим «не беспокоить» включён\n"
                "📐 Горизонтальное видео для YouTube / вертикальное для Reels\n"
                "🎬 Снять 3+ дублей каждой сцены\n"
                "🔊 Проверить звук первых 10 секунд\n"
            ),
        },
    ],
    "pl": [
        {
            **_KB[0],
            "title": "Pojęcia medialne",
            "text": (
                "*Słowniczek Klasyk TV*\n\n"
                "🎬 *B-roll* — ujęcia tła bez osoby mówiącej\n"
                "🎙 *Stand-up* — prowadzący mówi prosto do kamery\n"
                "💡 *Hook* — pierwsze 3 sekundy, które zatrzymują widza\n"
                "✂️ *Cut* — twarde cięcie między dwoma ujęciami\n"
                "🔊 *Voice-over* — lektor / głos z offu\n"
                "📐 *Zasada trójpodziału* — główny obiekt na 1/3 kadru\n"
                "🎨 *Color grading* — korekcja i stylizacja kolorów\n"
                "📍 *Location* — miejsce nagrania\n"
                "🎯 *CTA* — Call To Action, wezwanie do działania\n"
                "📊 *Reach* — zasięg publikacji\n"
                "💬 *Engagement* — zaangażowanie (lajki+komentarze+udostępnienia)\n"
            ),
        },
        {
            **_KB[1],
            "title": "CapCut — poradniki",
            "text": (
                "*CapCut — szybki start*\n\n"
                "1️⃣ *Auto-napisy* → Tekst → Auto-napisy\n"
                "2️⃣ *Przejścia* → między klipami → ikonka +\n"
                "3️⃣ *Klatki kluczowe* → ikona rombu na osi czasu\n"
                "4️⃣ *Chroma key* → zielone tło → Efekty → Usuń tło\n"
                "5️⃣ *Eksport* → zawsze 1080p, 30 fps\n\n"
                "📺 Lista CapCut (PL): [YouTube](https://youtube.com/results?search_query=capcut+poradnik+pl)\n"
                "📺 Oficjalny kanał: [CapCut](https://www.youtube.com/@CapCut)\n"
            ),
        },
        {
            **_KB[2],
            "title": "Hooki marketingowe",
            "text": (
                "*Formuły pierwszych 3 sekund*\n\n"
                "❓ *Pytanie* — „Czy wiesz, że w naszej szkole…?”\n"
                "😱 *Szokujący fakt* — „97% uczniów nie zna tej zasady”\n"
                "🤫 *Sekret* — „Pokażemy coś, co zwykle zostaje poza kamerą”\n"
                "🏆 *Efekt końcowy* — „Zobacz, jak 5A wygrało puchar za pierwszym razem”\n"
                "⏱ *Timer* — „W 60 sekund wyjaśnimy, jak działa redakcja”\n\n"
                "✅ *Oświetlenie (schemat 3-punktowy):*\n"
                "• Key light — główne światło, 45° z boku\n"
                "• Fill light — wypełniające, zmiękcza cienie\n"
                "• Back light — odcina od tła\n"
            ),
        },
        {
            **_KB[3],
            "title": "Checklista nagrania",
            "text": (
                "*Checklista przed wyjściem na nagranie*\n\n"
                "📱 Telefon naładowany > 80%\n"
                "💾 Wolne miejsce > 5 GB\n"
                "🎙 Mikrofon (krawatowy / stabilizator)\n"
                "💡 Wystarczająco światła (lub ring)\n"
                "📋 Scenariusz / pytania do wywiadu gotowe\n"
                "🔕 Tryb „nie przeszkadzać” włączony\n"
                "📐 Poziomo na YouTube / pionowo na Reels\n"
                "🎬 Nagrać 3+ dubli każdej sceny\n"
                "🔊 Sprawdzić dźwięk w pierwszych 10 sekundach\n"
            ),
        },
    ],
}

# Fallback order when requested language isn't present in DB
KNOWLEDGE_LANG_FALLBACK_ORDER = ("en", "ru")


def get_specs(lang: str) -> list[str]:
    return SPECS_BY_LANG.get(lang) or SPECS_BY_LANG["en"]


def get_content_types(lang: str) -> list[str]:
    return CONTENT_TYPES_BY_LANG.get(lang) or CONTENT_TYPES_BY_LANG["en"]


def get_locations(lang: str) -> list[str]:
    return LOCATIONS_BY_LANG.get(lang) or LOCATIONS_BY_LANG["en"]

