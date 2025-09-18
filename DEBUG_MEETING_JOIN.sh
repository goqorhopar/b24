#!/bin/bash
# DEBUG_MEETING_JOIN.sh - Скрипт для диагностики проблем с присоединением к встречам

echo "🔍 ДИАГНОСТИКА ПРОБЛЕМ С ПРИСОЕДИНЕНИЕМ К ВСТРЕЧАМ"
echo "================================================="

# 1. Проверяем статус бота
echo "1. Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

# 2. Показываем последние логи
echo ""
echo "2. Последние 50 строк логов бота:"
journalctl -u telegram-bot -n 50 --no-pager

# 3. Проверяем наличие всех файлов
echo ""
echo "3. Проверяю наличие файлов:"
ls -la /opt/telegram-bot/main.py
ls -la /opt/telegram-bot/aggressive_meeting_automation.py
ls -la /opt/telegram-bot/meeting_link_processor.py
ls -la /opt/telegram-bot/platform_detector.py

# 4. Проверяем Chrome и Chromedriver
echo ""
echo "4. Проверяю Chrome и Chromedriver:"
google-chrome --version 2>/dev/null || echo "Chrome не найден"
which chromedriver || echo "Chromedriver не найден"

# 5. Проверяем Python зависимости
echo ""
echo "5. Проверяю Python зависимости:"
python3 -c "import selenium; print('Selenium:', selenium.__version__)" 2>/dev/null || echo "Selenium не установлен"
python3 -c "import requests; print('Requests:', requests.__version__)" 2>/dev/null || echo "Requests не установлен"

# 6. Проверяем права доступа
echo ""
echo "6. Проверяю права доступа:"
ls -la /opt/telegram-bot/
whoami
groups

# 7. Проверяем переменные окружения
echo ""
echo "7. Проверяю переменные окружения:"
if [ -f /opt/telegram-bot/.env ]; then
    echo "Файл .env найден:"
    cat /opt/telegram-bot/.env | grep -E "(TELEGRAM|BITRIX|GEMINI|MEETING)" || echo "Переменные не найдены"
else
    echo "Файл .env не найден!"
fi

# 8. Тестируем простой Python скрипт
echo ""
echo "8. Тестирую импорт модулей:"
python3 -c "
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
    from platform_detector import MeetingPlatformDetector
    print('✅ platform_detector импортирован')
except Exception as e:
    print('❌ Ошибка импорта platform_detector:', e)
"

echo ""
echo "🎯 ДИАГНОСТИКА ЗАВЕРШЕНА!"
echo "Проанализируйте вывод выше для выявления проблем."