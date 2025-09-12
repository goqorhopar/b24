#!/bin/bash

# Автоматический деплой Telegram бота на VPS
# Использование: ./deploy_script.sh

set -e

VPS_IP="109.172.47.253"
VPS_USER="root"
VPS_PASSWORD="MmSS0JSm%6vb"
PROJECT_DIR="/opt/telegram-bot"

echo "🚀 Начинаем деплой Telegram бота на VPS $VPS_IP"

# Проверяем наличие sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass не установлен. Устанавливаем..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install hudochenkov/sshpass/sshpass
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        echo "❌ Не удалось установить sshpass. Установите вручную."
        exit 1
    fi
fi

# Функция для выполнения команд на VPS
run_ssh() {
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "$1"
}

# Функция для копирования файлов
copy_files() {
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no -r "$1" "$VPS_USER@$VPS_IP:$2"
}

echo "📋 Проверяем подключение к VPS..."
run_ssh "echo 'Подключение успешно'"

echo "🔧 Обновляем систему и устанавливаем зависимости..."
run_ssh "apt update && apt install -y python3 python3-pip python3-venv git nginx ufw"

echo "📁 Создаем директорию проекта..."
run_ssh "mkdir -p $PROJECT_DIR"

echo "📤 Копируем файлы проекта..."
copy_files "./" "$PROJECT_DIR/"

echo "🐍 Настраиваем Python окружение..."
run_ssh "cd $PROJECT_DIR && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

echo "⚙️ Создаем systemd сервис..."
run_ssh "cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

echo "🌐 Настраиваем nginx..."
run_ssh "cat > /etc/nginx/sites-available/telegram-bot << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

run_ssh "ln -sf /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/ && nginx -t && systemctl reload nginx"

echo "🔥 Настраиваем файрвол..."
run_ssh "ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw --force enable"

echo "🚀 Запускаем сервис..."
run_ssh "systemctl daemon-reload && systemctl enable telegram-bot && systemctl start telegram-bot"

echo "✅ Деплой завершен!"
echo "🌐 Приложение доступно по адресу: http://$VPS_IP"
echo "📊 Статус сервиса:"
run_ssh "systemctl status telegram-bot --no-pager"

echo ""
echo "⚠️  ВАЖНО: Не забудьте настроить .env файл с вашими токенами!"
echo "   nano $PROJECT_DIR/.env"
