#!/bin/bash

# ===========================================
# БЫСТРЫЙ ДЕПЛОЙ MEETING BOT
# ===========================================

set -e

echo "🚀 Начинаю быстрый деплой Meeting Bot..."

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python3."
    exit 1
fi

# Проверяем наличие git
if ! command -v git &> /dev/null; then
    echo "❌ Git не найден. Установите Git."
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "📋 Скопируйте env_example.txt в .env и заполните настройки:"
    echo "   cp env_example.txt .env"
    echo "   nano .env"
    exit 1
fi

# Проверяем обязательные переменные
echo "🔍 Проверяю конфигурацию..."

if ! grep -q "TELEGRAM_BOT_TOKEN=" .env || grep -q "TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен в .env"
    exit 1
fi

if ! grep -q "GEMINI_API_KEY=" .env || grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "❌ GEMINI_API_KEY не настроен в .env"
    exit 1
fi

echo "✅ Конфигурация проверена"

# Коммит и пуш в GitHub
echo "📤 Отправляю изменения в GitHub..."
python3 auto_deploy.py --commit

if [ $? -eq 0 ]; then
    echo "✅ Изменения отправлены в GitHub"
else
    echo "❌ Ошибка отправки в GitHub"
    exit 1
fi

# Деплой на сервер
echo "🖥️ Деплою на сервер..."
python3 auto_deploy.py --deploy

if [ $? -eq 0 ]; then
    echo "✅ Деплой на сервер завершен"
else
    echo "❌ Ошибка деплоя на сервер"
    exit 1
fi

echo ""
echo "🎉 Быстрый деплой завершен успешно!"
echo ""
echo "📋 Что было сделано:"
echo "   ✅ Изменения отправлены в GitHub"
echo "   ✅ Код развернут на сервере"
echo "   ✅ Сервис перезапущен"
echo ""
echo "🔍 Для проверки статуса сервиса:"
echo "   ssh user@server 'systemctl status meeting-bot'"
echo ""
echo "📋 Для просмотра логов:"
echo "   ssh user@server 'journalctl -u meeting-bot -f'"
