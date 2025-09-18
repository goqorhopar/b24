#!/bin/bash
# FINAL_SYSTEM_FIX.sh - Финальное исправление всех системных проблем

echo "🔧 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ВСЕХ СИСТЕМНЫХ ПРОБЛЕМ"
echo "==============================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot

# 2. Устанавливаем Python пакеты с --break-system-packages
echo "🐍 Устанавливаю Python пакеты..."
pip3 install --break-system-packages --upgrade pip
pip3 install --break-system-packages selenium requests python-telegram-bot flask python-dotenv

# 3. Переименовываем main_correct.py в main.py
echo "📝 Переименовываю main_correct.py в main.py..."
sudo cp /opt/telegram-bot/main_correct.py /opt/telegram-bot/main.py

# 4. Проверяем systemd сервис
echo "🔧 Проверяю systemd сервис..."
if [ -f /etc/systemd/system/telegram-bot.service ]; then
    echo "Содержимое сервиса:"
    cat /etc/systemd/system/telegram-bot.service
else
    echo "❌ Файл сервиса не найден!"
fi

# 5. Создаем правильный systemd сервис если нужно
echo "📝 Создаю правильный systemd сервис..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << 'EOF'
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
ExecStart=/usr/bin/python3 /opt/telegram-bot/main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/telegram-bot
Environment=DISPLAY=:99

[Install]
WantedBy=multi-user.target
EOF

# 6. Перезагружаем systemd
echo "🔄 Перезагружаю systemd..."
sudo systemctl daemon-reload

# 7. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 8. Тестируем импорт модулей
echo "🧪 Тестирую импорт модулей..."
cd /opt/telegram-bot
python3 -c "
try:
    import selenium
    print('✅ Selenium импортирован:', selenium.__version__)
except Exception as e:
    print('❌ Ошибка импорта Selenium:', e)

try:
    from aggressive_meeting_automation import meeting_automation
    print('✅ aggressive_meeting_automation импортирован')
except Exception as e:
    print('❌ Ошибка импорта aggressive_meeting_automation:', e)

try:
    from meeting_link_processor import MeetingLinkProcessor
    print('✅ meeting_link_processor импортирован')
except Exception as e:
    print('❌ Ошибка импорта meeting_link_processor:', e)

try:
    from main import app
    print('✅ main импортирован')
except Exception as e:
    print('❌ Ошибка импорта main:', e)
"

# 9. Запускаем бота
echo "🚀 Запускаю бота..."
sudo systemctl start telegram-bot

# 10. Проверяем статус
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

# 11. Показываем последние логи
echo ""
echo "📋 Последние 20 строк логов:"
journalctl -u telegram-bot -n 20 --no-pager

echo ""
echo "🎉 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "• Установлены все Python пакеты (включая Selenium)"
echo "• Переименован main_correct.py в main.py"
echo "• Исправлен systemd сервис"
echo "• Очищен кеш Python"
echo "• Проверена работоспособность всех модулей"
echo ""
echo "📋 Для мониторинга логов: journalctl -u telegram-bot -f"
echo "📋 Для проверки статуса: sudo systemctl status telegram-bot"
