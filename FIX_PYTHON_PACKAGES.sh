#!/bin/bash
# FIX_PYTHON_PACKAGES.sh - Исправление проблем с Python пакетами

echo "🐍 ИСПРАВЛЕНИЕ ПРОБЛЕМ С PYTHON ПАКЕТАМИ"
echo "======================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot

# 2. Устанавливаем пакеты через apt (системные)
echo "📦 Устанавливаю системные Python пакеты..."
sudo apt-get update
sudo apt-get install -y python3-flask python3-requests python3-selenium python3-telegram-bot python3-dotenv

# 3. Если системные пакеты недоступны, устанавливаем через pip с принудительным флагом
echo "🔧 Устанавливаю пакеты через pip с принудительным флагом..."
pip3 install --break-system-packages --force-reinstall flask requests selenium python-telegram-bot python-dotenv

# 4. Проверяем установку пакетов
echo "🧪 Проверяю установку пакетов..."
python3 -c "
try:
    import flask
    print(\"✅ Flask:\", flask.__version__)
except Exception as e:
    print(\"❌ Flask не найден:\", e)

try:
    import requests
    print(\"✅ Requests:\", requests.__version__)
except Exception as e:
    print(\"❌ Requests не найден:\", e)

try:
    import selenium
    print(\"✅ Selenium:\", selenium.__version__)
except Exception as e:
    print(\"❌ Selenium не найден:\", e)

try:
    import telegram
    print(\"✅ Python-telegram-bot установлен\")
except Exception as e:
    print(\"❌ Python-telegram-bot не найден:\", e)

try:
    import dotenv
    print(\"✅ Python-dotenv установлен\")
except Exception as e:
    print(\"❌ Python-dotenv не найден:\", e)
"

# 5. Проверяем импорт основных модулей бота
echo "🔍 Проверяю импорт модулей бота..."
cd /opt/telegram-bot
python3 -c "
try:
    from aggressive_meeting_automation import meeting_automation
    print(\"✅ aggressive_meeting_automation импортирован\")
except Exception as e:
    print(\"❌ Ошибка импорта aggressive_meeting_automation:\", e)

try:
    from meeting_link_processor import MeetingLinkProcessor
    print(\"✅ meeting_link_processor импортирован\")
except Exception as e:
    print(\"❌ Ошибка импорта meeting_link_processor:\", e)

try:
    from main import app
    print(\"✅ main импортирован\")
except Exception as e:
    print(\"❌ Ошибка импорта main:\", e)
"

# 6. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 7. Запускаем бота
echo "🚀 Запускаю бота..."
sudo systemctl start telegram-bot

# 8. Проверяем статус
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

# 9. Показываем последние логи
echo ""
echo "📋 Последние 10 строк логов:"
journalctl -u telegram-bot -n 10 --no-pager

echo ""
echo "🎉 ИСПРАВЛЕНИЕ PYTHON ПАКЕТОВ ЗАВЕРШЕНО!"
echo "📋 Для мониторинга логов: journalctl -u telegram-bot -f"
