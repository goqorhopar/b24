#!/bin/bash
# Скрипт установки Meeting Bot на VPS Beget

set -e

echo "🚀 Установка Meeting Bot на VPS..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запустите скрипт с правами root: sudo bash install.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Права root подтверждены${NC}"

# Обновление системы
echo -e "${YELLOW}📦 Обновление системы...${NC}"
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo -e "${YELLOW}📦 Установка зависимостей...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    ffmpeg \
    pulseaudio \
    chromium-browser \
    chromium-chromedriver \
    wget \
    curl \
    unzip

# Альтернативная установка Chrome (если Chromium не работает)
if ! command -v google-chrome &> /dev/null; then
    echo -e "${YELLOW}📦 Установка Google Chrome...${NC}"
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    apt-get install -y ./google-chrome-stable_current_amd64.deb || true
    rm google-chrome-stable_current_amd64.deb
fi

# Создание пользователя для бота
if ! id "bot" &>/dev/null; then
    echo -e "${YELLOW}👤 Создание пользователя bot...${NC}"
    useradd -m -s /bin/bash bot
    usermod -aG audio,pulse,pulse-access bot
    echo -e "${GREEN}✅ Пользователь bot создан${NC}"
else
    echo -e "${GREEN}✅ Пользователь bot уже существует${NC}"
fi

# Создание рабочей директории
WORK_DIR="/opt/meeting-bot"
echo -e "${YELLOW}📁 Создание рабочей директории: ${WORK_DIR}${NC}"
mkdir -p ${WORK_DIR}
mkdir -p ${WORK_DIR}/recordings
mkdir -p /var/log/meeting-bot

# Клонирование репозитория (если еще не клонирован)
if [ ! -d "${WORK_DIR}/.git" ]; then
    echo -e "${YELLOW}📥 Клонирование репозитория...${NC}"
    cd ${WORK_DIR}
    # Замените на ваш репозиторий
    git clone https://github.com/goqorhopar/b24.git .
else
    echo -e "${YELLOW}🔄 Обновление репозитория...${NC}"
    cd ${WORK_DIR}
    git pull
fi

# Создание виртуального окружения
echo -e "${YELLOW}🐍 Создание виртуального окружения Python...${NC}"
cd ${WORK_DIR}
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo -e "${YELLOW}📦 Установка Python пакетов...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Настройка PulseAudio для headless режима
echo -e "${YELLOW}🔊 Настройка PulseAudio...${NC}"
mkdir -p /home/bot/.config/pulse
cat > /home/bot/.config/pulse/client.conf << 'EOF'
autospawn = yes
daemon-binary = /usr/bin/pulseaudio
extra-arguments = --log-target=syslog --exit-idle-time=-1
EOF

cat > /home/bot/.config/pulse/default.pa << 'EOF'
#!/usr/bin/pulseaudio -nF

# Load modules
load-module module-native-protocol-unix
load-module module-null-sink sink_name=virtual_speaker
load-module module-virtual-source source_name=virtual_mic
load-module module-loopback source=virtual_mic sink=virtual_speaker

# Set defaults
set-default-sink virtual_speaker
set-default-source virtual_mic
EOF

# Создание .env файла (шаблон)
if [ ! -f "${WORK_DIR}/.env" ]; then
    echo -e "${YELLOW}📝 Создание .env файла...${NC}"
    cat > ${WORK_DIR}/.env << 'EOF'
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# GitHub
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=goqorhopar/b24

# Bot Settings
BOT_NAME=MeetingBot
RECORD_DIR=/opt/meeting-bot/recordings
WHISPER_MODEL=medium
MEETING_TIMEOUT_MIN=180
EOF
    echo -e "${RED}⚠️  ВАЖНО: Отредактируйте файл ${WORK_DIR}/.env и добавьте ваши токены!${NC}"
else
    echo -e "${GREEN}✅ Файл .env уже существует${NC}"
fi

# Создание systemd сервиса
echo -e "${YELLOW}⚙️  Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/meeting-bot.service << EOF
[Unit]
Description=Meeting Bot Service
After=network.target pulseaudio.service

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=${WORK_DIR}
Environment="PATH=${WORK_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PULSE_SERVER=unix:/run/user/$(id -u bot)/pulse/native"
ExecStartPre=/bin/sleep 5
ExecStart=${WORK_DIR}/venv/bin/python3 ${WORK_DIR}/meeting-bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/meeting-bot/output.log
StandardError=append:/var/log/meeting-bot/error.log

[Install]
WantedBy=multi-user.target
EOF

# Настройка прав доступа
echo -e "${YELLOW}🔐 Настройка прав доступа...${NC}"
chown -R bot:bot ${WORK_DIR}
chown -R bot:bot /home/bot/.config/pulse
chown -R bot:bot /var/log/meeting-bot
chmod +x ${WORK_DIR}/meeting-bot.py
chmod 600 ${WORK_DIR}/.env

# Включение и запуск сервиса
echo -e "${YELLOW}🚀 Включение сервиса...${NC}"
systemctl daemon-reload
systemctl enable meeting-bot.service

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Установка завершена успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📋 Следующие шаги:${NC}"
echo ""
echo -e "1. Отредактируйте файл с токенами:"
echo -e "   ${YELLOW}nano ${WORK_DIR}/.env${NC}"
echo ""
echo -e "2. Добавьте ваши токены:"
echo -e "   - TELEGRAM_BOT_TOKEN (от @BotFather)"
echo -e "   - TELEGRAM_CHAT_ID (ваш Telegram ID)"
echo -e "   - GITHUB_TOKEN (Personal Access Token)"
echo ""
echo -e "3. Запустите бота:"
echo -e "   ${YELLOW}systemctl start meeting-bot${NC}"
echo ""
echo -e "4. Проверьте статус:"
echo -e "   ${YELLOW}systemctl status meeting-bot${NC}"
echo ""
echo -e "5. Просмотр логов:"
echo -e "   ${YELLOW}tail -f /var/log/meeting-bot/output.log${NC}"
echo -e "   ${YELLOW}journalctl -u meeting-bot -f${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
