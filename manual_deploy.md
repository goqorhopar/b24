# Инструкция по деплою на VPS Beget

## Подключение к серверу
```bash
ssh root@109.172.47.253
# Пароль: MmSS0JSm%6vb
```

## Информация о сервере
- **IP-адрес:** 109.172.47.253
- **Пользователь:** root
- **Пароль:** MmSS0JSm%6vb
- **ОС:** Ubuntu 24.04

## 1. Обновление системы и установка зависимостей
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git nginx ufw
```

## 2. Создание директории проекта
```bash
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot
```

## 3. Копирование файлов проекта
Скопируйте все файлы проекта в директорию `/opt/telegram-bot/`:
- main.py
- requirements.txt
- bitrix.py
- db.py
- gemini_client.py
- utils.py
- Dockerfile
- deploy.sh

## 4. Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Создание .env файла
```bash
nano .env
```

Содержимое .env файла:
```
TELEGRAM_BOT_TOKEN=ваш_токен_бота
GEMINI_API_KEY=ваш_gemini_api_ключ
RENDER_EXTERNAL_URL=https://ваш-домен.com
BITRIX_WEBHOOK_URL=https://ваш-bitrix.bitrix24.ru/rest/1/ваш-код/
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1
PORT=3000
DB_PATH=/opt/telegram-bot/bot_state.db
```

## 6. Создание systemd сервиса
```bash
nano /etc/systemd/system/telegram-bot.service
```

Содержимое сервиса:
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

[Install]
WantedBy=multi-user.target
```

## 7. Запуск сервиса
```bash
systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot
systemctl status telegram-bot
```

## 8. Настройка nginx
```bash
nano /etc/nginx/sites-available/telegram-bot
```

Конфигурация nginx:
```nginx
server {
    listen 80;
    server_name ваш-домен.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/telegram-bot /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## 9. Настройка файрвола
```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
```

## 10. Проверка работы
```bash
curl http://localhost:3000
journalctl -u telegram-bot -f
```
