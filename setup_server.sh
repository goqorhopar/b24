#!/bin/bash
# Автоматическая настройка сервера для Meeting Bot

echo "🚀 Настройка сервера для Meeting Bot"
echo "=================================="

# Обновляем систему
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Устанавливаем зависимости
echo "🔧 Установка зависимостей..."
apt install -y python3 python3-pip git curl wget

# Устанавливаем Chrome
echo "🌐 Установка Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Устанавливаем ffmpeg
echo "🎵 Установка ffmpeg..."
apt install -y ffmpeg

# Создаем пользователя для бота
echo "👤 Создание пользователя..."
useradd -m -s /bin/bash meetingbot
usermod -aG audio meetingbot

# Клонируем репозиторий
echo "📥 Клонирование репозитория..."
cd /opt
git clone https://github.com/goqorhopar/b24.git meeting-bot
chown -R meetingbot:meetingbot meeting-bot

# Устанавливаем Python зависимости
echo "🐍 Установка Python зависимостей..."
cd meeting-bot
pip3 install -r requirements.txt

# Создаем systemd сервис
echo "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/meeting-bot.service << EOF
[Unit]
Description=Meeting Bot
After=network.target

[Service]
Type=simple
User=meetingbot
WorkingDirectory=/opt/meeting-bot
ExecStart=/usr/bin/python3 meeting-bot.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/meeting-bot

[Install]
WantedBy=multi-user.target
EOF

# Активируем сервис
echo "🔄 Активация сервиса..."
systemctl daemon-reload
systemctl enable meeting-bot

echo "✅ Сервер настроен!"
echo "📋 Следующие шаги:"
echo "1. Скопируйте файлы авторизации в /opt/meeting-bot/"
echo "2. Настройте переменные окружения в .env"
echo "3. Запустите: systemctl start meeting-bot"
