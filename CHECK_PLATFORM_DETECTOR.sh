#!/bin/bash
# ПРОВЕРКА И ИСПРАВЛЕНИЕ platform_detector.py

echo "🔍 ПРОВЕРКА platform_detector.py"

# Переход в директорию проекта
cd /opt/telegram-bot

# Проверка текущего файла
echo "📋 Проверяю текущий platform_detector.py..."
if grep -q "def detect_platform" platform_detector.py; then
    echo "✅ Метод detect_platform найден"
else
    echo "❌ Метод detect_platform НЕ найден"
fi

# Скачивание правильного файла
echo "📥 Скачиваю правильный platform_detector.py..."
curl -fsSL https://raw.githubusercontent.com/goqorhopar/b24/main/platform_detector.py -o platform_detector.py

# Проверка скачанного файла
echo "🔍 Проверяю скачанный файл..."
if grep -q "def detect_platform" platform_detector.py; then
    echo "✅ Метод detect_platform найден в скачанном файле"
else
    echo "❌ Метод detect_platform НЕ найден в скачанном файле"
fi

# Очистка кеша Python
echo "🧹 Очищаю кеш Python..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Перезапуск бота
echo "🔄 Перезапускаю бота..."
systemctl restart telegram-bot

# Проверка статуса
echo "✅ Проверяю статус бота..."
sleep 3
systemctl status telegram-bot --no-pager

echo "🎉 ПРОВЕРКА ЗАВЕРШЕНА!"
