#!/bin/bash
# Скрипт для деплоя агрессивной автоматизации встреч

echo "🔥 ДЕПЛОЙ АГРЕССИВНОЙ АВТОМАТИЗАЦИИ ВСТРЕЧ"

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервной копии
echo "💾 Создаю резервную копию..."
cp real_meeting_automation.py real_meeting_automation.py.backup.$(date +%Y%m%d_%H%M%S)
cp meeting_link_processor.py meeting_link_processor.py.backup.$(date +%Y%m%d_%H%M%S)

# Скачивание агрессивных файлов
echo "📥 Скачиваю агрессивные файлы..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/aggressive_meeting_automation.py -o aggressive_meeting_automation.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/debug_meeting_automation.py -o debug_meeting_automation.py

# Проверка файлов
echo "🔍 Проверяю файлы..."
if [ ! -f "aggressive_meeting_automation.py" ]; then
    echo "❌ Ошибка: aggressive_meeting_automation.py не найден"
    exit 1
fi

if [ ! -f "meeting_link_processor.py" ]; then
    echo "❌ Ошибка: meeting_link_processor.py не найден"
    exit 1
fi

# Установка прав
chmod 644 aggressive_meeting_automation.py
chmod 644 meeting_link_processor.py
chmod 644 debug_meeting_automation.py

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

echo "🔥 АГРЕССИВНАЯ АВТОМАТИЗАЦИЯ РАЗВЕРНУТА!"
echo "📋 Что изменилось:"
echo "   • Агрессивное кликание по всем элементам"
echo "   • Множественные попытки ввода имени"
echo "   • JavaScript клики"
echo "   • Сохранение HTML для анализа"
echo "   • Максимальная отладка"
echo ""
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
echo "📋 Для отладки: python debug_meeting_automation.py <URL_встречи>"
