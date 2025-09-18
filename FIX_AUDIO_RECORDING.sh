#!/bin/bash
# ИСПРАВЛЕНИЕ АУДИОЗАПИСИ - используем parecord вместо pyaudio

echo "🔧 ИСПРАВЛЕНИЕ АУДИОЗАПИСИ - используем parecord вместо pyaudio"

# Остановка бота
echo "⏹️ Останавливаю бота..."
systemctl stop telegram-bot

# Переход в директорию проекта
cd /opt/telegram-bot

# Создание резервной копии
echo "💾 Создаю резервную копию..."
cp meeting_link_processor.py meeting_link_processor.py.backup.$(date +%Y%m%d_%H%M%S)

# Проверка наличия parecord
echo "🔍 Проверяю наличие parecord..."
if command -v parecord &> /dev/null; then
    echo "✅ parecord найден"
else
    echo "❌ parecord не найден, устанавливаю..."
    apt update && apt install -y pulseaudio-utils
fi

# Проверка аудиоустройств
echo "🔍 Проверяю аудиоустройства..."
pactl list sources short

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
echo "   • Убрана зависимость от pyaudio/sounddevice"
echo "   • Используется parecord для записи аудио"
echo "   • Аудиозапись интегрирована с агрессивной автоматизацией"
echo ""
echo "📋 Теперь бот должен корректно записывать аудио встреч!"
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
