#!/bin/bash
# БЫСТРОЕ ИСПРАВЛЕНИЕ ОШИБКИ MeetingPlatformDetector

echo "🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ ОШИБКИ MeetingPlatformDetector"

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервной копии
echo "💾 Создаю резервную копию..."
cp meeting_link_processor.py meeting_link_processor.py.backup.$(date +%Y%m%d_%H%M%S)

# Скачивание исправленного файла
echo "📥 Скачиваю исправленный файл..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py

# Проверка файла
if [ ! -f "meeting_link_processor.py" ]; then
    echo "❌ Ошибка: meeting_link_processor.py не найден"
    exit 1
fi

# Установка прав
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
sleep 3
systemctl status telegram-bot --no-pager

echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "   • Добавлена инициализация platform_detector в MeetingLinkProcessor"
echo "   • Исправлена ошибка 'MeetingPlatformDetector' object has no attribute 'detect_platform'"
echo ""
echo "📋 Теперь бот должен корректно определять платформы встреч!"
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
