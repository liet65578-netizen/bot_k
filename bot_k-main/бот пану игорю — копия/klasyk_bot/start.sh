#!/usr/bin/env bash
# ============================================================
#  Klasyk Bot — Управление ботом
#  Использование:  ./start.sh [команда]
#
#  Команды:
#    start    — запустить бот
#    stop     — остановить бот
#    restart  — перезапустить бот
#    status   — показать статус
#    logs     — показать логи (live)
#    update   — обновить зависимости и перезапустить
# ============================================================
set -euo pipefail

SERVICE_NAME="klasyk-bot"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; exit 1; }

# ── Проверки ─────────────────────────────────────────────────
check_env() {
    if [ ! -f "${SCRIPT_DIR}/.env" ]; then
        error ".env файл не найден! Сначала запусти install.sh"
    fi
    # Проверяем что BOT_TOKEN заполнен
    if ! grep -qE '^BOT_TOKEN=.+' "${SCRIPT_DIR}/.env"; then
        error "BOT_TOKEN не заполнен в .env! Заполни: nano ${SCRIPT_DIR}/.env"
    fi
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        error "Виртуальное окружение не найдено! Сначала запусти: sudo ./install.sh"
    fi
}

# ── Команды ──────────────────────────────────────────────────
cmd_start() {
    check_env
    check_venv
    info "Запускаю ${SERVICE_NAME}..."
    sudo systemctl start "$SERVICE_NAME"
    sleep 1
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        info "Бот запущен!"
    else
        error "Не удалось запустить. Смотри логи: ./start.sh logs"
    fi
}

cmd_stop() {
    info "Останавливаю ${SERVICE_NAME}..."
    sudo systemctl stop "$SERVICE_NAME"
    info "Бот остановлен."
}

cmd_restart() {
    check_env
    check_venv
    info "Перезапускаю ${SERVICE_NAME}..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep 1
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        info "Бот перезапущен!"
    else
        error "Не удалось перезапустить. Смотри логи: ./start.sh logs"
    fi
}

cmd_status() {
    echo ""
    systemctl status "$SERVICE_NAME" --no-pager || true
    echo ""
}

cmd_logs() {
    journalctl -u "$SERVICE_NAME" -f --no-pager
}

cmd_update() {
    check_venv
    info "Обновляю зависимости..."
    "${VENV_DIR}/bin/pip" install -r "${SCRIPT_DIR}/requirements.txt" -q
    info "Зависимости обновлены."
    cmd_restart
}

# ── Главное меню ─────────────────────────────────────────────
show_help() {
    echo ""
    echo "  Klasyk Bot — Управление"
    echo "  ───────────────────────"
    echo "  ./start.sh start    — запустить бот"
    echo "  ./start.sh stop     — остановить бот"
    echo "  ./start.sh restart  — перезапустить бот"
    echo "  ./start.sh status   — показать статус"
    echo "  ./start.sh logs     — показать логи (live)"
    echo "  ./start.sh update   — обновить зависимости + рестарт"
    echo ""
}

case "${1:-help}" in
    start)   cmd_start   ;;
    stop)    cmd_stop     ;;
    restart) cmd_restart  ;;
    status)  cmd_status   ;;
    logs)    cmd_logs     ;;
    update)  cmd_update   ;;
    *)       show_help    ;;
esac
