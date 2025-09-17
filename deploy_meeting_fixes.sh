#!/bin/bash
# Скрипт для деплоя исправлений автоматизации встреч на VPS

set -e

echo "🚀 Деплой исправлений автоматизации встреч..."

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервной копии
echo "💾 Создаю резервную копию..."
cp real_meeting_automation.py real_meeting_automation.py.backup
cp meeting_link_processor.py meeting_link_processor.py.backup

# Скачивание исправленных файлов
echo "📥 Скачиваю исправленные файлы..."

# Скачиваем исправленный real_meeting_automation.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Скачиваем исправленный meeting_link_processor.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py

# Проверка файлов
echo "🔍 Проверяю файлы..."
if [ ! -f "real_meeting_automation.py" ]; then
    echo "❌ Ошибка: real_meeting_automation.py не найден"
    exit 1
fi

if [ ! -f "meeting_link_processor.py" ]; then
    echo "❌ Ошибка: meeting_link_processor.py не найден"
    exit 1
fi

# Установка прав
chmod 644 real_meeting_automation.py
chmod 644 meeting_link_processor.py

# Очистка кеша Python
echo "🧹 Очищаю кеш Python..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапуск бота
echo "🔄 Перезапускаю бота..."
systemctl start telegram-bot

# Проверка статуса
echo "✅ Проверяю статус бота..."
sleep 5
systemctl status telegram-bot --no-pager

echo "🎉 Деплой исправлений завершен!"
echo "📋 Для проверки логов используйте: journalctl -u telegram-bot -f"
