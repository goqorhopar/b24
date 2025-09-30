#!/bin/bash

echo "🔧 Развертывание исправленного Audio Meeting Bot..."

# Остановим бота
echo "⏹️ Останавливаю бота..."
systemctl stop meeting-bot.service 2>/dev/null || true

# Создадим резервную копию
echo "💾 Создаю резервную копию..."
cp -r /opt/meeting-bot /opt/meeting-bot.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Удалим старые файлы
echo "🗑️ Удаляю старые файлы..."
rm -rf /opt/meeting-bot/app/joiners/
rm -rf /opt/meeting-bot/app/recorder/
rm -rf /opt/meeting-bot/app/deploy/
rm -rf /opt/meeting-bot/app/systemd/
rm -f /opt/meeting-bot/app/meeting_bot.py
rm -f /opt/meeting-bot/app/telegram_meeting_bot.py
rm -f /opt/meeting-bot/app/meeting_bot_hybrid.py
rm -f /opt/meeting-bot/app/config.yaml
rm -f /opt/meeting-bot/app/requirements.txt
rm -f /opt/meeting-bot/requirements.txt
rm -f /opt/meeting-bot/auto_deploy.py
rm -f /opt/meeting-bot/github_integration.py
rm -f /opt/meeting-bot/docker-compose.yml
rm -f /opt/meeting-bot/install_server.sh
rm -f /opt/meeting-bot/install_hybrid.sh
rm -f /opt/meeting-bot/install_auto_bot.sh
rm -rf /opt/meeting-bot/.github/

# Создадим минимальную структуру
echo "📁 Создаю структуру директорий..."
mkdir -p /opt/meeting-bot/app
mkdir -p /opt/meeting-bot/logs
mkdir -p /recordings

# Создадим requirements.txt
echo "📦 Создаю requirements.txt..."
cat > /opt/meeting-bot/app/requirements.txt << 'EOF'
python-telegram-bot==21.6
playwright==1.48.0
faster-whisper==0.10.0
soundfile>=0.12.1
psutil>=5.9.0
python-dotenv>=1.0.0
EOF

# Копируем исправленный бот
echo "📋 Копирую исправленный бот..."
cp fixed_audio_only_bot.py /opt/meeting-bot/app/audio_only_bot.py

# Установим зависимости
echo "📦 Устанавливаю зависимости..."
sudo -u bot /opt/meeting-bot/venv/bin/pip install -r /opt/meeting-bot/app/requirements.txt

# Установим браузеры для Playwright
echo "🌐 Устанавливаю браузеры..."
sudo -u bot /opt/meeting-bot/venv/bin/playwright install chromium

# Обновим systemd сервис
echo "⚙️ Обновляю systemd сервис..."
cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Audio Only Meeting Bot
After=network.target

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=/opt/meeting-bot
EnvironmentFile=/opt/meeting-bot/.env
ExecStart=/opt/meeting-bot/venv/bin/python /opt/meeting-bot/app/audio_only_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Настроим права
echo "🔐 Настраиваю права доступа..."
chown -R bot:bot /opt/meeting-bot
chown -R bot:bot /recordings
chmod +x /opt/meeting-bot/app/audio_only_bot.py

# Проверим PulseAudio
echo "🔊 Проверяю PulseAudio..."
if ! pulseaudio --check; then
    echo "⚠️ PulseAudio не запущен, запускаю..."
    pulseaudio --start
    sleep 2
fi

# Проверим ffmpeg
echo "🎥 Проверяю ffmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg не установлен!"
    echo "Установите: apt-get install ffmpeg"
    exit 1
fi

# Перезагрузим systemd
echo "🔄 Перезагружаю systemd..."
systemctl daemon-reload

# Запустим бота
echo "🚀 Запускаю бота..."
systemctl start meeting-bot.service

# Проверим статус
echo "📊 Проверяю статус..."
sleep 3
systemctl status meeting-bot.service --no-pager

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Полезные команды:"
echo "  systemctl status meeting-bot.service  # Статус бота"
echo "  journalctl -u meeting-bot.service -f  # Логи в реальном времени"
echo "  systemctl restart meeting-bot.service # Перезапуск бота"
echo ""
echo "🔍 Для отладки:"
echo "  journalctl -u meeting-bot.service --since '5 minutes ago'"
echo "  ls -la /recordings/  # Проверить записи"
echo "  pulseaudio --check   # Проверить аудио"
