#!/bin/bash

# Скрипт запуска Meeting Bot Assistant
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

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker и повторите попытку."
fi

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен. Установите Docker Compose и повторите попытку."
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    error "Файл .env не найден. Создайте его на основе env.example"
fi

# Проверка обязательных переменных
source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    error "TELEGRAM_BOT_TOKEN не настроен в .env файле"
fi

if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your_gemini_api_key_here" ]; then
    error "GEMINI_API_KEY не настроен в .env файле"
fi

if [ -z "$BITRIX_WEBHOOK_URL" ] || [ "$BITRIX_WEBHOOK_URL" = "your_bitrix_webhook_url_here" ]; then
    error "BITRIX_WEBHOOK_URL не настроен в .env файле"
fi

log "Проверка конфигурации завершена"

# Создание необходимых директорий
log "Создание директорий..."
mkdir -p logs data/audio tmp recordings ssl

# Остановка существующих контейнеров
log "Остановка существующих контейнеров..."
docker-compose down --remove-orphans || true

# Очистка старых образов
log "Очистка старых образов..."
docker system prune -f || true

# Сборка образов
log "Сборка Docker образов..."
docker-compose build --no-cache

# Запуск сервисов
log "Запуск сервисов..."
docker-compose up -d

# Ожидание запуска
log "Ожидание запуска сервисов..."
sleep 10

# Проверка статуса
log "Проверка статуса контейнеров..."
docker-compose ps

# Проверка здоровья
log "Проверка здоровья сервиса..."
for i in {1..30}; do
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        log "✅ Сервис запущен и работает!"
        break
    fi
    if [ $i -eq 30 ]; then
        error "❌ Сервис не отвечает на health check"
    fi
    sleep 2
done

# Показать логи
log "Последние логи:"
docker-compose logs --tail=20

echo ""
log "🎉 Meeting Bot Assistant успешно запущен!"
echo ""
echo "📊 Статус:"
echo "- HTTP API: http://localhost:3000"
echo "- Health Check: http://localhost:3000/health"
echo "- Логи: docker-compose logs -f"
echo "- Остановка: docker-compose down"
echo ""
echo "🤖 Бот готов к работе в Telegram!"
