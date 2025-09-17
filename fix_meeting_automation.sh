#!/bin/bash

echo "🚀 Исправление автоматизации встреч на VPS"
echo "=========================================="

# Останавливаем бота
echo "1. Останавливаем бота..."
systemctl stop telegram-bot

# Переходим в директорию проекта
cd /opt/telegram-bot

# Обновляем код из GitHub
echo "2. Обновляем код из GitHub..."
git pull origin main

# Устанавливаем необходимые пакеты
echo "3. Устанавливаем виртуальный дисплей и браузеры..."
apt update
apt install -y xvfb x11vnc fluxbox firefox-esr chromium-browser pulseaudio alsa-utils

# Создаем скрипт запуска с виртуальным дисплеем
echo "4. Создаем скрипт запуска с виртуальным дисплеем..."
cat > start_with_display.sh << 'EOF'
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

chmod +x start_with_display.sh

# Заменяем main.py на версию с автоматизацией
echo "5. Обновляем main.py для поддержки автоматизации встреч..."
if [ -f "main_with_meeting_automation.py" ]; then
    cp main.py main.py.backup
    cp main_with_meeting_automation.py main.py
    echo "✅ main.py обновлен"
else
    echo "❌ main_with_meeting_automation.py не найден"
fi

# Обновляем systemd сервис
echo "6. Обновляем systemd сервис..."
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

# Перезагружаем systemd
echo "7. Перезагружаем systemd..."
systemctl daemon-reload

# Запускаем бота
echo "8. Запускаем бота..."
systemctl start telegram-bot

# Проверяем статус
echo "9. Проверяем статус бота..."
sleep 3
systemctl status telegram-bot --no-pager

echo -e "\n✅ Исправление завершено!"
echo "📋 Проверьте логи: journalctl -u telegram-bot -f"
echo "🤖 Отправьте боту ссылку на встречу для тестирования"
