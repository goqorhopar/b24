#!/bin/bash

# Скрипт для быстрого деплоя на VPS
# Запускать на VPS

set -e

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

# Создаем директорию если не существует
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Останавливаем бота
echo "⏹️ Останавливаем бота..."
systemctl stop telegram-bot 2>/dev/null || pkill -f "python.*main.py" 2>/dev/null || true
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
    cat > .env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI

# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.1
GEMINI_TOP_P=0.2
GEMINI_MAX_TOKENS=1200

# Bitrix24 Configuration
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1
BITRIX_TASK_DEADLINE_DAYS=3

# Application Configuration
PORT=3000
DB_PATH=bot_state.db
LOG_LEVEL=INFO
NODE_ENV=production

# Request Configuration
MAX_RETRIES=3
RETRY_DELAY=2
REQUEST_TIMEOUT=30
MAX_COMMENT_LENGTH=8000

# Admin Configuration
ADMIN_CHAT_ID=7537953397

# Meeting Automation
MEETING_DISPLAY_NAME=Ассистент Григория Сергеевича
MEETING_HEADLESS=true
MEETING_AUTO_LEAVE=true
MEETING_DURATION_MINUTES=60
EOF
    echo "⚠️ .env файл создан. Проверьте настройки!"
fi

# Создаем systemd сервис
echo "🔧 Настраиваем systemd сервис..."
cat > /etc/systemd/system/telegram-bot.service << EOF
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
systemctl daemon-reload
systemctl enable telegram-bot

# Запускаем бота
echo "▶️ Запускаем бота..."
systemctl start telegram-bot

# Проверяем статус
sleep 3
if systemctl is-active --quiet telegram-bot; then
    echo "✅ Бот успешно запущен!"
    echo "📊 Статус:"
    systemctl status telegram-bot --no-pager -l
else
    echo "❌ Ошибка при запуске бота!"
    echo "📋 Логи:"
    journalctl -u telegram-bot --no-pager -l --since "1 minute ago"
    exit 1
fi

echo "🎉 Деплой завершен успешно!"
echo "📝 Управление ботом:"
echo "  - Статус: systemctl status telegram-bot"
echo "  - Логи: journalctl -u telegram-bot -f"
echo "  - Перезапуск: systemctl restart telegram-bot"
echo "  - Остановка: systemctl stop telegram-bot"