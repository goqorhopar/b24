#!/bin/bash

# Ручная загрузка файлов на сервер
echo "=== Ручная загрузка Meeting Bot на сервер ==="

# Параметры сервера
SERVER="109.172.47.253"
USER="root"
PASSWORD="MmSS0JSm%6vb"
REMOTE_DIR="/root/b24"

echo "Подключение к серверу $SERVER..."

# Создаем директорию на сервере
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no $USER@$SERVER "mkdir -p $REMOTE_DIR"

# Загружаем основные файлы
echo "Загрузка основных файлов..."

sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no meeting-bot.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no monitor_bot.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no load_auth_data.py $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no meeting_bot_playwright.py $USER@$SERVER:$REMOTE_DIR/

# Загружаем скрипты
echo "Загрузка скриптов..."
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no install_server.sh $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no bot_control.sh $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no server_commands.sh $USER@$SERVER:$REMOTE_DIR/

# Загружаем systemd сервисы
echo "Загрузка systemd сервисов..."
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no meeting-bot.service $USER@$SERVER:$REMOTE_DIR/
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no meeting-bot-monitor.service $USER@$SERVER:$REMOTE_DIR/

# Загружаем requirements.txt
echo "Загрузка зависимостей..."
sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no requirements.txt $USER@$SERVER:$REMOTE_DIR/

# Загружаем файлы авторизации (если есть)
if [ -f "selenium_cookies.json" ]; then
    echo "Загрузка файлов авторизации..."
    sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no selenium_cookies.json $USER@$SERVER:$REMOTE_DIR/
fi

if [ -f "storage.json" ]; then
    sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no storage.json $USER@$SERVER:$REMOTE_DIR/
fi

echo "=== Загрузка завершена ==="
echo ""
echo "Теперь на сервере выполни:"
echo "cd /root/b24"
echo "chmod +x *.sh"
echo "./install_server.sh"
