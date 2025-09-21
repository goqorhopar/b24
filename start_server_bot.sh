#!/bin/bash

# Скрипт для запуска серверного бота

set -e

echo "🚀 Запуск Meeting Bot Server"

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env на основе .env.example"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден!"
    exit 1
fi

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install -r requirements_simple.txt

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p logs
mkdir -p temp
mkdir -p /tmp/meeting_bot

# Настройка аудиосистемы (если возможно)
echo "🔊 Настройка аудиосистемы..."
if command -v pactl &> /dev/null; then
    # Создание виртуального аудиоустройства
    pactl load-module module-null-sink sink_name=meeting_bot 2>/dev/null || true
    pactl load-module module-loopback source=meeting_bot.monitor sink=@DEFAULT_SINK@ 2>/dev/null || true
    pactl set-default-source meeting_bot.monitor 2>/dev/null || true
fi

# Запуск виртуального дисплея (если нужен)
echo "🖥️  Настройка виртуального дисплея..."
if command -v Xvfb &> /dev/null; then
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    export DISPLAY=:99
fi

# Проверка переменных окружения
echo "🔍 Проверка конфигурации..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY']
missing = []

for var in required_vars:
    if not os.getenv(var):
        missing.append(var)

if missing:
    print(f'❌ Отсутствуют переменные: {missing}')
    exit(1)
else:
    print('✅ Конфигурация корректна')
"

# Запуск бота
echo "🤖 Запуск Meeting Bot Server..."
python3 main_server_bot.py
