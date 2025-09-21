#!/bin/bash

# 🚀 Быстрый запуск бота на сервере

echo "🤖 Запуск Telegram бота на сервере..."
echo "=================================="

# Проверяем, что мы на Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ ОШИБКА: Этот скрипт должен запускаться на Linux сервере!"
    echo "   Текущая ОС: $OSTYPE"
    exit 1
fi

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Устанавливаем..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

# Проверяем зависимости
echo "📦 Проверяем зависимости..."
pip3 install -r requirements.txt

# Проверяем .env файл
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "   Создайте файл .env с настройками бота"
    exit 1
fi

# Останавливаем старые процессы
echo "🛑 Останавливаем старые процессы..."
pkill -f "python.*start_bot"
pkill -f "python.*main"

# Запускаем бота
echo "🚀 Запускаем бота..."
nohup python3 start_bot_fixed.py > bot.log 2>&1 &

# Ждем немного
sleep 3

# Проверяем, что бот запустился
if pgrep -f "python.*start_bot" > /dev/null; then
    echo "✅ Бот успешно запущен!"
    echo "📋 PID процесса: $(pgrep -f "python.*start_bot")"
    echo "📄 Логи: tail -f bot.log"
    echo ""
    echo "🧪 Тестирование:"
    echo "   1. Найдите бота: @TranscriptionleadBot"
    echo "   2. Отправьте: /start"
    echo "   3. Отправьте ссылку на встречу"
else
    echo "❌ Бот не запустился. Проверьте логи:"
    echo "   tail -f bot.log"
    exit 1
fi

echo "=================================="
echo "🎉 Бот готов к работе!"
