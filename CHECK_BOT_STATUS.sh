#!/bin/bash
# CHECK_BOT_STATUS.sh - Скрипт для проверки статуса бота

echo "🔍 ПРОВЕРКА СТАТУСА БОТА"
echo "========================"

# 1. Проверяем статус сервиса
echo "📊 Статус сервиса telegram-bot:"
sudo systemctl status telegram-bot --no-pager

echo ""
echo "📋 Последние логи (последние 20 строк):"
sudo journalctl -u telegram-bot -n 20 --no-pager

echo ""
echo "🔧 Проверяем файлы бота:"
ls -la /opt/telegram-bot/ | grep -E "(main|aggressive|meeting_link)"

echo ""
echo "✅ Проверка завершена!"
echo "📋 Для мониторинга логов в реальном времени: journalctl -u telegram-bot -f"
