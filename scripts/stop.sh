#!/bin/bash

# Скрипт остановки Meeting Bot Assistant
# Автор: AI Assistant

set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

log "🛑 Остановка Meeting Bot Assistant..."

# Остановка контейнеров
log "Остановка Docker контейнеров..."
docker-compose down

# Остановка systemd сервиса (если запущен)
if systemctl is-active --quiet meeting-bot; then
    log "Остановка systemd сервиса..."
    sudo systemctl stop meeting-bot
fi

log "✅ Meeting Bot Assistant остановлен"
