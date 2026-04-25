#!/usr/bin/env bash
# ============================================================
#  Klasyk Bot — Автоматический установщик для Ubuntu/Debian
#  Запуск:  chmod +x install.sh && sudo ./install.sh
# ============================================================
set -euo pipefail

# ── Цвета ────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Проверка root ────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    error "Запусти от root:  sudo ./install.sh"
fi

# ── Определяем рабочую директорию (где лежит этот скрипт) ────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$SCRIPT_DIR"
SERVICE_NAME="klasyk-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${BOT_DIR}/venv"
RUN_USER="${SUDO_USER:-root}"

echo ""
echo "======================================"
echo "  Klasyk Bot — Установка"
echo "======================================"
echo ""
info "Директория бота: ${BOT_DIR}"
info "Пользователь:    ${RUN_USER}"
echo ""

# ── 1. Системные пакеты ─────────────────────────────────────
info "Обновляю список пакетов..."
apt-get update -qq

info "Устанавливаю python3, pip, venv..."
apt-get install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1

# ── 2. Виртуальное окружение ─────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    info "Создаю виртуальное окружение..."
    python3 -m venv "$VENV_DIR"
else
    info "Виртуальное окружение уже существует."
fi

info "Устанавливаю зависимости..."
"${VENV_DIR}/bin/pip" install --upgrade pip -q
"${VENV_DIR}/bin/pip" install -r "${BOT_DIR}/requirements.txt" -q
info "Зависимости установлены."

# ── 3. Файл .env ────────────────────────────────────────────
ENV_FILE="${BOT_DIR}/.env"
if [ ! -f "$ENV_FILE" ]; then
    warn ".env файл не найден — создаю шаблон..."
    cat > "$ENV_FILE" << 'ENVEOF'
# ── Klasyk Bot — Настройки ──
# Токен бота от @BotFather
BOT_TOKEN=

# ID группы администраторов (отрицательное число)
ADMIN_GROUP_ID=0

# ID администраторов через запятую
ADMIN_IDS=
ENVEOF
    chown "$RUN_USER":"$RUN_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    warn "Заполни ${ENV_FILE} перед запуском!"
    echo ""
else
    info ".env файл уже существует."
fi

# ── 4. Systemd-сервис ───────────────────────────────────────
info "Создаю systemd-сервис: ${SERVICE_NAME}..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Klasyk Telegram Bot
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${BOT_DIR}
ExecStart=${VENV_DIR}/bin/python bot.py
Restart=always
RestartSec=10
EnvironmentFile=${ENV_FILE}

# Логи в journalctl
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" > /dev/null 2>&1
info "Сервис ${SERVICE_NAME} создан и включён в автозагрузку."

# ── 5. Права ─────────────────────────────────────────────────
chown -R "$RUN_USER":"$RUN_USER" "$BOT_DIR"

# ── Готово ───────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  Установка завершена!"
echo "======================================"
echo ""
info "Следующие шаги:"
echo "  1. Заполни .env файл:     nano ${ENV_FILE}"
echo "  2. Запусти бот:           ./start.sh start"
echo "  3. Проверь статус:        ./start.sh status"
echo "  4. Смотри логи:           ./start.sh logs"
echo ""
