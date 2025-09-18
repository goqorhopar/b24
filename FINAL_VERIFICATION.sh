#!/bin/bash
# FINAL_VERIFICATION.sh - Финальная проверка всех компонентов бота

echo "🔍 ФИНАЛЬНАЯ ПРОВЕРКА БОТА"
echo "=========================="

# 1. Проверяем статус сервиса
echo "📊 Статус сервиса:"
sudo systemctl is-active telegram-bot

# 2. Проверяем основные файлы
echo ""
echo "📁 Проверяем основные файлы:"
echo "• main.py: $(ls -la /opt/telegram-bot/main.py 2>/dev/null | awk '{print $5}') байт"
echo "• aggressive_meeting_automation.py: $(ls -la /opt/telegram-bot/aggressive_meeting_automation.py 2>/dev/null | awk '{print $5}') байт"
echo "• meeting_link_processor.py: $(ls -la /opt/telegram-bot/meeting_link_processor.py 2>/dev/null | awk '{print $5}') байт"

# 3. Проверяем аудиоустройства
echo ""
echo "🎤 Проверяем аудиоустройства:"
pactl list sources short 2>/dev/null | head -3 || echo "❌ PulseAudio не доступен"

# 4. Проверяем последние логи
echo ""
echo "📋 Последние логи (последние 10 строк):"
sudo journalctl -u telegram-bot -n 10 --no-pager

# 5. Проверяем процессы
echo ""
echo "🔄 Активные процессы бота:"
ps aux | grep -E "(python|telegram)" | grep -v grep

echo ""
echo "✅ Финальная проверка завершена!"
echo ""
echo "📋 Для тестирования отправьте ссылку на встречу в Telegram боту"
echo "📋 Для мониторинга: journalctl -u telegram-bot -f"
