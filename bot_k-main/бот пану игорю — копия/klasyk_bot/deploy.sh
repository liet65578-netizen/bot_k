#!/usr/bin/env bash
# ============================================================
#  Klasyk Bot — Полная установка с изоляцией
#  Создаёт пользователя, копирует проект, настраивает сервис
#
#  Запуск:  chmod +x deploy.sh && sudo ./deploy.sh
# ============================================================
set -euo pipefail

# ── Настройки ────────────────────────────────────────────────
BOT_USER="klasykbot"
BOT_HOME="/home/${BOT_USER}"
BOT_DIR="${BOT_HOME}/bot"
SERVICE_NAME="klasyk-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${BOT_DIR}/venv"

# Папка, откуда копировать файлы бота (где лежит этот скрипт)
SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Проверка root ────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    error "Запусти от root:  sudo ./deploy.sh"
fi

echo ""
echo "======================================"
echo "  Klasyk Bot — Deploy"
echo "======================================"
echo ""

# ── 1. Системные пакеты ─────────────────────────────────────
info "Устанавливаю системные пакеты..."
apt-get update -qq 2>/dev/null || true
apt-get install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1
info "Python3 + venv готовы."

# ── 2. Создать пользователя ─────────────────────────────────
if id "$BOT_USER" &>/dev/null; then
    info "Пользователь ${BOT_USER} уже существует."
else
    adduser --disabled-password --gecos "Klasyk Telegram Bot" "$BOT_USER"
    info "Создан пользователь: ${BOT_USER}"
fi

# ── 3. Остановить старый сервис если есть ────────────────────
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    systemctl stop "$SERVICE_NAME"
    info "Остановлен старый сервис."
fi

# ── 4. Скопировать файлы бота ────────────────────────────────
mkdir -p "$BOT_DIR"

# Копируем всё кроме venv, data, __pycache__, .git
rsync -a --delete \
    --exclude='venv/' \
    --exclude='data/' \
    --exclude='logs/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='klasyk.db' \
    --exclude='bot.lock' \
    --exclude='.env' \
    "${SOURCE_DIR}/" "${BOT_DIR}/"

# Удалить кэши Python на сервере (чтобы старый код не использовался)
find "${BOT_DIR}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
find "${BOT_DIR}" -name '*.pyc' -delete 2>/dev/null || true

info "Файлы скопированы: ${SOURCE_DIR} → ${BOT_DIR}"

# ── 5. Создать рабочие директории ────────────────────────────
mkdir -p "${BOT_DIR}/data"
mkdir -p "${BOT_DIR}/logs"

# ── 6. Права (ДО создания venv) ─────────────────────────────
chown -R "${BOT_USER}:${BOT_USER}" "$BOT_HOME"
info "Права выставлены: всё принадлежит ${BOT_USER}"

# ── 7. Виртуальное окружение ─────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    sudo -u "$BOT_USER" python3 -m venv "$VENV_DIR"
    info "Создано виртуальное окружение."
else
    info "Виртуальное окружение уже существует."
fi

sudo -u "$BOT_USER" "${VENV_DIR}/bin/pip" install --upgrade pip -q
sudo -u "$BOT_USER" "${VENV_DIR}/bin/pip" install -r "${BOT_DIR}/requirements.txt" -q
info "Зависимости установлены."

# ── 7. Файл .env ────────────────────────────────────────────
ENV_FILE="${BOT_DIR}/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'ENVEOF'
# ── Klasyk Bot — Настройки ──
# Токен бота от @BotFather
BOT_TOKEN=

# ID группы администраторов (отрицательное число)
ADMIN_GROUP_ID=0

# ID администраторов через запятую
ADMIN_IDS=
ENVEOF
    chmod 600 "$ENV_FILE"
    warn "Создан ${ENV_FILE} — ЗАПОЛНИ его перед запуском!"
else
    info ".env уже существует, не перезаписываю."
fi

# ── 9. Финальные права ───────────────────────────────────────
chown -R "${BOT_USER}:${BOT_USER}" "$BOT_HOME"

# ── 10. Systemd-сервис с изоляцией ──────────────────────────
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Klasyk Telegram Bot
After=network.target

[Service]
Type=simple
User=${BOT_USER}
Group=${BOT_USER}
WorkingDirectory=${BOT_DIR}
ExecStart=${VENV_DIR}/bin/python bot.py
Restart=always
RestartSec=10
EnvironmentFile=${ENV_FILE}

# Логи
StandardOutput=journal
StandardError=journal

# Изоляция
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=${BOT_DIR}/data ${BOT_DIR}/logs
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
info "Сервис создан: ${SERVICE_NAME}"

# ── 10. Итог ─────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  Установка завершена!"
echo "======================================"
echo ""
echo "  Пользователь:  ${BOT_USER}"
echo "  Проект:         ${BOT_DIR}"
echo "  Данные:         ${BOT_DIR}/data/"
echo "  Логи:           ${BOT_DIR}/logs/"
echo "  Сервис:         ${SERVICE_NAME}"
echo ""
info "Следующие шаги:"
echo ""
echo "  1. Заполни .env:"
echo "     sudo -u ${BOT_USER} nano ${ENV_FILE}"
echo ""
echo "  2. Запусти бот:"
echo "     sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "  3. Проверь статус:"
echo "     sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "  4. Смотри логи:"
echo "     journalctl -u ${SERVICE_NAME} -f"
echo ""
