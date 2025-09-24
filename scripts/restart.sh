#!/bin/bash

# Скрипт перезапуска Meeting Bot Assistant
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

log "🔄 Перезапуск Meeting Bot Assistant..."

# Остановка
log "Остановка сервисов..."
./scripts/stop.sh

# Небольшая пауза
sleep 3

# Запуск
log "Запуск сервисов..."
./scripts/start.sh

log "✅ Meeting Bot Assistant перезапущен"
