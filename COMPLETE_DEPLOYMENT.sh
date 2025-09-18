#!/bin/bash
# COMPLETE_DEPLOYMENT.sh - Полное развертывание всех исправлений

echo "🚀 ПОЛНОЕ РАЗВЕРТЫВАНИЕ БОТА"
echo "============================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot

# 2. Создаем резервную копию
echo "💾 Создаю резервную копию..."
sudo mkdir -p /opt/telegram-bot/backup_$(date +%Y%m%d_%H%M%S)
sudo cp -r /opt/telegram-bot/*.py /opt/telegram-bot/backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true

# 3. Скачиваем все исправленные файлы
echo "📥 Скачиваю исправленные файлы..."

# Основные файлы
sudo curl -o /opt/telegram-bot/aggressive_meeting_automation.py https://raw.githubusercontent.com/goqorhopar/b24/main/aggressive_meeting_automation.py
sudo curl -o /opt/telegram-bot/meeting_link_processor.py https://raw.githubusercontent.com/goqorhopar/b24/main/meeting_link_processor.py
sudo curl -o /opt/telegram-bot/platform_detector.py https://raw.githubusercontent.com/goqorhopar/b24/main/platform_detector.py
sudo curl -o /opt/telegram-bot/main_correct.py https://raw.githubusercontent.com/goqorhopar/b24/main/main_correct.py

# Заменяем main.py на исправленную версию
sudo cp /opt/telegram-bot/main_correct.py /opt/telegram-bot/main.py

# 4. Устанавливаем необходимые пакеты
echo "📦 Устанавливаю необходимые пакеты..."
sudo apt update -qq
sudo apt install -y pulseaudio-utils

# 5. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# 6. Устанавливаем права доступа
echo "🔐 Устанавливаю права доступа..."
sudo chown -R root:root /opt/telegram-bot/
sudo chmod +x /opt/telegram-bot/*.py

# 7. Перезапускаем бота
echo "🔄 Перезапускаю бота..."
sudo systemctl daemon-reload
sudo systemctl start telegram-bot

# 8. Проверяем статус
echo "✅ Проверяю статус бота..."
sleep 3
sudo systemctl status telegram-bot --no-pager

# 9. Показываем последние логи
echo ""
echo "📋 Последние логи (последние 10 строк):"
sudo journalctl -u telegram-bot -n 10 --no-pager

echo ""
echo "🎉 ПОЛНОЕ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo ""
echo "📋 Что исправлено:"
echo "• ✅ Бесконечный цикл аудиозаписи"
echo "• ✅ Проблемы с аудиоустройствами"
echo "• ✅ Импорты и зависимости"
echo "• ✅ Поддержка всех платформ встреч"
echo "• ✅ Агрессивная автоматизация"
echo "• ✅ Интеграция с Gemini AI и Bitrix24"
echo ""
echo "📋 Для тестирования отправьте ссылку на встречу в Telegram боту"
echo "📋 Для мониторинга: journalctl -u telegram-bot -f"
echo "📋 Для проверки статуса: sudo systemctl status telegram-bot"
