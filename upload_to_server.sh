#!/bin/bash

echo "📤 ЗАГРУЗКА ФАЙЛОВ НА СЕРВЕР"
echo "============================="

SERVER="109.172.47.253"
USER="root"

echo "🔗 Подключение к серверу $SERVER..."

# Создание директории на сервере
ssh $USER@$SERVER "mkdir -p /root/b24"

# Загрузка файлов автономного бота
echo "📋 Загрузка файлов..."

scp autonomous_server_bot.py $USER@$SERVER:/root/b24/
scp meeting-bot-autonomous.service $USER@$SERVER:/root/b24/
scp deploy_autonomous_server.sh $USER@$SERVER:/root/b24/
scp requirements.txt $USER@$SERVER:/root/b24/

# Установка прав на выполнение
ssh $USER@$SERVER "chmod +x /root/b24/deploy_autonomous_server.sh"

echo "✅ Файлы загружены!"
echo ""
echo "🚀 Теперь запустите на сервере:"
echo "   cd /root/b24"
echo "   sudo ./deploy_autonomous_server.sh"
