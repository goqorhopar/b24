#!/bin/bash

# Скрипт для первоначальной настройки VPS для деплоя через GitHub Actions
# Запускать на VPS от имени пользователя с sudo правами

set -e

echo "🚀 Настраиваем VPS для автоматического деплоя..."

# Обновляем систему
echo "📦 Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
echo "🔧 Устанавливаем необходимые пакеты..."
sudo apt install -y \
    git \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    wget \
    unzip \
    htop \
    nano \
    vim

# Создаем директорию для проекта
echo "📁 Создаем директорию для проекта..."
sudo mkdir -p /opt/telegram-bot
sudo chown $USER:$USER /opt/telegram-bot

# Настраиваем SSH ключи для GitHub Actions
echo "🔑 Настраиваем SSH ключи..."
if [ ! -f ~/.ssh/github_actions_key ]; then
    ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions_key -N ""
    echo "✅ SSH ключ создан"
else
    echo "⚠️ SSH ключ уже существует"
fi

# Добавляем публичный ключ в authorized_keys
if ! grep -q "$(cat ~/.ssh/github_actions_key.pub)" ~/.ssh/authorized_keys 2>/dev/null; then
    cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
    echo "✅ Публичный ключ добавлен в authorized_keys"
else
    echo "⚠️ Публичный ключ уже в authorized_keys"
fi

# Устанавливаем правильные права
chmod 600 ~/.ssh/github_actions_key
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh

# Клонируем репозиторий (замените URL на ваш)
echo "📥 Клонируем репозиторий..."
cd /opt/telegram-bot

# Запрашиваем URL репозитория
if [ -z "$1" ]; then
    echo "Введите URL вашего GitHub репозитория (например: https://github.com/username/repo.git):"
    read REPO_URL
else
    REPO_URL="$1"
fi

if [ ! -d ".git" ]; then
    git clone "$REPO_URL" .
    echo "✅ Репозиторий клонирован"
else
    echo "⚠️ Репозиторий уже существует, обновляем..."
    git pull origin main
fi

# Создаем виртуальное окружение
echo "🐍 Создаем виртуальное окружение..."
python3.11 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Настраиваем переменные окружения
echo "⚙️ Настраиваем переменные окружения..."
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Создан файл .env из .env.example"
    echo "⚠️ Не забудьте настроить переменные в файле .env!"
    echo "📝 Редактируйте файл: nano /opt/telegram-bot/.env"
else
    echo "⚠️ Файл .env уже существует или .env.example не найден"
fi

# Создаем systemd сервис
echo "🔧 Создаем systemd сервис..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
ExecStart=/opt/telegram-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и включаем сервис
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot

echo "🎉 Настройка VPS завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте переменные в файле .env:"
echo "   nano /opt/telegram-bot/.env"
echo ""
echo "2. Добавьте следующие секреты в GitHub:"
echo "   - VPS_HOST: $(curl -s ifconfig.me || echo 'YOUR_VPS_IP')"
echo "   - VPS_USERNAME: $USER"
echo "   - VPS_SSH_KEY: $(cat ~/.ssh/github_actions_key)"
echo "   - VPS_PORT: 22 (если не стандартный)"
echo ""
echo "3. Для добавления секретов перейдите в:"
echo "   GitHub → Settings → Secrets and variables → Actions"
echo ""
echo "4. Запустите бота:"
echo "   sudo systemctl start telegram-bot"
echo ""
echo "5. Проверьте статус:"
echo "   sudo systemctl status telegram-bot"
echo ""
echo "6. Просмотр логов:"
echo "   sudo journalctl -u telegram-bot -f"
echo ""
echo "🔑 Приватный SSH ключ для GitHub Secrets:"
echo "---"
cat ~/.ssh/github_actions_key
echo "---"
