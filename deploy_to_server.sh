#!/bin/bash

echo "🚀 АВТОМАТИЧЕСКИЙ ДЕПЛОЙ НА СЕРВЕР"
echo "БЕЗ УЧАСТИЯ ПОЛЬЗОВАТЕЛЯ!"

# Определяем IP сервера (замените на ваш)
SERVER_IP="YOUR_SERVER_IP"
SERVER_USER="root"

echo "📡 Подключение к серверу $SERVER_IP..."

# Копируем файлы на сервер
scp autonomous_bot.py $SERVER_USER@$SERVER_IP:/root/b24/
scp meeting-bot.service $SERVER_USER@$SERVER_IP:/etc/systemd/system/
scp auto_deploy.sh $SERVER_USER@$SERVER_IP:/root/b24/

# Запускаем автоматический деплой на сервере
ssh $SERVER_USER@$SERVER_IP "cd /root/b24 && chmod +x auto_deploy.sh && ./auto_deploy.sh"

echo "✅ ДЕПЛОЙ ЗАВЕРШЕН АВТОМАТИЧЕСКИ!"
echo "🤖 Бот работает на сервере без вашего участия!"
