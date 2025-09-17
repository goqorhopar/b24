#!/bin/bash

# Скрипт для настройки VPS с виртуальным дисплеем для автоматизации встреч

echo "🚀 Настройка VPS для автоматизации встреч..."

# 1. Обновляем систему
apt update && apt upgrade -y

# 2. Устанавливаем виртуальный дисплей и браузеры
apt install -y xvfb x11vnc fluxbox firefox-esr chromium-browser

# 3. Устанавливаем дополнительные пакеты для аудио
apt install -y pulseaudio alsa-utils

# 4. Создаем скрипт запуска с виртуальным дисплеем
cat > /opt/telegram-bot/start_with_display.sh << 'EOF'
#!/bin/bash

# Запуск виртуального дисплея
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Запуск оконного менеджера
DISPLAY=:99 fluxbox > /dev/null 2>&1 &
FLUXBOX_PID=$!

# Запуск PulseAudio
pulseaudio --start --exit-idle-time=-1 > /dev/null 2>&1 &

# Ждем немного для инициализации
sleep 3

# Запуск бота
cd /opt/telegram-bot
source venv/bin/activate
python main.py

# Очистка при завершении
kill $XVFB_PID $FLUXBOX_PID 2>/dev/null
EOF

chmod +x /opt/telegram-bot/start_with_display.sh

# 5. Обновляем systemd сервис для использования виртуального дисплея
cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Bot with Virtual Display
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
Environment=DISPLAY=:99
ExecStart=/opt/telegram-bot/start_with_display.sh
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# 6. Перезагружаем systemd
systemctl daemon-reload
systemctl enable telegram-bot

echo "✅ VPS настроен для автоматизации встреч с виртуальным дисплеем!"
echo "Для запуска бота выполните: systemctl start telegram-bot"
