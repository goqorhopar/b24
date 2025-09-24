#!/bin/bash

# Скрипт для настройки VPS для развертывания Meeting Bot Assistant

set -e

# Конфигурация
VPS_USER="deploy"
VPS_GROUP="deploy"
APP_DIR="/opt/meetingbot"
DATA_DIR="/data/meetingbot"
LOGS_DIR="/var/log/meetingbot"
SERVICE_NAME="meeting-bot"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Функция проверки прав root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Функция обновления системы
update_system() {
    log "Updating system packages"
    
    # Обновление списка пакетов
    apt-get update -y
    
    # Обновление установленных пакетов
    apt-get upgrade -y
    
    # Установка базовых пакетов
    apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        htop \
        vim \
        nano \
        ufw \
        fail2ban \
        logrotate \
        cron \
        rsync \
        tar \
        gzip
}

# Функция установки Docker
install_docker() {
    log "Installing Docker"
    
    # Удаление старых версий Docker
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Установка зависимостей
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    # Добавление GPG ключа Docker
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Добавление репозитория Docker
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Обновление списка пакетов
    apt-get update -y
    
    # Установка Docker
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Запуск и включение Docker
    systemctl start docker
    systemctl enable docker
    
    # Проверка установки
    docker --version
    docker compose version
}

# Функция создания пользователя deploy
create_deploy_user() {
    log "Creating deploy user"
    
    # Создание группы
    if ! getent group "$VPS_GROUP" > /dev/null 2>&1; then
        groupadd "$VPS_GROUP"
    fi
    
    # Создание пользователя
    if ! getent passwd "$VPS_USER" > /dev/null 2>&1; then
        useradd -m -s /bin/bash -g "$VPS_GROUP" "$VPS_USER"
    fi
    
    # Добавление пользователя в группу docker
    usermod -aG docker "$VPS_USER"
    
    # Настройка sudo без пароля для Docker команд
    echo "$VPS_USER ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/docker-compose, /usr/local/bin/docker-compose" > /etc/sudoers.d/docker-deploy
    
    # Создание SSH директории
    mkdir -p "/home/$VPS_USER/.ssh"
    chmod 700 "/home/$VPS_USER/.ssh"
    chown "$VPS_USER:$VPS_GROUP" "/home/$VPS_USER/.ssh"
}

# Функция настройки SSH
setup_ssh() {
    log "Configuring SSH"
    
    # Резервное копирование конфигурации SSH
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Настройка SSH
    cat >> /etc/ssh/sshd_config << 'EOF'

# Meeting Bot Assistant SSH Configuration
Port 22
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxSessions 10
ClientAliveInterval 300
ClientAliveCountMax 2
EOF
    
    # Перезапуск SSH
    systemctl restart sshd
    
    log "SSH configured. Make sure to add your public key to /home/$VPS_USER/.ssh/authorized_keys"
}

# Функция настройки firewall
setup_firewall() {
    log "Configuring firewall"
    
    # Сброс правил
    ufw --force reset
    
    # Настройка по умолчанию
    ufw default deny incoming
    ufw default allow outgoing
    
    # Разрешение SSH
    ufw allow 22/tcp
    
    # Разрешение HTTP и HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Разрешение порта приложения
    ufw allow 3000/tcp
    
    # Включение firewall
    ufw --force enable
    
    # Проверка статуса
    ufw status
}

# Функция настройки fail2ban
setup_fail2ban() {
    log "Configuring fail2ban"
    
    # Создание конфигурации для SSH
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF
    
    # Запуск и включение fail2ban
    systemctl start fail2ban
    systemctl enable fail2ban
    
    # Проверка статуса
    fail2ban-client status
}

# Функция создания директорий
create_directories() {
    log "Creating application directories"
    
    # Создание директорий
    mkdir -p "$APP_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "/opt/meetingbot/backups"
    
    # Установка прав доступа
    chown -R "$VPS_USER:$VPS_GROUP" "$APP_DIR"
    chown -R "$VPS_USER:$VPS_GROUP" "$DATA_DIR"
    chown -R "$VPS_USER:$VPS_GROUP" "$LOGS_DIR"
    chown -R "$VPS_USER:$VPS_GROUP" "/opt/meetingbot/backups"
    
    # Установка прав доступа
    chmod 755 "$APP_DIR"
    chmod 755 "$DATA_DIR"
    chmod 755 "$LOGS_DIR"
    chmod 755 "/opt/meetingbot/backups"
}

# Функция настройки logrotate
setup_logrotate() {
    log "Configuring log rotation"
    
    cat > /etc/logrotate.d/meeting-bot << EOF
$LOGS_DIR/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $VPS_USER $VPS_GROUP
    postrotate
        /bin/kill -USR1 \$(cat /var/run/meeting-bot.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
}

# Функция настройки cron
setup_cron() {
    log "Configuring cron jobs"
    
    # Создание cron заданий для пользователя deploy
    cat > "/home/$VPS_USER/crontab" << 'EOF'
# Meeting Bot Assistant cron jobs

# Backup and cleanup every day at 2 AM
0 2 * * * /opt/meetingbot/scripts/backup_old.sh

# Health check every 5 minutes
*/5 * * * * /opt/meetingbot/scripts/healthcheck.sh

# Log rotation check every hour
0 * * * * /usr/sbin/logrotate /etc/logrotate.d/meeting-bot

# System cleanup every week
0 3 * * 0 /opt/meetingbot/scripts/cleanup_system.sh
EOF
    
    # Установка cron заданий
    crontab -u "$VPS_USER" "/home/$VPS_USER/crontab"
    
    # Удаление временного файла
    rm "/home/$VPS_USER/crontab"
}

# Функция создания systemd сервиса
create_systemd_service() {
    log "Creating systemd service"
    
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Meeting Bot Assistant
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose restart
TimeoutStartSec=0
User=$VPS_USER
Group=$VPS_GROUP

[Install]
WantedBy=multi-user.target
EOF
    
    # Перезагрузка systemd
    systemctl daemon-reload
    
    # Включение сервиса
    systemctl enable "$SERVICE_NAME"
}

# Функция настройки мониторинга
setup_monitoring() {
    log "Setting up monitoring"
    
    # Создание скрипта мониторинга
    cat > "/opt/meetingbot/scripts/monitor.sh" << 'EOF'
#!/bin/bash

# Мониторинг Meeting Bot Assistant

CONTAINER_NAME="meeting-bot-assistant"
LOG_FILE="/var/log/meetingbot/monitor.log"
MAX_RESTARTS=3
RESTART_COUNT_FILE="/tmp/meeting-bot-restart-count"

# Функция логирования
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Проверка статуса контейнера
if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    log "Container $CONTAINER_NAME is not running"
    
    # Увеличение счетчика перезапусков
    restart_count=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo "0")
    restart_count=$((restart_count + 1))
    echo "$restart_count" > "$RESTART_COUNT_FILE"
    
    if [ "$restart_count" -le "$MAX_RESTARTS" ]; then
        log "Attempting to restart container (attempt $restart_count/$MAX_RESTARTS)"
        cd /opt/meetingbot
        docker compose up -d
        log "Container restart attempted"
    else
        log "Maximum restart attempts reached. Manual intervention required."
        # Отправка уведомления (если настроено)
        # curl -X POST "https://api.telegram.org/bot\$TELEGRAM_BOT_TOKEN/sendMessage" \
        #     -d "chat_id=\$NOTIFICATION_CHAT_ID" \
        #     -d "text=Meeting Bot Assistant is down and requires manual intervention"
    fi
else
    # Сброс счетчика перезапусков
    echo "0" > "$RESTART_COUNT_FILE"
    log "Container $CONTAINER_NAME is running normally"
fi
EOF
    
    # Установка прав доступа
    chmod +x "/opt/meetingbot/scripts/monitor.sh"
    chown "$VPS_USER:$VPS_GROUP" "/opt/meetingbot/scripts/monitor.sh"
    
    # Добавление в cron
    echo "*/2 * * * * /opt/meetingbot/scripts/monitor.sh" | crontab -u "$VPS_USER" -
}

# Функция создания .env файла
create_env_file() {
    log "Creating .env file template"
    
    cat > "$APP_DIR/.env" << 'EOF'
# Meeting Bot Assistant Environment Configuration
# Copy this file and fill in your actual values

# Basic Settings
NODE_ENV=production
PORT=3000
HOST=0.0.0.0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_WEBHOOK_URL=https://your-domain.com
TELEGRAM_WEBHOOK_SECRET=your_webhook_secret_here

# Bitrix24
BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/1/your_webhook_code/
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1
BITRIX_TASK_DEADLINE_DAYS=3

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI (Whisper STT)
OPENAI_API_KEY=your_openai_api_key_here

# Audio Settings
AUDIO_RECORDING_DURATION=3600000
AUDIO_FORMAT=wav
AUDIO_SAMPLE_RATE=16000
AUDIO_CHANNELS=1

# Paths
DATA_DIR=/data/meetingbot
LOGS_DIR=/var/log/meetingbot
AUDIO_DIR=/data/meetingbot/audio
TEMP_DIR=/tmp

# Logging
LOG_LEVEL=info
LOG_MAX_SIZE=10m
LOG_MAX_FILES=5

# Database
DATABASE_URL=sqlite:/data/meetingbot/meetingbot.db

# Security
JWT_SECRET=your_jwt_secret_key_here
API_RATE_LIMIT=100
API_RATE_WINDOW=900000

# Notifications
NOTIFICATION_TELEGRAM_CHAT_ID=your_telegram_chat_id_here
NOTIFICATION_ENABLED=true

# Monitoring
HEALTH_CHECK_INTERVAL=300000
METRICS_ENABLED=true
EOF
    
    # Установка прав доступа
    chmod 600 "$APP_DIR/.env"
    chown "$VPS_USER:$VPS_GROUP" "$APP_DIR/.env"
}

# Функция создания docker-compose.yml
create_docker_compose() {
    log "Creating docker-compose.yml"
    
    cat > "$APP_DIR/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  meeting-bot:
    image: ghcr.io/your-username/meeting-bot-assistant:latest
    container_name: meeting-bot-assistant
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "3000:3000"
    volumes:
      - /data/meetingbot:/data
      - /var/log/meetingbot:/var/log/meetingbot
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - /dev/snd:/dev/snd:rw
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    healthcheck:
      test: ["CMD", "node", "scripts/healthcheck.js"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF
    
    # Установка прав доступа
    chown "$VPS_USER:$VPS_GROUP" "$APP_DIR/docker-compose.yml"
}

# Функция финальной настройки
final_setup() {
    log "Performing final setup"
    
    # Создание скрипта для быстрого управления
    cat > "/opt/meetingbot/manage.sh" << 'EOF'
#!/bin/bash

# Meeting Bot Assistant Management Script

APP_DIR="/opt/meetingbot"
SERVICE_NAME="meeting-bot"

case "$1" in
    start)
        echo "Starting Meeting Bot Assistant..."
        cd "$APP_DIR"
        docker compose up -d
        systemctl start "$SERVICE_NAME"
        ;;
    stop)
        echo "Stopping Meeting Bot Assistant..."
        cd "$APP_DIR"
        docker compose down
        systemctl stop "$SERVICE_NAME"
        ;;
    restart)
        echo "Restarting Meeting Bot Assistant..."
        cd "$APP_DIR"
        docker compose restart
        systemctl restart "$SERVICE_NAME"
        ;;
    status)
        echo "Meeting Bot Assistant Status:"
        systemctl status "$SERVICE_NAME"
        echo ""
        echo "Container Status:"
        docker ps -f name=meeting-bot-assistant
        ;;
    logs)
        echo "Meeting Bot Assistant Logs:"
        docker logs meeting-bot-assistant --tail 50 -f
        ;;
    update)
        echo "Updating Meeting Bot Assistant..."
        cd "$APP_DIR"
        docker compose pull
        docker compose up -d
        ;;
    backup)
        echo "Creating backup..."
        /opt/meetingbot/scripts/backup_old.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|update|backup}"
        exit 1
        ;;
esac
EOF
    
    # Установка прав доступа
    chmod +x "/opt/meetingbot/manage.sh"
    chown "$VPS_USER:$VPS_GROUP" "/opt/meetingbot/manage.sh"
    
    # Создание символической ссылки
    ln -sf "/opt/meetingbot/manage.sh" "/usr/local/bin/meeting-bot"
}

# Функция вывода итоговой информации
show_summary() {
    log "VPS setup completed successfully!"
    echo ""
    info "Next steps:"
    echo "1. Add your SSH public key to /home/$VPS_USER/.ssh/authorized_keys"
    echo "2. Edit /opt/meetingbot/.env with your actual configuration"
    echo "3. Update docker-compose.yml with your image name"
    echo "4. Test the setup with: meeting-bot status"
    echo ""
    info "Useful commands:"
    echo "  meeting-bot start    - Start the application"
    echo "  meeting-bot stop     - Stop the application"
    echo "  meeting-bot restart  - Restart the application"
    echo "  meeting-bot status   - Check application status"
    echo "  meeting-bot logs     - View application logs"
    echo "  meeting-bot update   - Update application"
    echo "  meeting-bot backup   - Create backup"
    echo ""
    info "Important files:"
    echo "  Configuration: /opt/meetingbot/.env"
    echo "  Docker Compose: /opt/meetingbot/docker-compose.yml"
    echo "  Logs: /var/log/meetingbot/"
    echo "  Data: /data/meetingbot/"
    echo "  Backups: /opt/meetingbot/backups/"
    echo ""
    warn "Remember to:"
    echo "  - Configure your .env file with real values"
    echo "  - Set up SSL certificates if using HTTPS"
    echo "  - Configure your domain DNS to point to this server"
    echo "  - Test the application before going live"
}

# Основная функция
main() {
    log "Starting VPS setup for Meeting Bot Assistant"
    
    # Проверка прав root
    check_root
    
    # Обновление системы
    update_system
    
    # Установка Docker
    install_docker
    
    # Создание пользователя deploy
    create_deploy_user
    
    # Настройка SSH
    setup_ssh
    
    # Настройка firewall
    setup_firewall
    
    # Настройка fail2ban
    setup_fail2ban
    
    # Создание директорий
    create_directories
    
    # Настройка logrotate
    setup_logrotate
    
    # Настройка cron
    setup_cron
    
    # Создание systemd сервиса
    create_systemd_service
    
    # Настройка мониторинга
    setup_monitoring
    
    # Создание .env файла
    create_env_file
    
    # Создание docker-compose.yml
    create_docker_compose
    
    # Финальная настройка
    final_setup
    
    # Вывод итоговой информации
    show_summary
}

# Обработка аргументов командной строки
case "${1:-}" in
    --help)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  --help    Show this help"
        echo ""
        echo "This script sets up a VPS for Meeting Bot Assistant deployment."
        echo "It must be run as root."
        exit 0
        ;;
    *)
        main
        ;;
esac
