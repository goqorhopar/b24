#!/bin/bash

# Простой скрипт деплоя для VPS
# Запускать на VPS

set -e

echo "🚀 Начинаем деплой бота..."

# Определяем директорию проекта
PROJECT_DIR="/opt/telegram-bot"
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="/home/$USER/telegram-bot"
fi
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="$HOME/telegram-bot"
fi

echo "📁 Рабочая директория: $PROJECT_DIR"

# Создаем директорию если не существует
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Останавливаем бота
echo "⏹️ Останавливаем бота..."
sudo systemctl stop telegram-bot 2>/dev/null || pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Получаем последние изменения
echo "📥 Получаем последние изменения..."
if [ -d ".git" ]; then
    git fetch origin
    git reset --hard origin/main
    git clean -fd
else
    echo "❌ Git репозиторий не найден. Сначала клонируйте репозиторий."
    exit 1
fi

# Создаем виртуальное окружение
echo "🐍 Настраиваем Python окружение..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Создаем .env файл если не существует
if [ ! -f ".env" ]; then
    echo "⚙️ Создаем .env файл..."
    cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Bitrix24
BITRIX_WEBHOOK_URL=your_webhook_url_here
BITRIX_USER_ID=your_user_id_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///bot.db

# Logging
LOG_LEVEL=INFO

# Server
PORT=3000
USE_POLLING=true
EOF
    echo "⚠️ Не забудьте заполнить .env файл!"
fi

# Создаем systemd сервис
echo "🔧 Настраиваем systemd сервис..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << EOF
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

# Перезагружаем systemd и запускаем сервис
echo "🔄 Перезагружаем systemd..."
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot

echo "✅ Деплой завершен!"
echo "📝 Не забудьте:"
echo "1. Заполнить .env файл с вашими токенами"
echo "2. Запустить бота: sudo systemctl start telegram-bot"
echo "3. Проверить статус: sudo systemctl status telegram-bot"
echo "4. Посмотреть логи: sudo journalctl -u telegram-bot -f"