#!/bin/bash

echo "🚀 ДЕПЛОЙ АВТОНОМНОГО СЕРВЕРНОГО БОТА"
echo "======================================"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт от имени root: sudo $0"
    exit 1
fi

# Определение путей
BOT_DIR="/root/b24"
SERVICE_FILE="meeting-bot-autonomous.service"
BOT_SCRIPT="autonomous_server_bot.py"
LOGS_DIR="$BOT_DIR/logs"

echo "📁 Создание директорий..."
mkdir -p "$BOT_DIR"
mkdir -p "$LOGS_DIR"

echo "📋 Копирование файлов..."
cp "$BOT_SCRIPT" "$BOT_DIR/"
cp "$SERVICE_FILE" "/etc/systemd/system/"

echo "🔧 Установка зависимостей..."
pip3 install requests google-generativeai

echo "⚙️ Настройка systemd сервиса..."
systemctl daemon-reload
systemctl enable meeting-bot-autonomous.service

echo "🛑 Остановка старых процессов..."
systemctl stop meeting-bot-autonomous.service 2>/dev/null || true
pkill -f "autonomous_server_bot.py" 2>/dev/null || true

echo "🚀 Запуск автономного бота..."
systemctl start meeting-bot-autonomous.service

echo "⏳ Ожидание запуска..."
sleep 5

echo "📊 Проверка статуса..."
systemctl status meeting-bot-autonomous.service --no-pager

echo ""
echo "✅ АВТОНОМНЫЙ БОТ РАЗВЕРНУТ!"
echo "=========================="
echo "📱 Бот работает автоматически на сервере"
echo "🔄 Автоматический перезапуск при сбоях"
echo "🚀 Автоматический запуск при перезагрузке"
echo ""
echo "📋 Команды управления:"
echo "  systemctl status meeting-bot-autonomous.service  # Статус"
echo "  systemctl restart meeting-bot-autonomous.service  # Перезапуск"
echo "  journalctl -u meeting-bot-autonomous.service -f   # Логи"
echo "  systemctl stop meeting-bot-autonomous.service     # Остановка"
echo ""
echo "🎯 БОТ РАБОТАЕТ БЕЗ ВАШЕГО УЧАСТИЯ!"
