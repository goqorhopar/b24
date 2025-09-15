#!/bin/bash

# Скрипт для деплоя бота на VPS через GitHub Actions
# Этот скрипт будет выполняться на VPS при деплое

set -e  # Останавливаем выполнение при ошибке

echo "🚀 Начинаем деплой бота на VPS..."

# Определяем директорию проекта
PROJECT_DIR="/opt/telegram-bot"
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="/home/$USER/telegram-bot"
fi
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="$HOME/telegram-bot"
fi

echo "📁 Рабочая директория: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Останавливаем бота
echo "⏹️ Останавливаем бота..."
sudo systemctl stop telegram-bot 2>/dev/null || pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Получаем последние изменения из GitHub
echo "📥 Получаем последние изменения..."
git fetch origin
git reset --hard origin/main
git clean -fd

# Создаем виртуальное окружение если не существует
if [ ! -d "venv" ]; then
    echo "🐍 Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip
echo "⬆️ Обновляем pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# Настраиваем переменные окружения
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "⚙️ Создаем файл .env из .env.example..."
    cp .env.example .env
    echo "⚠️ Не забудьте настроить переменные в файле .env!"
fi

# Проверяем конфигурацию
echo "🔍 Проверяем конфигурацию..."
python3 -c "
import sys
sys.path.append('.')
try:
    from config import *
    print('✅ Конфигурация загружена успешно')
except Exception as e:
    print(f'❌ Ошибка в конфигурации: {e}')
    sys.exit(1)
"

# Создаем systemd сервис если не существует
if [ ! -f "/etc/systemd/system/telegram-bot.service" ]; then
    echo "🔧 Создаем systemd сервис..."
    sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable telegram-bot
fi

# Запускаем бота
echo "▶️ Запускаем бота..."
sudo systemctl start telegram-bot

# Проверяем статус
sleep 3
if sudo systemctl is-active --quiet telegram-bot; then
    echo "✅ Бот успешно запущен!"
    echo "📊 Статус сервиса:"
    sudo systemctl status telegram-bot --no-pager -l
else
    echo "❌ Ошибка при запуске бота!"
    echo "📋 Логи сервиса:"
    sudo journalctl -u telegram-bot --no-pager -l --since "1 minute ago"
    exit 1
fi

echo "🎉 Деплой завершен успешно!"
echo "📝 Для просмотра логов используйте: sudo journalctl -u telegram-bot -f"
