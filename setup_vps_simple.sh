#!/bin/bash

# Простая настройка VPS для деплоя бота
# Запускать на VPS от имени пользователя с sudo правами

set -e

echo "🚀 Настраиваем VPS для бота..."

# Обновляем систему
echo "📦 Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
echo "🔧 Устанавливаем необходимые пакеты..."
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    htop \
    nano

# Создаем директорию для проекта
echo "📁 Создаем директорию для проекта..."
sudo mkdir -p /opt/telegram-bot
sudo chown $USER:$USER /opt/telegram-bot

# Клонируем репозиторий
echo "📥 Клонируем репозиторий..."
cd /opt/telegram-bot
if [ ! -d ".git" ]; then
    echo "Введите URL вашего GitHub репозитория:"
    read REPO_URL
    git clone $REPO_URL .
else
    echo "Репозиторий уже существует, обновляем..."
    git pull origin main
fi

# Делаем скрипт деплоя исполняемым
chmod +x simple_deploy.sh

# Запускаем деплой
echo "🚀 Запускаем деплой..."
./simple_deploy.sh

echo "✅ Настройка VPS завершена!"
echo "📝 Следующие шаги:"
echo "1. Отредактируйте .env файл: nano .env"
echo "2. Запустите бота: sudo systemctl start telegram-bot"
echo "3. Проверьте статус: sudo systemctl status telegram-bot"
