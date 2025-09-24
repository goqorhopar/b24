# Команды для исправления сервиса на сервере

## 1. Исправить git pull
```bash
cd /root/b24
git config pull.rebase false
git pull origin main
```

## 2. Создать файл .env с токенами
```bash
cd /root/b24
cat > .env << 'EOF'
# Основные настройки
LOG_LEVEL=INFO
PORT=3000
HOST=0.0.0.0
USE_POLLING=true

# Telegram Bot (ЗАМЕНИТЕ НА ВАШ ТОКЕН!)
TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token_here

# Bitrix24 (ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ!)
BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/1/your_webhook_code/
BITRIX_USER_ID=1

# Gemini AI (ЗАМЕНИТЕ НА ВАШ API КЛЮЧ!)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# База данных
DATABASE_URL=sqlite:///bot_state.db

# Webhook (опционально)
WEBHOOK_URL=
WEBHOOK_SECRET=
EOF
```

## 3. Обновить конфигурацию сервиса
```bash
cd /root/b24
sudo cp systemd/meeting-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## 4. Проверить конфигурацию сервиса
```bash
sudo systemctl cat meeting-bot.service
```

## 5. Перезапустить сервис
```bash
sudo systemctl stop meeting-bot.service
sudo systemctl start meeting-bot.service
sudo systemctl status meeting-bot.service
```

## 6. Проверить логи
```bash
sudo journalctl -u meeting-bot.service -f
```

## 7. Проверить работу приложения
```bash
# Проверить health endpoint
curl http://localhost:3000/health

# Проверить процессы
ps aux | grep python
```

## Если сервис все еще не работает:

### Проверить права доступа
```bash
ls -la /root/b24/
ls -la /root/b24/venv/bin/python
```

### Запустить вручную для диагностики
```bash
cd /root/b24
source venv/bin/activate
python main.py
```

### Проверить переменные окружения
```bash
cd /root/b24
source venv/bin/activate
python -c "from config import config; print(config.runtime_summary())"
```
