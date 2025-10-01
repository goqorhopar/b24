#!/bin/bash
# Скрипт для копирования файлов авторизации на сервер

echo "🔐 Копирование файлов авторизации на сервер"
echo "=========================================="

# Проверяем наличие файлов
if [ ! -f "selenium_cookies.json" ] || [ ! -f "storage.json" ]; then
    echo "❌ Файлы авторизации не найдены!"
    echo "Запустите: python simple_auth.py"
    exit 1
fi

# Запрашиваем данные сервера
read -p "Введите IP адрес сервера: " SERVER_IP
read -p "Введите пользователя сервера (root): " SERVER_USER
SERVER_USER=${SERVER_USER:-root}

echo "📤 Копирование файлов на $SERVER_USER@$SERVER_IP..."

# Копируем файлы
scp selenium_cookies.json $SERVER_USER@$SERVER_IP:/opt/meeting-bot/
scp storage.json $SERVER_USER@$SERVER_IP:/opt/meeting-bot/
scp cookies_*.json $SERVER_USER@$SERVER_IP:/opt/meeting-bot/
scp storage_*.json $SERVER_USER@$SERVER_IP:/opt/meeting-bot/

echo "✅ Файлы скопированы!"

# Проверяем авторизацию на сервере
echo "🧪 Проверка авторизации на сервере..."
ssh $SERVER_USER@$SERVER_IP "cd /opt/meeting-bot && python3 check_auth.py"

echo "🎉 Готово! Бот готов к работе на сервере."
