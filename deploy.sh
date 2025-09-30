#!/bin/bash
# Скрипт обновления Meeting Bot на VPS

set -e

echo "🚀 Обновление Meeting Bot на VPS..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Запустите скрипт с правами root: sudo bash deploy.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Права root подтверждены${NC}"

# Рабочая директория
WORK_DIR="/opt/meeting-bot"

# Проверяем, существует ли директория
if [ ! -d "${WORK_DIR}" ]; then
    echo -e "${RED}❌ Директория ${WORK_DIR} не найдена. Сначала запустите install.sh${NC}"
    exit 1
fi

# Остановка сервиса
echo -e "${YELLOW}⏹️  Остановка сервиса...${NC}"
systemctl stop meeting-bot.service || true

# Переход в рабочую директорию
cd ${WORK_DIR}

# Обновление кода из GitHub
echo -e "${YELLOW}📥 Обновление кода из GitHub...${NC}"
git fetch origin
git reset --hard origin/main

# Обновление зависимостей
echo -e "${YELLOW}📦 Обновление Python зависимостей...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Настройка прав доступа
echo -e "${YELLOW}🔐 Настройка прав доступа...${NC}"
chown -R bot:bot ${WORK_DIR}
chmod +x ${WORK_DIR}/meeting-bot.py

# Перезагрузка systemd
echo -e "${YELLOW}⚙️  Перезагрузка systemd...${NC}"
systemctl daemon-reload

# Запуск сервиса
echo -e "${YELLOW}🚀 Запуск сервиса...${NC}"
systemctl start meeting-bot.service

# Проверка статуса
echo -e "${YELLOW}📊 Проверка статуса...${NC}"
sleep 3
systemctl status meeting-bot.service --no-pager

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Обновление завершено успешно!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}📋 Полезные команды:${NC}"
echo ""
echo -e "Проверить статус:"
echo -e "   ${YELLOW}systemctl status meeting-bot${NC}"
echo ""
echo -e "Просмотр логов:"
echo -e "   ${YELLOW}tail -f /var/log/meeting-bot/output.log${NC}"
echo -e "   ${YELLOW}journalctl -u meeting-bot -f${NC}"
echo ""
echo -e "Перезапустить бота:"
echo -e "   ${YELLOW}systemctl restart meeting-bot${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
