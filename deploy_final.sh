#!/bin/bash

echo "🚀 Финальное развертывание исправленного Meeting Bot..."

# Подключаемся к серверу и развертываем
ssh -o StrictHostKeyChecking=no root@109.172.47.253 << 'EOF'

echo "🛑 Останавливаю старый бот..."
systemctl stop meeting-bot.service 2>/dev/null || true

echo "📁 Перехожу в рабочую директорию..."
cd /opt/meeting-bot

echo "📥 Обновляю код с GitHub..."
git fetch origin
git reset --hard origin/main-fixed

echo "🔧 Обновляю зависимости..."
source venv/bin/activate
pip install -r requirements.txt

echo "🔐 Обновляю .env файл с токенами..."
cat > /opt/meeting-bot/.env << 'ENV_EOF'
# VPS
VPS_HOST=your_server_ip
VPS_USERNAME=root
VPS_PASSWORD=your_password

# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# GitHub
GITHUB_REPO=goqorhopar/b24
GITHUB_TOKEN=your_github_token
GITHUB_BRANCH=main-fixed

# Deploy
DEPLOY_LOCAL_PATH=/opt/meeting-bot
SERVICE_NAME=meeting-bot.service

# Bot
BOT_NAME=AutoMeetingBot
RECORD_DIR=/recordings
WHISPER_MODEL=medium
MEETING_TIMEOUT_MIN=3
ENV_EOF

echo "⚙️ Настраиваю права доступа..."
chown -R bot:bot /opt/meeting-bot
chmod +x /opt/meeting-bot/meeting-bot-main.py

echo "🚀 Запускаю исправленного бота..."
systemctl start meeting-bot.service

echo "⏳ Жду запуска..."
sleep 5

echo "📊 Проверяю статус..."
systemctl status meeting-bot.service --no-pager

echo "📋 Последние логи:"
journalctl -u meeting-bot.service -n 10 --no-pager

echo "✅ Развертывание завершено!"

EOF

echo ""
echo "🎉 Исправленный бот развернут!"
echo "🔗 Тестируйте с ссылкой: https://meet.google.com/gwm-uzbz-vxw"
