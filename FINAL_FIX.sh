#!/bin/bash
# ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ БОТА

echo "🔥 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ БОТА - УБИРАЕМ ФЕЙКОВУЮ ЛОГИКУ"

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервных копий
echo "💾 Создаю резервные копии..."
cp main.py main.py.backup.$(date +%Y%m%d_%H%M%S)
cp real_meeting_automation.py real_meeting_automation.py.backup.$(date +%Y%m%d_%H%M%S)
cp meeting_link_processor.py meeting_link_processor.py.backup.$(date +%Y%m%d_%H%M%S)

# Удаление фейковых файлов
echo "🗑️ Удаляю фейковые файлы..."
rm -f main_real_automation.py
rm -f main_with_meeting_automation.py

# Скачивание ПРАВИЛЬНЫХ файлов
echo "📥 Скачиваю ПРАВИЛЬНЫЕ файлы..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/main_correct.py -o main.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/aggressive_meeting_automation.py -o aggressive_meeting_automation.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py

# Проверка файлов
echo "🔍 Проверяю файлы..."
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: main.py не найден"
    exit 1
fi

if [ ! -f "aggressive_meeting_automation.py" ]; then
    echo "❌ Ошибка: aggressive_meeting_automation.py не найден"
    exit 1
fi

if [ ! -f "meeting_link_processor.py" ]; then
    echo "❌ Ошибка: meeting_link_processor.py не найден"
    exit 1
fi

# Установка прав
chmod 644 main.py
chmod 644 aggressive_meeting_automation.py
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

echo "🎉 ФИНАЛЬНОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "   • Удален фейковый main_real_automation.py"
echo "   • Установлен правильный main.py"
echo "   • Используется агрессивная автоматизация"
echo "   • Убрана фейковая логика анализа"
echo ""
echo "📋 Теперь бот будет РЕАЛЬНО присоединяться к встречам!"
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
