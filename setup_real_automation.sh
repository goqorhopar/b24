#!/bin/bash

echo "🚀 Настройка РЕАЛЬНОЙ автоматизации встреч"
echo "=========================================="

# Остановить бота
echo "1. Останавливаем бота..."
systemctl stop telegram-bot

# Переходим в директорию проекта
cd /opt/telegram-bot

# Устанавливаем Chrome и ChromeDriver
echo "2. Устанавливаем Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt update
apt install -y google-chrome-stable

# Устанавливаем ChromeDriver
echo "3. Устанавливаем ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d'.' -f1)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}/chromedriver_linux64.zip"
unzip /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Устанавливаем Python пакеты для автоматизации
echo "4. Устанавливаем Python пакеты..."
source venv/bin/activate
pip install selenium webdriver-manager pyaudio speechrecognition

# Устанавливаем дополнительные аудио компоненты
echo "5. Устанавливаем аудио компоненты..."
apt install -y pulseaudio-utils paprefs pavucontrol

# Копируем файлы реальной автоматизации
echo "6. Обновляем код бота..."
cp main_real_automation.py main.py

# Проверяем установку
echo "7. Проверяем установку..."
google-chrome --version
chromedriver --version
python -c "import selenium; print('Selenium:', selenium.__version__)"

# Настраиваем виртуальный дисплей с большим разрешением
echo "8. Обновляем скрипт запуска..."
cat > start_with_display.sh << 'EOF'
#!/bin/bash

# Запуск виртуального дисплея с большим разрешением
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Запуск оконного менеджера
DISPLAY=:99 fluxbox > /dev/null 2>&1 &
FLUXBOX_PID=$!

# Запуск PulseAudio
pulseaudio --start --exit-idle-time=-1 > /dev/null 2>&1 &

# Устанавливаем переменные для Chrome
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Ждем немного для инициализации
sleep 5

# Запуск бота
cd /opt/telegram-bot
source venv/bin/activate
python main.py

# Очистка при завершении
kill $XVFB_PID $FLUXBOX_PID 2>/dev/null
EOF

chmod +x start_with_display.sh

# Обновляем systemd сервис
echo "9. Обновляем systemd сервис..."
cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Bot with Real Meeting Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin:/usr/local/bin
Environment=DISPLAY=:99
Environment=CHROME_BIN=/usr/bin/google-chrome
Environment=CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ExecStart=/opt/telegram-bot/start_with_display.sh
Restart=always
RestartSec=10
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и запускаем бота
echo "10. Запускаем бота..."
systemctl daemon-reload
systemctl start telegram-bot

# Проверяем статус
echo "11. Проверяем статус..."
sleep 5
systemctl status telegram-bot --no-pager

echo ""
echo "✅ НАСТРОЙКА ЗАВЕРШЕНА!"
echo ""
echo "🎯 Теперь бот может:"
echo "• РЕАЛЬНО присоединяться к встречам через браузер"
echo "• Записывать аудио с встреч"
echo "• Анализировать контент с помощью ИИ"
echo "• Обновлять лиды в Bitrix24"
echo ""
echo "📋 Проверьте логи: journalctl -u telegram-bot -f"
echo "🤖 Отправьте боту ссылку на встречу для тестирования!"
