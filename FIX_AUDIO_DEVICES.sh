#!/bin/bash
# FIX_AUDIO_DEVICES.sh - Скрипт для исправления проблем с аудиоустройствами

echo "🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМ С АУДИОУСТРОЙСТВАМИ"
echo "=========================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot
sudo systemctl daemon-reload

# 2. Создаем резервную копию
echo "💾 Создаю резервную копию..."
sudo cp /opt/telegram-bot/aggressive_meeting_automation.py /opt/telegram-bot/aggressive_meeting_automation.py.bak_$(date +%Y%m%d%H%M%S)

# 3. Скачиваем исправленный файл
echo "📥 Скачиваю исправленный файл..."
sudo curl -o /opt/telegram-bot/aggressive_meeting_automation.py https://raw.githubusercontent.com/goqorhopar/b24/main/aggressive_meeting_automation.py

# 4. Устанавливаем/обновляем PulseAudio утилиты
echo "📦 Устанавливаю PulseAudio утилиты..."
sudo apt-get update
sudo apt-get install -y pulseaudio pulseaudio-utils

# 5. Проверяем доступные аудиоустройства
echo "🔍 Проверяю доступные аудиоустройства..."
echo "Sink-устройства:"
pactl list short sinks | grep .monitor || echo "Нет sink-мониторов"
echo ""
echo "Все sink-устройства:"
pactl list short sinks || echo "Нет sink-устройств"
echo ""
echo "Источники звука:"
pactl list short sources || echo "Нет источников звука"

# 6. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 7. Перезапускаем бота
echo "🔄 Перезапускаю бота..."
sudo systemctl start telegram-bot
sudo systemctl daemon-reload

# 8. Проверяем статус бота
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

echo ""
echo "🎉 ИСПРАВЛЕНИЕ АУДИОУСТРОЙСТВ ЗАВЕРШЕНО!"
echo "📋 Что исправлено:"
echo "• Добавлено автоматическое определение доступных аудиоустройств"
echo "• Улучшена обработка ошибок parecord"
echo "• Добавлены множественные попытки с разными параметрами"
echo "• Увеличено время ожидания для стабильности"
echo ""
echo "📋 Для проверки логов: journalctl -u telegram-bot -f"
echo "📋 Для проверки аудиоустройств: pactl list short sinks"
