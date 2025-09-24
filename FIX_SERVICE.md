# Исправление сервиса meeting-bot

## Проблема
Сервис `meeting-bot.service` постоянно перезапускается с ошибкой из-за отсутствующих файлов Python.

## Решение

### 1. Обновить файлы на сервере
```bash
cd /root/b24
git pull origin main
```

### 2. Установить зависимости Python
```bash
cd /root/b24
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Создать файл .env с переменными окружения
```bash
cd /root/b24
cp env.example .env
# Отредактировать .env файл с вашими токенами
nano .env
```

### 4. Обновить конфигурацию сервиса
```bash
sudo cp systemd/meeting-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 5. Перезапустить сервис
```bash
sudo systemctl stop meeting-bot.service
sudo systemctl start meeting-bot.service
sudo systemctl status meeting-bot.service
```

### 6. Проверить логи
```bash
sudo journalctl -u meeting-bot.service -f
```

## Необходимые переменные окружения в .env

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_actual_token_here

# Bitrix24
BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/1/your_webhook_code/
BITRIX_USER_ID=1

# Gemini AI
GEMINI_API_KEY=your_actual_gemini_key_here

# Основные настройки
LOG_LEVEL=INFO
PORT=3000
USE_POLLING=true
```

## Проверка работы
После исправления сервис должен:
- Запускаться без ошибок
- Отвечать на /health endpoint
- Обрабатывать сообщения в Telegram
