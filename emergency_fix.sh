#!/bin/bash
# Экстренное исправление бота

echo "🚨 ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ БОТА"

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию
cd /opt/telegram-bot

# Скачивание исправленного файла
echo "📥 Скачиваю исправленный файл..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Очистка кеша
echo "🧹 Очищаю кеш..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапуск
echo "🔄 Перезапускаю бота..."
systemctl start telegram-bot

# Проверка
echo "✅ Проверяю статус..."
sleep 3
systemctl status telegram-bot --no-pager

echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Теперь отправьте боту ссылку на встречу для тестирования"
