# 🚀 Деплой Telegram бота на VPS Beget

## 📋 Информация о сервере
- **IP-адрес:** 109.172.47.253
- **Пользователь:** root
- **Пароль:** MmSS0JSm%6vb
- **ОС:** Ubuntu 24.04

## 🔧 Пошаговая инструкция

### 1. Подключение к серверу
```bash
ssh root@109.172.47.253
# Введите пароль: MmSS0JSm%6vb
```

### 2. Обновление системы
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx ufw curl wget
```

### 3. Создание директории проекта
```bash
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot
```

### 4. Копирование файлов проекта
На вашем локальном компьютере выполните:
```bash
scp -r ./* root@109.172.47.253:/opt/telegram-bot/
```

### 5. Настройка Python окружения
```bash
cd /opt/telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Создание .env файла
```bash
nano .env
```

Скопируйте и заполните следующий контент:
```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=ваш_токен_бота
RENDER_EXTERNAL_URL=http://109.172.47.253

# Gemini AI Configuration
GEMINI_API_KEY=ваш_gemini_api_ключ
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.1
GEMINI_TOP_P=0.2
GEMINI_MAX_TOKENS=1200

# Bitrix24 Configuration (Optional)
BITRIX_WEBHOOK_URL=https://ваш-bitrix.bitrix24.ru/rest/1/ваш-код/
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1
BITRIX_TASK_DEADLINE_DAYS=3

# Application Configuration
PORT=3000
DB_PATH=/opt/telegram-bot/bot_state.db
LOG_LEVEL=INFO
NODE_ENV=production

# Request Configuration
MAX_RETRIES=3
RETRY_DELAY=2
REQUEST_TIMEOUT=30
MAX_COMMENT_LENGTH=8000
```

### 7. Создание systemd сервиса
```bash
nano /etc/systemd/system/telegram-bot.service
```

Скопируйте следующий контент:
```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
Environment=PATH=/opt/telegram-bot/venv/bin
ExecStart=/opt/telegram-bot/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 8. Настройка nginx
```bash
nano /etc/nginx/sites-available/telegram-bot
```

Скопируйте следующий контент:
```nginx
server {
    listen 80;
    server_name 109.172.47.253;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Активируйте конфигурацию:
```bash
ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

### 9. Настройка файрвола
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
```

### 10. Запуск сервиса
```bash
systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot
systemctl status telegram-bot
```

## ✅ Проверка работы

### Проверка статуса сервиса
```bash
systemctl status telegram-bot
```

### Проверка логов
```bash
journalctl -u telegram-bot -f
```

### Проверка доступности
```bash
curl http://localhost:3000
curl http://109.172.47.253
```

## 🔧 Полезные команды

### Перезапуск сервиса
```bash
systemctl restart telegram-bot
```

### Остановка сервиса
```bash
systemctl stop telegram-bot
```

### Просмотр логов
```bash
journalctl -u telegram-bot --since "1 hour ago"
```

### Обновление кода
```bash
cd /opt/telegram-bot
git pull  # если используете git
# или скопируйте новые файлы через scp
systemctl restart telegram-bot
```

## 🌐 Доступ к приложению

После успешного деплоя ваше приложение будет доступно по адресу:
- **HTTP:** http://109.172.47.253
- **Webhook URL для Telegram:** http://109.172.47.253/webhook

## ⚠️ Важные замечания

1. **Безопасность:** Не забудьте настроить .env файл с вашими токенами
2. **Домен:** Если у вас есть домен, настройте его в nginx конфигурации
3. **SSL:** Для продакшена рекомендуется настроить SSL сертификат
4. **Мониторинг:** Регулярно проверяйте логи и статус сервиса
