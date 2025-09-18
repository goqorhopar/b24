#!/bin/bash

echo "🔧 ИСПРАВЛЕНИЕ БЕСКОНЕЧНОГО ЦИКЛА АУДИОЗАПИСИ"
echo "=============================================="

# Останавливаем бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Создаем резервную копию
echo "💾 Создаю резервную копию..."
cp /opt/telegram-bot/aggressive_meeting_automation.py /opt/telegram-bot/aggressive_meeting_automation.py.backup

# Скачиваем исправленный файл
echo "📥 Скачиваю исправленный файл..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/aggressive_meeting_automation.py -o /opt/telegram-bot/aggressive_meeting_automation.py

# Проверяем, что файл скачался
if [ ! -f "/opt/telegram-bot/aggressive_meeting_automation.py" ]; then
    echo "❌ Ошибка: файл не скачался"
    exit 1
fi

# Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
find /opt/telegram-bot -name "*.pyc" -delete
find /opt/telegram-bot -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапускаем бота
echo "🔄 Перезапускаю бота..."
systemctl start telegram-bot

# Проверяем статус
echo "✅ Проверяю статус бота..."
sleep 3
systemctl status telegram-bot --no-pager

echo ""
echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "• Убран бесконечный цикл в start_audio_recording"
echo "• Добавлена проверка is_recording для предотвращения дублирования"
echo "• Улучшена обработка ошибок аудиоустройств"
echo "• Добавлен возврат пути к файлу записи"
echo ""
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
