#!/usr/bin/env bash
# ============================================================
#  Klasyk Bot — Полная изоляция
#
#  Переносит бота из /root/ (или любой папки) в изолированную
#  директорию с отдельным пользователем, жёсткими правами
#  и systemd-песочницей.
#
#  Запуск:  chmod +x isolate.sh && sudo ./isolate.sh
#
#  Что делает:
#   1. Создаёт системного пользователя без логина
#   2. Переносит проект в /opt/klasykbot/
#   3. Сохраняет .env, data/, logs/ если они есть
#   4. Ставит venv + зависимости
#   5. Закрывает права: 750 на папки, 640 на файлы, 600 на .env
#   6. Создаёт systemd-сервис с максимальной песочницей
#   7. Предлагает удалить старую копию
# ============================================================
set -euo pipefail

# ── Настройки ────────────────────────────────────────────────
BOT_USER="klasykbot"
BOT_GROUP="klasykbot"
INSTALL_DIR="/opt/klasykbot"
SERVICE_NAME="klasyk-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${INSTALL_DIR}/venv"
DATA_DIR="${INSTALL_DIR}/data"
LOGS_DIR="${INSTALL_DIR}/logs"
ENV_FILE="${INSTALL_DIR}/.env"

# Откуда копировать — каталог, где лежит этот скрипт
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Цвета ────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }
step()  { echo -e "\n${CYAN}${BOLD}── $* ──${NC}"; }

# ── Проверки ─────────────────────────────────────────────────
[ "$EUID" -eq 0 ] || error "Запусти от root:  sudo ./isolate.sh"

if [ ! -f "${SOURCE_DIR}/bot.py" ]; then
    error "bot.py не найден в ${SOURCE_DIR}. Запусти скрипт из папки бота."
fi

if [ "${SOURCE_DIR}" = "${INSTALL_DIR}" ]; then
    error "Бот уже в ${INSTALL_DIR}. Изоляция не нужна."
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    Klasyk Bot — Полная изоляция          ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Источник : ${SOURCE_DIR}"
echo "║  Цель     : ${INSTALL_DIR}"
echo "║  Юзер     : ${BOT_USER}"
echo "║  Сервис   : ${SERVICE_NAME}"
echo "╚══════════════════════════════════════════╝"
echo ""
read -rp "Продолжить? [y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { echo "Отменено."; exit 0; }

# ═══════════════════════════════════════════════════════════════
#  1. СИСТЕМНЫЕ ПАКЕТЫ
# ═══════════════════════════════════════════════════════════════
step "1/9  Системные пакеты"

apt-get update -qq 2>/dev/null || true
apt-get install -y -qq python3 python3-pip python3-venv rsync > /dev/null 2>&1
info "python3, pip, venv, rsync — готово."

# ═══════════════════════════════════════════════════════════════
#  2. СИСТЕМНЫЙ ПОЛЬЗОВАТЕЛЬ
# ═══════════════════════════════════════════════════════════════
step "2/9  Системный пользователь"

if id "$BOT_USER" &>/dev/null; then
    info "Пользователь ${BOT_USER} уже существует."
else
    useradd \
        --system \
        --shell /usr/sbin/nologin \
        --home-dir "$INSTALL_DIR" \
        --create-home \
        --comment "Klasyk Telegram Bot" \
        "$BOT_USER"
    info "Создан системный пользователь: ${BOT_USER} (без логина, без пароля)."
fi

# Заблокировать SSH-вход
if [ -f /etc/ssh/sshd_config ]; then
    if ! grep -q "^DenyUsers.*${BOT_USER}" /etc/ssh/sshd_config 2>/dev/null; then
        # Проверяем, есть ли уже строка DenyUsers
        if grep -q "^DenyUsers" /etc/ssh/sshd_config 2>/dev/null; then
            sed -i "s/^DenyUsers.*/& ${BOT_USER}/" /etc/ssh/sshd_config
        else
            echo "DenyUsers ${BOT_USER}" >> /etc/ssh/sshd_config
        fi
        systemctl reload sshd 2>/dev/null || true
        info "SSH-вход для ${BOT_USER} заблокирован."
    else
        info "SSH уже заблокирован для ${BOT_USER}."
    fi
fi

# ═══════════════════════════════════════════════════════════════
#  3. ОСТАНОВИТЬ СТАРЫЙ СЕРВИС
# ═══════════════════════════════════════════════════════════════
step "3/9  Остановка старого сервиса"

if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl stop "$SERVICE_NAME"
    info "Сервис ${SERVICE_NAME} остановлен."
elif systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    info "Сервис существует, но не запущен."
else
    info "Старый сервис не найден — чистая установка."
fi

# ═══════════════════════════════════════════════════════════════
#  4. ПЕРЕНОС ФАЙЛОВ
# ═══════════════════════════════════════════════════════════════
step "4/9  Перенос файлов"

mkdir -p "$INSTALL_DIR"

# Копируем код бота (без venv, data, logs, .git, кэша, .env)
rsync -a --delete \
    --exclude='venv/' \
    --exclude='data/' \
    --exclude='logs/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='klasyk.db' \
    --exclude='bot.lock' \
    --exclude='.env' \
    --exclude='isolate.sh' \
    --exclude='deploy.sh' \
    --exclude='install.sh' \
    "${SOURCE_DIR}/" "${INSTALL_DIR}/"

info "Код бота скопирован."

# Перенос данных (data/) — если есть в источнике и нет в цели
if [ -d "${SOURCE_DIR}/data" ] && [ ! -d "${DATA_DIR}" ]; then
    cp -a "${SOURCE_DIR}/data" "${DATA_DIR}"
    info "Данные (data/) перенесены."
elif [ -d "${DATA_DIR}" ]; then
    info "data/ уже существует в ${INSTALL_DIR} — не перезаписываю."
fi

# Перенос логов (logs/) — если есть в источнике и нет в цели
if [ -d "${SOURCE_DIR}/logs" ] && [ ! -d "${LOGS_DIR}" ]; then
    cp -a "${SOURCE_DIR}/logs" "${LOGS_DIR}"
    info "Логи (logs/) перенесены."
fi

# Перенос .env — если есть в источнике и нет в цели
if [ -f "${SOURCE_DIR}/.env" ] && [ ! -f "${ENV_FILE}" ]; then
    cp -a "${SOURCE_DIR}/.env" "${ENV_FILE}"
    info ".env перенесён."
elif [ -f "${ENV_FILE}" ]; then
    info ".env уже существует — не перезаписываю."
fi

# Перенос старой БД klasyk.db — если есть, положить рядом для ручной миграции
if [ -f "${SOURCE_DIR}/klasyk.db" ] && [ ! -f "${INSTALL_DIR}/klasyk.db" ]; then
    cp "${SOURCE_DIR}/klasyk.db" "${INSTALL_DIR}/klasyk.db"
    warn "Старая БД klasyk.db скопирована для ручной миграции."
fi

# Удалить Python-кэш в целевой папке
find "${INSTALL_DIR}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${INSTALL_DIR}" -name '*.pyc' -delete 2>/dev/null || true
info "Python-кэш очищен."

# Создать рабочие каталоги
mkdir -p "${DATA_DIR}" "${LOGS_DIR}"

# ═══════════════════════════════════════════════════════════════
#  5. .env ФАЙЛ
# ═══════════════════════════════════════════════════════════════
step "5/9  Конфигурация (.env)"

if [ ! -f "${ENV_FILE}" ]; then
    cat > "${ENV_FILE}" << 'ENVEOF'
# ── Klasyk Bot — Настройки ──
# Токен бота от @BotFather
BOT_TOKEN=

# ID группы администраторов (отрицательное число)
ADMIN_GROUP_ID=0

# ID администраторов через запятую
ADMIN_IDS=
ENVEOF
    warn "Создан шаблон ${ENV_FILE} — ЗАПОЛНИ перед запуском!"
else
    info ".env уже заполнен."
fi

# ═══════════════════════════════════════════════════════════════
#  6. ВИРТУАЛЬНОЕ ОКРУЖЕНИЕ
# ═══════════════════════════════════════════════════════════════
step "6/9  Виртуальное окружение + зависимости"

# Права на install_dir ДО создания venv (нужны для sudo -u)
chown -R "${BOT_USER}:${BOT_GROUP}" "${INSTALL_DIR}"

if [ ! -d "$VENV_DIR" ]; then
    sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
    info "Создано виртуальное окружение."
else
    info "venv уже существует."
fi

sudo -u "$BOT_USER" "${VENV_DIR}/bin/pip" install --upgrade pip -q 2>/dev/null
sudo -u "$BOT_USER" "${VENV_DIR}/bin/pip" install -r "${INSTALL_DIR}/requirements.txt" -q 2>/dev/null
info "Зависимости установлены."

# ═══════════════════════════════════════════════════════════════
#  7. ПРАВА ДОСТУПА
# ═══════════════════════════════════════════════════════════════
step "7/9  Права доступа"

# Владелец — bot user
chown -R "${BOT_USER}:${BOT_GROUP}" "${INSTALL_DIR}"

# Директории: rwxr-x--- (750) — читать может только владелец и группа
find "${INSTALL_DIR}" -type d -exec chmod 750 {} +

# Файлы: rw-r----- (640) — код доступен группе (для отладки)
find "${INSTALL_DIR}" -type f -exec chmod 640 {} +

# Python в venv должен быть исполняемым
find "${VENV_DIR}/bin" -type f -exec chmod 750 {} + 2>/dev/null || true

# .env — только владелец (600)
chmod 600 "${ENV_FILE}"

# start.sh — исполняемый
[ -f "${INSTALL_DIR}/start.sh" ] && chmod 750 "${INSTALL_DIR}/start.sh"

info "Права:"
info "  Директории: 750 (rwxr-x---)"
info "  Файлы:      640 (rw-r-----)"
info "  .env:        600 (rw-------)"
info "  Владелец:   ${BOT_USER}:${BOT_GROUP}"

# ═══════════════════════════════════════════════════════════════
#  8. SYSTEMD СЕРВИС С ПОЛНОЙ ПЕСОЧНИЦЕЙ
# ═══════════════════════════════════════════════════════════════
step "8/9  Systemd сервис"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Klasyk Telegram Bot
Documentation=https://github.com/your-repo/klasyk-bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_GROUP}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${VENV_DIR}/bin/python bot.py
Restart=on-failure
RestartSec=15

# ── Переменные ──
EnvironmentFile=${ENV_FILE}
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=PYTHONUNBUFFERED=1

# ── Логирование ──
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

# ── Лимиты ресурсов ──
# Макс 512 МБ RAM (бот не должен жрать больше)
MemoryMax=512M
MemoryHigh=384M
# Макс 25% CPU
CPUQuota=25%
# Макс 1024 открытых файлов
LimitNOFILE=1024
# Макс 64 процесса/потока
TasksMax=64

# ══════════════════════════════════════════════════════════════
#  ПЕСОЧНИЦА (Sandbox)
# ══════════════════════════════════════════════════════════════

# -- Файловая система --
# Вся FS read-only, кроме явно разрешённых путей
ProtectSystem=strict
ReadWritePaths=${DATA_DIR} ${LOGS_DIR}
# Закрыть /home, /root, /run/user
ProtectHome=yes
# Приватный /tmp (не виден другим процессам)
PrivateTmp=yes
# Запретить монтирование новых FS
ProtectControlGroups=yes
# /dev — только /dev/null, /dev/zero, /dev/random
PrivateDevices=yes
# Запретить запись в /proc и /sys
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
# /proc видит только свои процессы
ProtectProc=invisible
ProcSubset=pid
# Запретить изменение hostname
ProtectHostname=yes
ProtectClock=yes

# -- Сеть --
# Только IPv4/IPv6 (без raw сокетов, netlink и т.д.)
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
# Запретить создание сетевых namespace
RestrictNamespaces=yes

# -- Привилегии --
# Запретить получение новых привилегий (suid, capabilities)
NoNewPrivileges=yes
# Убрать ВСЕ capabilities
CapabilityBoundingSet=
AmbientCapabilities=
# Запретить suid/sgid биты
RestrictSUIDSGID=yes
# Запретить запись+исполнение в одной области памяти
MemoryDenyWriteExecute=yes
# Запретить изменение realtime-приоритета
RestrictRealtime=yes
# Разрешить только необходимые системные вызовы
SystemCallArchitectures=native
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources @mount @swap @reboot @raw-io @clock @cpu-emulation @debug @obsolete @module
# Убрать KEYRING
KeyringMode=private
# Lock personality (no compat mode)
LockPersonality=yes

# -- Маскируем ненужные каталоги --
InaccessiblePaths=/boot
ReadOnlyPaths=/etc
TemporaryFileSystem=/var:ro
BindReadOnlyPaths=/var/run/dbus

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}" > /dev/null 2>&1
info "Сервис ${SERVICE_NAME} создан и включён."
info "Песочница: strict FS, ограниченные syscalls, лимиты RAM/CPU."

# ═══════════════════════════════════════════════════════════════
#  9. ОЧИСТКА СТАРОЙ КОПИИ
# ═══════════════════════════════════════════════════════════════
step "9/9  Очистка"

echo ""
warn "Старая копия бота находится в:"
echo "    ${SOURCE_DIR}"
echo ""
read -rp "Удалить старую копию? [y/N] " del_confirm
if [[ "$del_confirm" =~ ^[Yy]$ ]]; then
    # Безопасная проверка — не удаляем / или /root целиком
    if [ "${#SOURCE_DIR}" -lt 5 ]; then
        warn "Путь слишком короткий (${SOURCE_DIR}). Удали вручную."
    else
        rm -rf "${SOURCE_DIR}"
        info "Старая копия удалена: ${SOURCE_DIR}"
    fi
else
    info "Старая копия оставлена: ${SOURCE_DIR}"
fi

# ═══════════════════════════════════════════════════════════════
#  ИТОГ
# ═══════════════════════════════════════════════════════════════
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          Изоляция завершена!                     ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║                                                  ║"
echo "║  Пользователь : ${BOT_USER} (системный, без логина)"
echo "║  Проект       : ${INSTALL_DIR}/"
echo "║  Данные       : ${DATA_DIR}/"
echo "║  Логи         : ${LOGS_DIR}/"
echo "║  Конфиг       : ${ENV_FILE}"
echo "║  Сервис       : ${SERVICE_NAME}"
echo "║                                                  ║"
echo "╠══════════════════════════════════════════════════╣"
echo "║  Защита:                                         ║"
echo "║  • Отдельный системный юзер без shell/SSH        ║"
echo "║  • Файлы 640, папки 750, .env 600                ║"
echo "║  • ProtectSystem=strict (FS read-only)           ║"
echo "║  • PrivateTmp, PrivateDevices                    ║"
echo "║  • NoNewPrivileges, CapabilityBoundingSet=       ║"
echo "║  • SystemCallFilter (только @system-service)     ║"
echo "║  • MemoryMax=512M, CPUQuota=25%                  ║"
echo "║  • Защита ядра, clock, hostname                  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Проверить, заполнен ли .env
if grep -qE '^BOT_TOKEN=.+' "${ENV_FILE}" 2>/dev/null; then
    info ".env заполнен. Можно запускать:"
    echo ""
    echo "    sudo systemctl start ${SERVICE_NAME}"
    echo "    journalctl -u ${SERVICE_NAME} -f"
else
    warn ".env НЕ ЗАПОЛНЕН. Перед запуском:"
    echo ""
    echo "    sudo nano ${ENV_FILE}"
    echo ""
    echo "  Затем:"
    echo "    sudo systemctl start ${SERVICE_NAME}"
    echo "    journalctl -u ${SERVICE_NAME} -f"
fi

echo ""
info "Полезные команды:"
echo "    sudo systemctl status ${SERVICE_NAME}     # статус"
echo "    sudo systemctl restart ${SERVICE_NAME}    # перезапуск"
echo "    sudo systemctl stop ${SERVICE_NAME}       # остановка"
echo "    journalctl -u ${SERVICE_NAME} -n 50       # последние 50 строк лога"
echo "    sudo -u ${BOT_USER} ls ${DATA_DIR}/       # посмотреть данные"
echo ""
