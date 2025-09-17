#!/bin/bash
# Скрипт для деплоя исправлений с поддержкой всех платформ

echo "🚀 Деплой исправлений с поддержкой всех платформ..."

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервной копии
echo "💾 Создаю резервную копию..."
cp real_meeting_automation.py real_meeting_automation.py.backup.$(date +%Y%m%d_%H%M%S)

# Скачивание исправленного файла
echo "📥 Скачиваю исправленный файл с поддержкой всех платформ..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py

# Проверка файла
echo "🔍 Проверяю файл..."
if [ ! -f "real_meeting_automation.py" ]; then
    echo "❌ Ошибка: real_meeting_automation.py не найден"
    exit 1
fi

# Установка прав
chmod 644 real_meeting_automation.py

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
echo "📋 Поддерживаемые платформы:"
echo "   • Zoom (zoom.us, us05web.zoom.us)"
echo "   • Google Meet (meet.google.com)"
echo "   • Microsoft Teams (teams.microsoft.com)"
echo "   • Контур.Толк (ktalk.ru, talk.kontur.ru)"
echo "   • Яндекс Телемост (telemost.yandex.ru)"
echo ""
echo "📋 Для проверки логов используйте: journalctl -u telegram-bot -f"
