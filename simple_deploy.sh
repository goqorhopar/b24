#!/bin/bash

# Простой скрипт деплоя для VPS
# Запуск: chmod +x simple_deploy.sh && ./simple_deploy.sh

VPS_IP="109.172.47.253"
VPS_USER="root"

echo "🚀 Деплой Telegram бота на VPS $VPS_IP"
echo "📋 Подключитесь к серверу и выполните следующие команды:"
echo ""

echo "1️⃣ Подключение к серверу:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   (пароль: MmSS0JSm%6vb)"
echo ""

echo "2️⃣ Обновление системы:"
echo "   apt update && apt upgrade -y"
echo "   apt install -y python3 python3-pip python3-venv git nginx ufw"
echo ""

echo "3️⃣ Создание директории проекта:"
echo "   mkdir -p /opt/telegram-bot"
echo "   cd /opt/telegram-bot"
echo ""

echo "4️⃣ Копирование файлов (выполните на локальной машине):"
echo "   scp -r ./* $VPS_USER@$VPS_IP:/opt/telegram-bot/"
echo ""

echo "5️⃣ Настройка Python окружения:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""

echo "6️⃣ Создание .env файла:"
echo "   nano .env"
echo "   (скопируйте содержимое из env.example и заполните ваши токены)"
echo ""

echo "7️⃣ Создание systemd сервиса:"
echo "   nano /etc/systemd/system/telegram-bot.service"
echo "   (скопируйте содержимое из manual_deploy.md)"
echo ""

echo "8️⃣ Запуск сервиса:"
echo "   systemctl daemon-reload"
echo "   systemctl enable telegram-bot"
echo "   systemctl start telegram-bot"
echo "   systemctl status telegram-bot"
echo ""

echo "9️⃣ Настройка nginx:"
echo "   nano /etc/nginx/sites-available/telegram-bot"
echo "   (скопируйте конфигурацию из manual_deploy.md)"
echo "   ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/"
echo "   nginx -t && systemctl reload nginx"
echo ""

echo "🔟 Настройка файрвола:"
echo "   ufw allow 22 && ufw allow 80 && ufw allow 443"
echo "   ufw --force enable"
echo ""

echo "✅ После выполнения всех шагов приложение будет доступно по адресу:"
echo "   http://$VPS_IP"
echo ""

echo "📊 Для проверки статуса:"
echo "   systemctl status telegram-bot"
echo "   journalctl -u telegram-bot -f"
