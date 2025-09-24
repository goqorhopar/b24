#!/bin/bash

# Meeting Bot Assistant - Автоматический скрипт развертывания
# Этот скрипт автоматически развертывает бота на сервере

set -e

echo "🚀 Начинаю развертывание Meeting Bot Assistant..."

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с правами root: sudo $0"
    exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка Docker
echo "🐳 Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Установка Docker Compose
echo "🐳 Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Создание директории проекта
echo "📁 Создание директории проекта..."
mkdir -p /opt/meeting-bot
cd /opt/meeting-bot

# Копирование файлов проекта
echo "📋 Копирование файлов проекта..."
if [ -d "/root/b24" ]; then
    cp -r /root/b24/* /opt/meeting-bot/
else
    echo "❌ Директория /root/b24 не найдена. Скопируйте файлы проекта вручную."
    exit 1
fi

# Создание .env файла
echo "⚙️ Создание .env файла..."
cat > .env << 'EOF'
NODE_ENV=production
PORT=3000
HOST=0.0.0.0
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
ADMIN_CHAT_ID=7537953397
PUPPETEER_HEADLESS=true
TZ=Europe/Moscow
EOF

# Создание systemd сервиса
echo "🔧 Создание systemd сервиса..."
cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/meeting-bot
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Включение сервиса
echo "🔄 Включение сервиса..."
systemctl daemon-reload
systemctl enable meeting-bot.service

# Запуск сервиса
echo "🚀 Запуск сервиса..."
systemctl start meeting-bot.service

# Проверка статуса
echo "📊 Проверка статуса..."
sleep 10
systemctl status meeting-bot.service --no-pager

# Проверка контейнеров
echo "🐳 Проверка контейнеров..."
docker-compose ps

# Проверка логов
echo "📋 Последние логи..."
docker-compose logs --tail=20

echo "✅ Развертывание завершено!"
echo ""
echo "📊 Статус сервиса:"
echo "• systemctl status meeting-bot"
echo "• docker-compose ps"
echo "• docker-compose logs -f"
echo ""
echo "🔧 Управление:"
echo "• systemctl start meeting-bot"
echo "• systemctl stop meeting-bot"
echo "• systemctl restart meeting-bot"
echo ""
echo "📋 Логи:"
echo "• journalctl -u meeting-bot -f"
echo "• docker-compose logs -f"
echo ""
echo "🎉 Meeting Bot Assistant готов к работе!"