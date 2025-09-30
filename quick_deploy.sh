#!/bin/bash

echo "🚀 Быстрое развертывание Meeting Bot на сервере..."

# Параметры сервера
SERVER_IP="109.172.47.253"
SERVER_USER="root"
SERVER_PASS="MmSS0JSm%6vb"

echo "📡 Подключаюсь к серверу $SERVER_IP..."

# Создаем SSH ключ если не существует
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
fi

# Копируем ключ на сервер
sshpass -p "$SERVER_PASS" ssh-copy-id -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP"

echo "📁 Создаю директории на сервере..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
mkdir -p /opt/meeting-bot
cd /opt/meeting-bot
pwd
EOF

echo "📤 Копирую файлы на сервер..."
scp -o StrictHostKeyChecking=no -r . "$SERVER_USER@$SERVER_IP:/opt/meeting-bot/"

echo "⚙️ Настраиваю сервер..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
cd /opt/meeting-bot

# Останавливаем старый бот
systemctl stop meeting-bot.service 2>/dev/null || true

# Обновляем систему
apt-get update -y

# Устанавливаем системные зависимости
apt-get install -y python3 python3-pip python3-venv ffmpeg pulseaudio chromium-browser sshpass

# Создаем пользователя bot
useradd -m -s /bin/bash bot 2>/dev/null || true
usermod -a -G audio bot

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Устанавливаем Python зависимости
pip install --upgrade pip
pip install python-telegram-bot==21.6
pip install selenium>=4.15.0
pip install faster-whisper>=1.0.0
pip install pydub>=0.25.1
pip install speechrecognition>=3.10.0
pip install PyGithub>=1.59.0
pip install python-dotenv>=1.0.0
pip install playwright>=1.48.0

# Устанавливаем браузеры
playwright install chromium

# Настраиваем права
chown -R bot:bot /opt/meeting-bot
chmod +x /opt/meeting-bot/meeting-bot-main.py
chmod +x /opt/meeting-bot/fixed_audio_only_bot.py

# Создаем systemd сервис
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

# Перезагружаем systemd
systemctl daemon-reload
systemctl enable meeting-bot.service

echo "✅ Настройка завершена!"
EOF

echo "🚀 Запускаю бота..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" << 'EOF'
systemctl start meeting-bot.service
sleep 3
systemctl status meeting-bot.service --no-pager
EOF

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  systemctl status meeting-bot.service"
echo "  journalctl -u meeting-bot.service -f"
echo ""
echo "🔗 Тестируйте бота с ссылкой: https://meet.google.com/gwm-uzbz-vxw"
