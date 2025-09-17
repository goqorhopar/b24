#!/bin/bash
# Быстрое исправление бота на VPS

echo "🚀 Быстрое исправление бота..."

# Остановка бота
systemctl stop telegram-bot

# Переход в директорию
cd /opt/telegram-bot

# Скачивание исправленных файлов
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/real_meeting_automation.py -o real_meeting_automation.py
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py -o meeting_link_processor.py

# Очистка кеша
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапуск
systemctl start telegram-bot

echo "✅ Исправления применены! Проверьте логи: journalctl -u telegram-bot -f"
