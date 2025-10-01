#!/bin/bash
# Автоматический деплой Meeting Bot на сервер

echo "🚀 Автоматический деплой Meeting Bot"
echo "=================================="

# Проверяем наличие файлов авторизации
if [ ! -f "selenium_cookies.json" ] || [ ! -f "storage.json" ]; then
    echo "❌ Файлы авторизации не найдены!"
    echo "Запустите: python simple_auth.py"
    exit 1
fi

echo "✅ Файлы авторизации найдены"

# Клонируем репозиторий на сервере
echo "📥 Клонирование репозитория..."
git clone https://github.com/goqorhopar/b24.git /tmp/b24-deploy
cd /tmp/b24-deploy

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Копируем файлы авторизации
echo "🔐 Копирование файлов авторизации..."
cp /path/to/local/selenium_cookies.json ./
cp /path/to/local/storage.json ./
cp /path/to/local/cookies_*.json ./
cp /path/to/local/storage_*.json ./

# Проверяем авторизацию
echo "🧪 Тестирование авторизации..."
python3 check_auth.py

# Запускаем бота
echo "🤖 Запуск бота..."
python3 meeting-bot.py
