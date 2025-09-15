# 🚀 Быстрый деплой бота на VPS

## 1. Подключение к VPS

```bash
ssh root@109.172.47.253
# или
ssh your_username@109.172.47.253
```

## 2. Установка необходимых пакетов

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Python и Git
apt install -y python3 python3-pip python3-venv git curl wget

# Устанавливаем системные зависимости
apt install -y build-essential libssl-dev libffi-dev python3-dev
```

## 3. Клонирование репозитория

```bash
# Создаем директорию для проекта
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot

# Клонируем репозиторий
git clone https://github.com/goqorhopar/b24.git .

# Делаем скрипты исполняемыми
chmod +x simple_deploy.sh setup_vps_simple.sh
```

## 4. Настройка .env файла

```bash
# Создаем .env файл
nano .env
```

Заполните файл:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI

# Gemini AI Configuration
GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.1
GEMINI_TOP_P=0.2
GEMINI_MAX_TOKENS=1200

# Bitrix24 Configuration
BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31
BITRIX_RESPONSIBLE_ID=1
BITRIX_CREATED_BY_ID=1
BITRIX_TASK_DEADLINE_DAYS=3

# Application Configuration
PORT=3000
DB_PATH=bot_state.db
LOG_LEVEL=INFO
NODE_ENV=production

# Request Configuration
MAX_RETRIES=3
RETRY_DELAY=2
REQUEST_TIMEOUT=30
MAX_COMMENT_LENGTH=8000

# Admin Configuration
ADMIN_CHAT_ID=7537953397

# Meeting Automation
MEETING_DISPLAY_NAME=Ассистент Григория Сергеевича
MEETING_HEADLESS=true
MEETING_AUTO_LEAVE=true
MEETING_DURATION_MINUTES=60
```

## 5. Запуск деплоя

```bash
# Запускаем скрипт деплоя
./simple_deploy.sh
```

## 6. Проверка работы бота

```bash
# Проверяем статус
systemctl status telegram-bot

# Смотрим логи
journalctl -u telegram-bot -f

# Проверяем, что бот отвечает
curl -X GET "http://localhost:3000/"
```

## 7. Управление ботом

```bash
# Запустить
systemctl start telegram-bot

# Остановить
systemctl stop telegram-bot

# Перезапустить
systemctl restart telegram-bot

# Статус
systemctl status telegram-bot

# Логи
journalctl -u telegram-bot -f
```

## 8. Автоматический деплой через GitHub Actions

После настройки VPS, GitHub Actions будет автоматически деплоить бота при каждом пуше в main ветку.

### Настройка GitHub Secrets:

1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте секреты:
   - `VPS_HOST`: 109.172.47.253
   - `VPS_USERNAME`: root (или ваш username)
   - `VPS_SSH_KEY`: приватный SSH ключ
   - `VPS_PORT`: 22

## 9. Проверка работы

После деплоя отправьте боту сообщение в Telegram:
- Найдите бота: @TranscriptionleadBot
- Отправьте: /start
- Бот должен ответить

## 10. Мониторинг

```bash
# Смотрим логи в реальном времени
journalctl -u telegram-bot -f

# Проверяем использование ресурсов
htop

# Проверяем сетевые соединения
netstat -tlnp | grep :3000
```
