#!/bin/bash

# Скрипт для деплоя Telegram бота на VPS Beget
# IP: 109.172.47.253, User: root, Password: MmSS0JSm%6vb

set -e

VPS_IP="109.172.47.253"
VPS_USER="root"
VPS_PASSWORD="MmSS0JSm%6vb"
PROJECT_NAME="telegram-bot"
PROJECT_DIR="/opt/$PROJECT_NAME"

echo "🚀 Деплой Telegram бота на VPS Beget ($VPS_IP)"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем наличие sshpass
if ! command -v sshpass &> /dev/null; then
    log_error "sshpass не установлен. Устанавливаем..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install hudochenkov/sshpass/sshpass
        else
            log_error "Homebrew не найден. Установите sshpass вручную."
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y sshpass
    else
        log_error "Не удалось установить sshpass. Установите вручную."
        exit 1
    fi
fi

# Функция для выполнения команд на VPS
run_ssh() {
    sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "$VPS_USER@$VPS_IP" "$1"
}

# Функция для копирования файлов
copy_files() {
    sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r "$1" "$VPS_USER@$VPS_IP:$2"
}

log_info "Проверяем подключение к VPS..."
if run_ssh "echo 'Подключение успешно'"; then
    log_success "Подключение к VPS установлено"
else
    log_error "Не удалось подключиться к VPS"
    exit 1
fi

log_info "Обновляем систему и устанавливаем зависимости..."
run_ssh "apt update && apt upgrade -y"
run_ssh "apt install -y python3 python3-pip python3-venv git nginx ufw curl wget"

log_info "Создаем директорию проекта..."
run_ssh "mkdir -p $PROJECT_DIR"

log_info "Копируем файлы проекта..."
copy_files "./" "$PROJECT_DIR/"

log_info "Настраиваем Python окружение..."
run_ssh "cd $PROJECT_DIR && python3 -m venv venv"
run_ssh "cd $PROJECT_DIR && source venv/bin/activate && pip install --upgrade pip"
run_ssh "cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt"

log_info "Создаем systemd сервис..."
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
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

log_info "Настраиваем nginx..."
run_ssh "cat > /etc/nginx/sites-available/telegram-bot << 'EOF'
server {
    listen 80;
    server_name $VPS_IP;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF"

run_ssh "ln -sf /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/"
run_ssh "rm -f /etc/nginx/sites-enabled/default"
run_ssh "nginx -t"
run_ssh "systemctl reload nginx"

log_info "Настраиваем файрвол..."
run_ssh "ufw allow 22"
run_ssh "ufw allow 80"
run_ssh "ufw allow 443"
run_ssh "ufw --force enable"

log_info "Запускаем сервис..."
run_ssh "systemctl daemon-reload"
run_ssh "systemctl enable telegram-bot"
run_ssh "systemctl start telegram-bot"

log_success "Деплой завершен!"
echo ""
echo "🌐 Приложение доступно по адресу: http://$VPS_IP"
echo "📊 Статус сервиса:"
run_ssh "systemctl status telegram-bot --no-pager -l"

echo ""
log_warning "ВАЖНО: Не забудьте настроить .env файл с вашими токенами!"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "📋 Для проверки логов:"
echo "   journalctl -u telegram-bot -f"
echo ""
echo "🔧 Для перезапуска сервиса:"
echo "   systemctl restart telegram-bot"
