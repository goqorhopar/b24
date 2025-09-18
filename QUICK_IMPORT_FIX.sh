#!/bin/bash
# QUICK_IMPORT_FIX.sh - Быстрое исправление проблем с импортами

echo "🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМ С ИМПОРТАМИ"
echo "=========================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot

# 2. Скачиваем исправленные файлы
echo "📥 Скачиваю исправленные файлы..."
sudo curl -o /opt/telegram-bot/meeting_link_processor.py https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py

# 3. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 4. Тестируем импорт
echo "🧪 Тестирую импорт модулей..."
cd /opt/telegram-bot
python3 -c "
try:
    from aggressive_meeting_automation import meeting_automation
    print('✅ aggressive_meeting_automation импортирован')
    print('✅ meeting_automation объект доступен')
except Exception as e:
    print('❌ Ошибка импорта aggressive_meeting_automation:', e)

try:
    from meeting_link_processor import MeetingLinkProcessor
    print('✅ meeting_link_processor импортирован')
except Exception as e:
    print('❌ Ошибка импорта meeting_link_processor:', e)

try:
    from main_correct import app
    print('✅ main_correct импортирован')
except Exception as e:
    print('❌ Ошибка импорта main_correct:', e)
"

# 5. Перезапускаем бота
echo "🔄 Перезапускаю бота..."
sudo systemctl start telegram-bot

# 6. Проверяем статус
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

echo ""
echo "🎉 ИСПРАВЛЕНИЕ ИМПОРТОВ ЗАВЕРШЕНО!"
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
