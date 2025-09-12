#!/bin/bash

# Скрипт для деплоя Telegram бота на VPS сервер
# IP: 109.172.47.253
# User: root
# Password: MmSS0JSm%6vb

set -e

VPS_IP="109.172.47.253"
VPS_USER="root"
VPS_PASSWORD="MmSS0JSm%6vb"
PROJECT_NAME="telegram-bot"

echo "🚀 Начинаем деплой на VPS сервер $VPS_IP"

# Функция для выполнения команд на VPS
run_on_vps() {
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Функция для копирования файлов на VPS
copy_to_vps() {
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$VPS_USER@$VPS_IP:$2"
}

echo "📋 Проверяем систему на VPS..."
run_on_vps "uname -a && python3 --version && pip3 --version"

echo "📁 Создаем директорию проекта..."
run_on_vps "mkdir -p /opt/$PROJECT_NAME"

echo "📤 Копируем файлы проекта..."
copy_to_vps "./" "/opt/$PROJECT_NAME/"

echo "🔧 Устанавливаем зависимости..."
run_on_vps "cd /opt/$PROJECT_NAME && pip3 install -r requirements.txt"

echo "✅ Деплой завершен!"
echo "🌐 Для запуска приложения выполните:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   cd /opt/$PROJECT_NAME"
echo "   python3 main.py"
