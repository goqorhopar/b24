#!/bin/bash
# FIX_MEETING_JOIN.sh - Скрипт для исправления проблем с присоединением к встречам

echo "🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С ПРИСОЕДИНЕНИЕМ К ВСТРЕЧАМ"
echo "================================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot
sudo systemctl daemon-reload

# 2. Создаем резервные копии
echo "💾 Создаю резервные копии..."
TIMESTAMP=$(date +%Y%m%d%H%M%S)
BACKUP_DIR="/opt/telegram-bot/backup_$TIMESTAMP"
sudo mkdir -p "$BACKUP_DIR"
sudo cp /opt/telegram-bot/*.py "$BACKUP_DIR/" 2>/dev/null
echo "Резервные копии сохранены в $BACKUP_DIR"

# 3. Удаляем старые/проблемные файлы
echo "🗑️ Удаляю старые файлы..."
sudo rm -f /opt/telegram-bot/main.py
sudo rm -f /opt/telegram-bot/meeting_automation.py
sudo rm -f /opt/telegram-bot/real_meeting_automation.py
sudo rm -f /opt/telegram-bot/audio_capture.py

# 4. Скачиваем исправленные файлы
echo "📥 Скачиваю исправленные файлы..."
REPO_BASE_URL="https://raw.githubusercontent.com/goqorhopar/b24/main"
sudo curl -o /opt/telegram-bot/main_correct.py "$REPO_BASE_URL/main_correct.py"
sudo curl -o /opt/telegram-bot/aggressive_meeting_automation.py "$REPO_BASE_URL/aggressive_meeting_automation.py"
sudo curl -o /opt/telegram-bot/meeting_link_processor.py "$REPO_BASE_URL/meeting_link_processor.py"
sudo curl -o /opt/telegram-bot/platform_detector.py "$REPO_BASE_URL/platform_detector.py"

# 5. Устанавливаем права доступа
echo "🔐 Устанавливаю права доступа..."
sudo chown -R root:root /opt/telegram-bot/
sudo chmod 644 /opt/telegram-bot/*.py
sudo chmod +x /opt/telegram-bot/*.sh 2>/dev/null

# 6. Устанавливаем/обновляем зависимости
echo "📦 Устанавливаю зависимости..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv
sudo apt-get install -y google-chrome-stable
sudo apt-get install -y pulseaudio pulseaudio-utils

# 7. Устанавливаем Python пакеты
echo "🐍 Устанавливаю Python пакеты..."
pip3 install --upgrade pip
pip3 install selenium requests python-telegram-bot flask python-dotenv

# 8. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 9. Проверяем Chrome и Chromedriver
echo "🌐 Проверяю Chrome и Chromedriver..."
google-chrome --version
# Selenium Manager должен автоматически управлять Chromedriver

# 10. Тестируем импорт модулей
echo "🧪 Тестирую импорт модулей..."
cd /opt/telegram-bot
python3 -c "
try:
    from aggressive_meeting_automation import meeting_automation
    print('✅ aggressive_meeting_automation импортирован успешно')
except Exception as e:
    print('❌ Ошибка импорта aggressive_meeting_automation:', e)

try:
    from meeting_link_processor import MeetingLinkProcessor
    print('✅ meeting_link_processor импортирован успешно')
except Exception as e:
    print('❌ Ошибка импорта meeting_link_processor:', e)

try:
    from platform_detector import MeetingPlatformDetector
    print('✅ platform_detector импортирован успешно')
except Exception as e:
    print('❌ Ошибка импорта platform_detector:', e)
"

# 11. Перезапускаем бота
echo "🔄 Перезапускаю бота..."
sudo systemctl start telegram-bot
sudo systemctl daemon-reload

# 12. Проверяем статус бота
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

# 13. Показываем последние логи
echo ""
echo "📋 Последние 20 строк логов:"
journalctl -u telegram-bot -n 20 --no-pager

echo ""
echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "• Обновлены все файлы бота"
echo "• Установлены все зависимости"
echo "• Очищен кеш Python"
echo "• Проверена работоспособность модулей"
echo ""
echo "📋 Для мониторинга логов: journalctl -u telegram-bot -f"
echo "📋 Для диагностики: curl -fsSL $REPO_BASE_URL/DEBUG_MEETING_JOIN.sh | bash"
