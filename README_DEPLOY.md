# Meeting Bot Assistant - Развертывание на сервере

## 🚀 Быстрое развертывание

### Автоматическое развертывание

```bash
# 1. Подключитесь к серверу
ssh root@your-server

# 2. Скопируйте файлы проекта
scp -r . root@your-server:/root/b24/

# 3. Запустите автоматический скрипт развертывания
cd /root/b24
chmod +x deploy.sh
./deploy.sh
```

### Ручное развертывание

```bash
# 1. Обновление системы
apt update && apt upgrade -y

# 2. Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 3. Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 4. Создание директории проекта
mkdir -p /opt/meeting-bot
cd /opt/meeting-bot

# 5. Копирование файлов
cp -r /root/b24/* /opt/meeting-bot/

# 6. Создание .env файла
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

# 7. Запуск через Docker Compose
docker-compose up -d

# 8. Создание systemd сервиса
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

# 9. Включение автозапуска
systemctl daemon-reload
systemctl enable meeting-bot.service
systemctl start meeting-bot.service
```

## 📊 Управление сервисом

### Проверка статуса
```bash
# Статус systemd сервиса
systemctl status meeting-bot

# Статус Docker контейнеров
docker-compose ps

# Логи сервиса
journalctl -u meeting-bot -f

# Логи Docker контейнеров
docker-compose logs -f
```

### Управление
```bash
# Запуск
systemctl start meeting-bot

# Остановка
systemctl stop meeting-bot

# Перезапуск
systemctl restart meeting-bot

# Перезапуск только контейнеров
docker-compose restart
```

## 🔧 Настройка

### Переменные окружения (.env)
```bash
NODE_ENV=production
PORT=3000
HOST=0.0.0.0
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
BITRIX_WEBHOOK_URL=your_bitrix_webhook_url
GEMINI_API_KEY=your_gemini_api_key
ADMIN_CHAT_ID=your_admin_chat_id
PUPPETEER_HEADLESS=true
TZ=Europe/Moscow
```

### Обновление
```bash
# Остановка сервиса
systemctl stop meeting-bot

# Обновление кода
cd /opt/meeting-bot
git pull  # или копирование новых файлов

# Пересборка и запуск
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Запуск сервиса
systemctl start meeting-bot
```

## 🐛 Отладка

### Проверка логов
```bash
# Логи MCP Router
tail -f logs/router.log

# Логи Telegram бота
docker-compose logs meeting-bot -f

# Системные логи
journalctl -u meeting-bot -f
```

### Проверка подключений
```bash
# Проверка Telegram API
curl -X GET "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Проверка Gemini API
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GEMINI_API_KEY"

# Проверка Bitrix24 API
curl -X POST "$BITRIX_WEBHOOK_URL/crm.lead.list"
```

## 📋 Мониторинг

### Health Check
```bash
# Проверка здоровья контейнера
docker inspect meeting-bot-assistant | grep Health

# Проверка портов
netstat -tlnp | grep :3000
```

### Производительность
```bash
# Использование ресурсов
docker stats meeting-bot-assistant

# Использование диска
df -h
du -sh /opt/meeting-bot
```

## 🔒 Безопасность

### Firewall
```bash
# Открытие только необходимых портов
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### SSL сертификаты
```bash
# Установка Let's Encrypt
apt install certbot
certbot --nginx -d your-domain.com
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `journalctl -u meeting-bot -f`
2. Проверьте статус: `systemctl status meeting-bot`
3. Проверьте контейнеры: `docker-compose ps`
4. Перезапустите сервис: `systemctl restart meeting-bot`

## 🎉 Готово!

После успешного развертывания ваш Meeting Bot Assistant будет:
- ✅ Автоматически запускаться при перезагрузке сервера
- ✅ Обрабатывать встречи через Telegram
- ✅ Интегрироваться с Gemini AI и Bitrix24
- ✅ Вести логи всех операций
- ✅ Автоматически перезапускаться при сбоях