# Настройка автоматического деплоя через GitHub Actions

## 1. Подготовка VPS

### Установка необходимых пакетов на VPS:
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем Git
sudo apt install git -y

# Устанавливаем Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Устанавливаем системные зависимости
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y
```

### Клонирование репозитория на VPS:
```bash
# Создаем директорию для проекта
sudo mkdir -p /opt/telegram-bot
sudo chown $USER:$USER /opt/telegram-bot

# Клонируем репозиторий
cd /opt/telegram-bot
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

### Настройка SSH ключей:
```bash
# Генерируем SSH ключ для GitHub Actions
ssh-keygen -t rsa -b 4096 -C "github-actions" -f ~/.ssh/github_actions_key

# Добавляем публичный ключ в authorized_keys
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys

# Устанавливаем правильные права
chmod 600 ~/.ssh/github_actions_key
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

## 2. Настройка GitHub Secrets

Перейдите в ваш GitHub репозиторий → Settings → Secrets and variables → Actions

Добавьте следующие секреты:

### VPS_HOST
- **Название**: `VPS_HOST`
- **Значение**: IP адрес вашего VPS (например: `192.168.1.100`)

### VPS_USERNAME
- **Название**: `VPS_USERNAME`
- **Значение**: Имя пользователя на VPS (например: `ubuntu` или `root`)

### VPS_SSH_KEY
- **Название**: `VPS_SSH_KEY`
- **Значение**: Содержимое приватного ключа `~/.ssh/github_actions_key` (весь файл)

### VPS_PORT (опционально)
- **Название**: `VPS_PORT`
- **Значение**: Порт SSH (по умолчанию: `22`)

## 3. Настройка переменных окружения

Создайте файл `.env` на VPS:
```bash
cd /opt/telegram-bot
cp .env.example .env
nano .env
```

Заполните необходимые переменные:
```env
# Telegram Bot
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://yourdomain.com/webhook

# Bitrix24
BITRIX_WEBHOOK_URL=your_bitrix_webhook_url
BITRIX_CLIENT_ID=your_client_id
BITRIX_CLIENT_SECRET=your_client_secret

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Database
DATABASE_URL=sqlite:///bot.db
```

## 4. Первоначальный деплой

Выполните на VPS:
```bash
cd /opt/telegram-bot
chmod +x deploy_vps_github.sh
./deploy_vps_github.sh
```

## 5. Проверка работы

### Проверка статуса бота:
```bash
sudo systemctl status telegram-bot
```

### Просмотр логов:
```bash
sudo journalctl -u telegram-bot -f
```

### Проверка работы GitHub Actions:
1. Перейдите в ваш репозиторий на GitHub
2. Откройте вкладку "Actions"
3. Вы должны увидеть workflow "Deploy to VPS"
4. При каждом пуше в main ветку будет запускаться деплой

## 6. Автоматический деплой

Теперь при каждом пуше в main ветку GitHub Actions автоматически:
1. Проверит код на синтаксические ошибки
2. Подключится к VPS по SSH
3. Остановит бота
4. Обновит код из репозитория
5. Установит зависимости
6. Перезапустит бота

## 7. Мониторинг

### Просмотр логов GitHub Actions:
- Перейдите в Actions → Deploy to VPS → выберите последний запуск

### Просмотр логов на VPS:
```bash
# Логи сервиса
sudo journalctl -u telegram-bot -f

# Логи приложения
tail -f /opt/telegram-bot/bot.log
```

## 8. Откат изменений

Если что-то пошло не так, можно откатиться к предыдущей версии:
```bash
cd /opt/telegram-bot
git log --oneline -10  # посмотреть последние коммиты
git reset --hard HEAD~1  # откатиться на один коммит назад
sudo systemctl restart telegram-bot
```

## 9. Troubleshooting

### Если деплой не запускается:
1. Проверьте, что все Secrets настроены правильно
2. Убедитесь, что SSH ключ добавлен в authorized_keys
3. Проверьте, что VPS доступен по указанному IP и порту

### Если бот не запускается:
1. Проверьте логи: `sudo journalctl -u telegram-bot -f`
2. Убедитесь, что все переменные в .env настроены
3. Проверьте права доступа к файлам

### Если есть ошибки в коде:
1. GitHub Actions покажет ошибки компиляции
2. Исправьте ошибки локально
3. Сделайте commit и push
4. Деплой запустится автоматически
