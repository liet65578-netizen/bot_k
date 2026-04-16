# 🎥 Klasyk Media Hub — Telegram Bot

Бот для управления школьной редакцией: регистрация участников, приём контента, план съёмок и база знаний.

---

## 📁 Структура проекта

```
klasyk_bot/
│
├── bot.py                  # Точка запуска
├── config.py               # Токены, списки классов, специализации, база знаний
├── database.py             # SQLite — все операции с данными
├── requirements.txt        # Зависимости Python
├── .env.example            # Шаблон переменных окружения
├── klasyk.db               # БД (создаётся автоматически при запуске)
│
└── handlers/
    ├── __init__.py
    ├── main_menu.py        # /start, главная клавиатура, роутинг
    ├── registration.py     # 🎥 Хочу в команду!
    ├── content.py          # 📥 Предложить контент
    ├── schedule.py         # 📅 План съёмок
    ├── knowledge.py        # 📚 База знаний
    └── profile.py          # 👤 Мой профиль
```

---

## 🚀 Быстрый старт

### 1. Создай бота у @BotFather
```
/newbot
→ Имя: Klasyk Media Hub
→ Username: klasyk_media_bot (или любой свободный)
→ Скопируй токен
```

### 2. Установи Python 3.11+
Скачай с [python.org](https://python.org) или используй системный пакетный менеджер.

### 3. Установи зависимости
```bash
cd klasyk_bot
pip install -r requirements.txt
```

### 4. Настрой .env
```bash
cp .env.example .env
# Открой .env в редакторе и заполни:
# BOT_TOKEN=токен_от_botfather
# ADMIN_GROUP_ID=ID_твоей_группы
# MAIN_ADMIN_ID=твой_telegram_ID
```

**Как узнать ID группы:**
1. Создай группу «Klasyk TV Admin»
2. Добавь в неё бота и сделай его администратором
3. Добавь @userinfobot в группу → он напишет ID (отрицательное число)
4. Вставь в ADMIN_GROUP_ID

### 5. Запусти бота
```bash
python bot.py
```

---

## ⚙️ Настройка под свою школу

### Добавить/изменить классы
В `config.py`, массив `CLASSES`:
```python
CLASSES = ["1A", "1B", "2A", ...] 
```

### Добавить мероприятия в план съёмок
Прямо в БД `klasyk.db` через любой SQLite-редактор (например DB Browser for SQLite):
```sql
INSERT INTO schedule_events (title, date_str, time_str, location, description)
VALUES ('🏆 Финал КВН', '05.05.2026', '17:00', 'Актовый зал', 'Нужны 2 оператора');
```

Или отредактируй функцию `_seed_demo_events()` в `database.py`.

### Изменить материалы базы знаний
В `config.py`, массив `KNOWLEDGE_ITEMS` — редактируй поле `"text"` для каждого раздела.

---

## 🗃️ Структура базы данных

| Таблица | Назначение |
|---|---|
| `users` | Зарегистрированные участники |
| `content_submissions` | Все присланные материалы |
| `schedule_events` | Мероприятия для съёмок |
| `signups` | Записи участников на события |

---

## 📊 Просмотр данных

Используй **DB Browser for SQLite** (бесплатно):
- Скачай: https://sqlitebrowser.org
- Открой файл `klasyk.db`

Полезные запросы:
```sql
-- Все участники команды
SELECT full_name, class_name, specs FROM users;

-- Новые заявки на контент
SELECT * FROM content_submissions WHERE status='new';

-- Кто записался на конкретное мероприятие
SELECT u.full_name, u.class_name
FROM signups s JOIN users u ON s.telegram_id = u.telegram_id
WHERE s.event_id = 1;
```

---

## 🔧 Возможные расширения

- **Google Sheets** — замени SQLite-функции в `database.py` на `gspread` для синхронизации
- **Напоминания** — добавь `JobQueue` для уведомлений перед событиями
- **Роли** — расширь поле `status` в таблице users: `editor`, `operator`, `admin`
- **Статистика** — команда `/stats` для подсчёта участников по специализациям

---

## ❓ Команды бота

| Команда | Действие |
|---|---|
| `/start` | Приветствие + главное меню |
| `/menu` | Показать главное меню |
| `/cancel` | Отменить текущий диалог |

---

## 🐛 Частые ошибки

**`Forbidden: bot was blocked by the user`** — пользователь заблокировал бота, это нормально.

**`Bad Request: chat not found`** — неверный ADMIN_GROUP_ID. Проверь что бот добавлен в группу как администратор.

**`ModuleNotFoundError`** — запусти `pip install -r requirements.txt` ещё раз.
