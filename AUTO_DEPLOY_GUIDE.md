# 🚀 Руководство по автоматическому деплою

## 📋 Обзор

Система автоматического деплоя позволяет:
- ✅ Автоматически коммитить изменения в GitHub
- ✅ Деплоить код на сервер при каждом push
- ✅ Получать уведомления о статусе деплоя
- ✅ Откатываться к предыдущим версиям при ошибках

## ⚙️ Настройка

### 1. Подготовка конфигурации

```bash
# Скопируйте пример конфигурации
cp env_example.txt .env

# Отредактируйте настройки
nano .env
```

### 2. Обязательные настройки в .env

```env
# GitHub
GITHUB_REPO=your_username/meeting-bot
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_BRANCH=main

# Сервер
DEPLOY_SERVER_URL=192.168.1.100
DEPLOY_SERVER_USER=root
DEPLOY_SERVER_PATH=/opt/meeting-bot
DEPLOY_RESTART_COMMAND=systemctl restart meeting-bot

# Telegram (для уведомлений)
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_chat_id
```

### 3. Получение GitHub токена

1. Перейдите в GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token
4. Выберите права: `repo`, `workflow`
5. Скопируйте токен в `.env`

### 4. Настройка SSH ключей

```bash
# Генерируем SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "deploy@meeting-bot"

# Копируем публичный ключ на сервер
ssh-copy-id user@your_server_ip

# Добавляем приватный ключ в GitHub Secrets
cat ~/.ssh/id_rsa
```

### 5. Настройка GitHub Secrets

В репозитории GitHub → Settings → Secrets and variables → Actions:

- `DEPLOY_SERVER_URL` - IP или домен сервера
- `DEPLOY_SERVER_USER` - пользователь для SSH
- `DEPLOY_SSH_KEY` - приватный SSH ключ
- `DEPLOY_SSH_PORT` - порт SSH (по умолчанию 22)
- `DEPLOY_SERVER_PATH` - путь на сервере (по умолчанию /opt/meeting-bot)

### 6. Запуск настройки

```bash
# Делаем скрипт исполняемым
chmod +x setup_auto_deploy.sh

# Запускаем настройку
./setup_auto_deploy.sh
```

## 🚀 Использование

### Быстрый деплой

```bash
# Делаем скрипт исполняемым
chmod +x quick_deploy.sh

# Запускаем быстрый деплой
./quick_deploy.sh
```

### Автоматический деплой

```bash
# Коммитим изменения
git add .
git commit -m "Update meeting bot"

# Пушим в GitHub (автоматически запустится деплой)
git push origin main
```

### Ручной деплой

```bash
# Только коммит в GitHub
python3 auto_deploy.py --commit

# Только деплой на сервер
python3 auto_deploy.py --deploy

# Полный деплой
python3 auto_deploy.py
```

## 📊 Мониторинг

### Проверка статуса

```bash
# Статус сервиса на сервере
ssh user@server 'systemctl status meeting-bot'

# Логи сервиса
ssh user@server 'journalctl -u meeting-bot -f'

# Логи деплоя
tail -f auto_deploy.log
```

### GitHub Actions

1. Перейдите в репозиторий → Actions
2. Выберите workflow "Auto Deploy Meeting Bot"
3. Просмотрите логи выполнения

## 🔧 Устранение неполадок

### Ошибка SSH подключения

```bash
# Проверьте SSH ключи
ssh -T git@github.com
ssh user@your_server

# Проверьте права на ключи
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

### Ошибка GitHub токена

```bash
# Проверьте токен
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Ошибка деплоя на сервер

```bash
# Проверьте доступ к серверу
ssh user@server 'whoami'

# Проверьте права на директорию
ssh user@server 'ls -la /opt/meeting-bot'

# Проверьте статус сервиса
ssh user@server 'systemctl status meeting-bot'
```

### Откат к предыдущей версии

```bash
# На сервере
ssh user@server
cd /opt/meeting-bot
git log --oneline -10
git reset --hard COMMIT_HASH
systemctl restart meeting-bot
```

## 📱 Уведомления

Система отправляет уведомления в Telegram:

- ✅ Успешный деплой
- ❌ Ошибки деплоя
- 📊 Статистика встреч
- 🔧 Системные уведомления

## 🔒 Безопасность

### Рекомендации

1. **Используйте отдельного пользователя** для деплоя
2. **Ограничьте права** SSH ключей
3. **Регулярно обновляйте** токены
4. **Мониторьте логи** на предмет подозрительной активности

### Настройка пользователя для деплоя

```bash
# Создаем пользователя
sudo useradd -m -s /bin/bash deployer

# Добавляем в группу sudo
sudo usermod -aG sudo deployer

# Настраиваем SSH ключи
sudo -u deployer ssh-keygen -t rsa -b 4096

# Копируем публичный ключ на сервер
sudo -u deployer ssh-copy-id deployer@your_server
```

## 📈 Расширенные настройки

### Множественные серверы

```env
# В .env можно указать несколько серверов
DEPLOY_SERVER_URL=server1.com,server2.com,server3.com
DEPLOY_SERVER_USER=deployer,deployer,deployer
```

### Кастомные команды

```env
# Команда перед деплоем
DEPLOY_PRE_COMMAND=systemctl stop nginx

# Команда после деплоя
DEPLOY_POST_COMMAND=systemctl start nginx
```

### Уведомления в Slack

```env
# Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f auto_deploy.log`
2. Проверьте GitHub Actions
3. Проверьте статус сервиса на сервере
4. Создайте issue в репозитории

## 📚 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SSH Key Management](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Docker Deployment](docker-compose.server.yml)
- [Server Setup Guide](SERVER_DEPLOYMENT_GUIDE.md)
