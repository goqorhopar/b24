# 🚀 Команды для быстрого деплоя на VPS

## Подключение к VPS

```bash
ssh root@109.172.47.253
```

## Установка и настройка (выполнить один раз)

```bash
# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y python3 python3-pip python3-venv git curl wget build-essential libssl-dev libffi-dev python3-dev

# Создаем директорию и клонируем репозиторий
mkdir -p /opt/telegram-bot
cd /opt/telegram-bot
git clone https://github.com/goqorhopar/b24.git .

# Делаем скрипт исполняемым
chmod +x deploy_to_vps.sh

# Запускаем деплой
./deploy_to_vps.sh
```

## Проверка работы

```bash
# Проверяем статус бота
systemctl status telegram-bot

# Смотрим логи
journalctl -u telegram-bot -f

# Проверяем, что сервер отвечает
curl http://localhost:3000/
```

## Управление ботом

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

## Обновление бота

```bash
cd /opt/telegram-bot
git pull origin main
systemctl restart telegram-bot
```

## Проверка работы в Telegram

1. Найдите бота: @TranscriptionleadBot
2. Отправьте: /start
3. Бот должен ответить

## Мониторинг

```bash
# Смотрим логи в реальном времени
journalctl -u telegram-bot -f

# Проверяем использование ресурсов
htop

# Проверяем сетевые соединения
netstat -tlnp | grep :3000
```

## Автоматический деплой через GitHub Actions

После настройки VPS, GitHub Actions будет автоматически деплоить бота при каждом пуше в main ветку.

### Настройка GitHub Secrets:

1. Перейдите в Settings → Secrets and variables → Actions
2. Добавьте секреты:
   - `VPS_HOST`: 109.172.47.253
   - `VPS_USERNAME`: root
   - `VPS_SSH_KEY`: приватный SSH ключ
   - `VPS_PORT`: 22

## Устранение проблем

```bash
# Если бот не запускается
journalctl -u telegram-bot --no-pager -l

# Если есть проблемы с зависимостями
cd /opt/telegram-bot
source venv/bin/activate
pip install -r requirements.txt

# Если есть проблемы с Git
cd /opt/telegram-bot
git status
git pull origin main
```
