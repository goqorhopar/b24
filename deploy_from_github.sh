#!/bin/bash

echo "🚀 Развертывание Meeting Bot с GitHub на сервер..."

# Параметры сервера
SERVER_IP="your_server_ip"
SERVER_USER="root"
SERVER_PASS="your_password"

# Параметры GitHub
GITHUB_REPO="goqorhopar/b24"
GITHUB_TOKEN="your_github_token"
GITHUB_BRANCH="main-clean"

echo "📡 Подключаюсь к серверу $SERVER_IP..."

# Подключаемся к серверу и развертываем
sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << EOF

echo "🛑 Останавливаю старый бот..."
systemctl stop meeting-bot.service 2>/dev/null || true

echo "📁 Создаю рабочую директорию..."
mkdir -p /opt/meeting-bot
cd /opt/meeting-bot

echo "🗑️ Очищаю старые файлы..."
rm -rf * .*

echo "📥 Клонирую репозиторий с GitHub..."
git clone -b $GITHUB_BRANCH https://$GITHUB_TOKEN@github.com/$GITHUB_REPO.git .

echo "🔧 Устанавливаю системные зависимости..."
apt-get update -y
apt-get install -y python3 python3-pip python3-venv ffmpeg pulseaudio chromium-browser git

echo "👤 Создаю пользователя bot..."
useradd -m -s /bin/bash bot 2>/dev/null || true
usermod -a -G audio bot

echo "🐍 Создаю виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

echo "📦 Устанавливаю Python зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🌐 Устанавливаю браузеры для Playwright..."
playwright install chromium

echo "⚙️ Настраиваю права доступа..."
chown -R bot:bot /opt/meeting-bot
chmod +x /opt/meeting-bot/meeting-bot-main.py
chmod +x /opt/meeting-bot/fixed_audio_only_bot.py

echo "🔐 Создаю .env файл с токенами..."
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
GITHUB_BRANCH=main-clean

# Deploy
DEPLOY_LOCAL_PATH=/opt/meeting-bot
SERVICE_NAME=meeting-bot.service

# Bot
BOT_NAME=AutoMeetingBot
RECORD_DIR=/recordings
WHISPER_MODEL=medium
MEETING_TIMEOUT_MIN=3
ENV_EOF

echo "📁 Создаю директорию для записей..."
mkdir -p /recordings
chown -R bot:bot /recordings

echo "⚙️ Создаю systemd сервис..."
cat > /etc/systemd/system/meeting-bot.service << 'SERVICE_EOF'
[Unit]
Description=Meeting Bot
After=network.target

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=/opt/meeting-bot
EnvironmentFile=/opt/meeting-bot/.env
ExecStart=/opt/meeting-bot/venv/bin/python /opt/meeting-bot/meeting-bot-main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "🔄 Перезагружаю systemd..."
systemctl daemon-reload
systemctl enable meeting-bot.service

echo "🚀 Запускаю бота..."
systemctl start meeting-bot.service

echo "⏳ Жду запуска..."
sleep 5

echo "📊 Проверяю статус..."
systemctl status meeting-bot.service --no-pager

echo "✅ Развертывание завершено!"

EOF

echo ""
echo "🎉 Бот развернут на сервере!"
echo ""
echo "📋 Полезные команды:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  systemctl status meeting-bot.service"
echo "  journalctl -u meeting-bot.service -f"
echo ""
echo "🔗 Тестируйте бота с ссылкой: https://meet.google.com/gwm-uzbz-vxw"
