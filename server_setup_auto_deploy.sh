#!/bin/bash

echo "🔧 НАСТРОЙКА СЕРВЕРА ДЛЯ АВТОМАТИЧЕСКОГО ДЕПЛОЯ"
echo "==============================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт от имени root: sudo $0"
    exit 1
fi

# Установка Git если не установлен
if ! command -v git &> /dev/null; then
    echo "📦 Установка Git..."
    apt update
    apt install -y git
fi

# Создание директории
BOT_DIR="/root/b24"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

echo "🔑 Настройка SSH ключей для GitHub..."

# Создание SSH ключа если не существует
if [ ! -f "/root/.ssh/id_rsa" ]; then
    echo "🔑 Генерация SSH ключа..."
    ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""
    echo "✅ SSH ключ создан: /root/.ssh/id_rsa.pub"
    echo ""
    echo "📋 Добавьте этот публичный ключ в GitHub:"
    echo "1. Перейдите в GitHub → Settings → SSH and GPG keys"
    echo "2. Нажмите 'New SSH key'"
    echo "3. Скопируйте содержимое файла /root/.ssh/id_rsa.pub"
    echo ""
    cat /root/.ssh/id_rsa.pub
    echo ""
    read -p "Нажмите Enter после добавления ключа в GitHub..."
fi

# Настройка Git
echo "⚙️ Настройка Git..."
git config --global user.name "Server Bot"
git config --global user.email "bot@server.local"

# Клонирование репозитория (замените на ваш)
echo "📥 Клонирование репозитория..."
echo "Введите URL вашего GitHub репозитория:"
read -p "GitHub URL: " GITHUB_URL

if [ -z "$GITHUB_URL" ]; then
    echo "❌ URL репозитория не указан"
    exit 1
fi

# Клонирование или обновление
if [ -d ".git" ]; then
    echo "🔄 Обновление существующего репозитория..."
    git remote set-url origin "$GITHUB_URL"
    git pull origin main
else
    echo "📥 Клонирование репозитория..."
    git clone "$GITHUB_URL" .
fi

# Установка зависимостей
echo "🔧 Установка зависимостей..."
pip3 install requests google-generativeai

# Настройка systemd сервиса
echo "⚙️ Настройка systemd сервиса..."
if [ -f "meeting-bot-autonomous.service" ]; then
    cp meeting-bot-autonomous.service /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable meeting-bot-autonomous.service
fi

# Запуск бота
echo "🚀 Запуск автономного бота..."
systemctl start meeting-bot-autonomous.service

# Проверка статуса
echo "📊 Проверка статуса..."
sleep 5
systemctl status meeting-bot-autonomous.service --no-pager

echo ""
echo "✅ СЕРВЕР НАСТРОЕН ДЛЯ АВТОМАТИЧЕСКОГО ДЕПЛОЯ!"
echo "============================================="
echo ""
echo "🎯 Теперь работает автоматическая синхронизация:"
echo "   1. Изменения в файлах → GitHub"
echo "   2. GitHub Actions → Автоматический деплой на сервер"
echo "   3. Бот обновляется без вашего участия!"
echo ""
echo "📋 Команды управления:"
echo "   systemctl status meeting-bot-autonomous.service  # Статус"
echo "   journalctl -u meeting-bot-autonomous.service -f   # Логи"
echo "   git pull origin main                              # Ручное обновление"
echo ""
echo "🤖 БОТ РАБОТАЕТ АВТОНОМНО И ОБНОВЛЯЕТСЯ АВТОМАТИЧЕСКИ!"
