# 🚀 Инструкция по деплою бота

## Быстрый старт

### 1. Настройка VPS (выполнить один раз)

Подключитесь к вашему VPS и выполните:

```bash
# Скачайте и запустите скрипт настройки
curl -sSL https://raw.githubusercontent.com/goqorhopar/b24/main/setup_vps_simple.sh | bash

# Или клонируйте репозиторий и запустите локально
git clone https://github.com/goqorhopar/b24.git
cd b24
chmod +x setup_vps_simple.sh
./setup_vps_simple.sh
```

### 2. Настройка GitHub Secrets

Перейдите в ваш репозиторий на GitHub:
1. Settings → Secrets and variables → Actions
2. Добавьте следующие секреты:

| Название | Значение | Описание |
|----------|----------|----------|
| `VPS_HOST` | IP адрес VPS | Например: `192.168.1.100` |
| `VPS_USERNAME` | Имя пользователя | Например: `ubuntu` |
| `VPS_SSH_KEY` | Приватный SSH ключ | Содержимое файла `~/.ssh/id_rsa` |
| `VPS_PORT` | Порт SSH | `22` (по умолчанию) |

### 3. Настройка .env файла

На VPS отредактируйте файл `.env`:

```bash
nano /opt/telegram-bot/.env
```

Заполните следующие переменные:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Bitrix24
BITRIX_WEBHOOK_URL=your_webhook_url_here
BITRIX_USER_ID=your_user_id_here

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///bot.db

# Logging
LOG_LEVEL=INFO

# Server
PORT=3000
USE_POLLING=true
```

### 4. Запуск бота

```bash
# Запустить бота
sudo systemctl start telegram-bot

# Проверить статус
sudo systemctl status telegram-bot

# Посмотреть логи
sudo journalctl -u telegram-bot -f
```

## Автоматический деплой

После настройки GitHub Secrets, при каждом пуше в `main` ветку:
1. GitHub Actions автоматически проверит код
2. Подключится к VPS
3. Обновит код
4. Перезапустит бота

## Управление ботом

```bash
# Запустить
sudo systemctl start telegram-bot

# Остановить
sudo systemctl stop telegram-bot

# Перезапустить
sudo systemctl restart telegram-bot

# Статус
sudo systemctl status telegram-bot

# Логи
sudo journalctl -u telegram-bot -f

# Автозапуск при загрузке
sudo systemctl enable telegram-bot
```

## Устранение проблем

### Бот не запускается
```bash
# Проверьте логи
sudo journalctl -u telegram-bot --no-pager -l

# Проверьте .env файл
cat /opt/telegram-bot/.env

# Проверьте права доступа
ls -la /opt/telegram-bot/
```

### Проблемы с зависимостями
```bash
cd /opt/telegram-bot
source venv/bin/activate
pip install -r requirements.txt
```

### Проблемы с Git
```bash
cd /opt/telegram-bot
git status
git pull origin main
```

## Структура проекта

```
/opt/telegram-bot/
├── main.py                 # Основной файл бота
├── config.py              # Конфигурация
├── requirements.txt       # Зависимости Python
├── .env                   # Переменные окружения
├── simple_deploy.sh       # Скрипт деплоя
└── venv/                  # Виртуальное окружение
```

## Поддержка

Если что-то не работает:
1. Проверьте логи: `sudo journalctl -u telegram-bot -f`
2. Проверьте статус: `sudo systemctl status telegram-bot`
3. Проверьте .env файл
4. Проверьте GitHub Actions в репозитории
