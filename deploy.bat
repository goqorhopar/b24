@echo off
echo 🚀 Начинаем деплой на сервер 109.172.47.253...

echo 🔄 Шаг 1/8: Остановка сервиса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl stop meeting-bot.service || true"

echo 🔄 Шаг 2/8: Очистка места...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "rm -rf /tmp/* /var/tmp/* /var/cache/apt/archives/* /var/lib/apt/lists/*"

echo 🔄 Шаг 3/8: Обновление кода...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cd /root/b24 && git pull origin main"

echo 🔄 Шаг 4/8: Создание .env файла...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF"

echo 🔄 Шаг 5/8: Установка зависимостей...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cd /root/b24 && source venv/bin/activate && pip install -r requirements.txt"

echo 🔄 Шаг 6/8: Обновление systemd сервиса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/b24
ExecStart=/root/b24/venv/bin/python /root/b24/main.py
Restart=always
RestartSec=10
Environment=LOG_LEVEL=INFO
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=USE_POLLING=true
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=BITRIX_USER_ID=1
Environment=DATABASE_URL=sqlite:///bot_state.db

[Install]
WantedBy=multi-user.target
EOF"

echo 🔄 Шаг 7/8: Перезапуск сервиса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl daemon-reload && systemctl enable meeting-bot.service && systemctl start meeting-bot.service"

echo 🔄 Шаг 8/8: Проверка статуса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl status meeting-bot.service --no-pager"

echo 🎉 Деплой завершен!
echo 🤖 Бот должен быть запущен на сервере
echo 📱 Отправьте боту ссылку на встречу для проверки
pause
