@echo off
echo 🚀 Деплой бота на сервер 109.172.47.253...

echo.
echo 📋 Шаг 1: Остановка сервиса
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl stop meeting-bot.service || true"

echo.
echo 📋 Шаг 2: Обновление кода
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cd /root/b24 && git pull origin main || echo 'Git pull failed, continuing...'"

echo.
echo 📋 Шаг 3: Создание .env файла
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cat > /root/b24/.env << 'EOF'
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
ADMIN_CHAT_ID=7537953397
BITRIX_USER_ID=1
DATABASE_URL=sqlite:///bot_state.db
EOF"

echo.
echo 📋 Шаг 4: Установка зависимостей
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cd /root/b24 && python3 -m pip install -r requirements.txt"

echo.
echo 📋 Шаг 5: Создание systemd сервиса
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "cat > /etc/systemd/system/meeting-bot.service << 'EOF'
[Unit]
Description=Meeting Bot Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/b24
ExecStart=/usr/bin/python3 /root/b24/main.py
Restart=always
RestartSec=10
Environment=LOG_LEVEL=INFO
Environment=PORT=3000
Environment=HOST=0.0.0.0
Environment=USE_POLLING=true
Environment=TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
Environment=BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
Environment=GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
Environment=ADMIN_CHAT_ID=7537953397
Environment=BITRIX_USER_ID=1
Environment=DATABASE_URL=sqlite:///bot_state.db

[Install]
WantedBy=multi-user.target
EOF"

echo.
echo 📋 Шаг 6: Перезагрузка systemd
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl daemon-reload"

echo.
echo 📋 Шаг 7: Включение автозапуска
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl enable meeting-bot.service"

echo.
echo 📋 Шаг 8: Запуск бота
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl start meeting-bot.service"

echo.
echo 📋 Шаг 9: Проверка статуса
ssh -o StrictHostKeyChecking=no root@109.172.47.253 "sleep 5 && systemctl status meeting-bot.service --no-pager"

echo.
echo 🎉 Деплой завершен!
echo 🤖 Бот должен быть запущен на сервере 109.172.47.253
echo 📱 Отправьте сообщение боту в Telegram для проверки

pause
