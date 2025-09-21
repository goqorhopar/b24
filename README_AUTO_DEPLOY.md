# 🚀 Meeting Bot - Автоматический деплой

## 🎯 Что это?

Полноценная система автоматического деплоя для Meeting Bot, которая:
- ✅ **Автоматически коммитит** все изменения в GitHub
- ✅ **Деплоит на сервер** при каждом push
- ✅ **Отправляет уведомления** в Telegram
- ✅ **Проверяет работоспособность** после деплоя
- ✅ **Откатывается** при ошибках

## ⚡ Быстрый старт

### 1. Настройка (один раз)

```bash
# Windows
copy env_example.txt .env
notepad .env
setup_auto_deploy.bat

# Linux/Mac
cp env_example.txt .env
nano .env
chmod +x setup_auto_deploy.sh
./setup_auto_deploy.sh
```

### 2. Заполните .env файл

```env
# ОБЯЗАТЕЛЬНО
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyABCdefGHIjklMNOpqrsTUVwxyz123456

# GitHub
GITHUB_REPO=yourusername/meeting-bot
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# Сервер
DEPLOY_SERVER_URL=192.168.1.100
DEPLOY_SERVER_USER=root
DEPLOY_SERVER_PATH=/opt/meeting-bot

# Уведомления
ADMIN_CHAT_ID=123456789
```

### 3. Настройте GitHub Secrets

В репозитории GitHub → Settings → Secrets and variables → Actions:

- `DEPLOY_SERVER_URL` - IP сервера
- `DEPLOY_SERVER_USER` - пользователь SSH
- `DEPLOY_SSH_KEY` - приватный SSH ключ
- `DEPLOY_SSH_PORT` - порт SSH (22)
- `DEPLOY_SERVER_PATH` - путь на сервере

### 4. Запустите деплой

```bash
# Windows
deploy_automation.bat

# Linux/Mac
./quick_deploy.sh
```

## 🔄 Автоматический деплой

После настройки **ВСЕ изменения автоматически деплоятся**:

```bash
# Любые изменения в коде
git add .
git commit -m "Update bot"
git push origin main

# 🚀 Автоматически:
# 1. GitHub Actions запускается
# 2. Код деплоится на сервер
# 3. Сервис перезапускается
# 4. Отправляется уведомление в Telegram
```

## 📱 Уведомления

Бот отправляет уведомления в Telegram:

- ✅ **Успешный деплой** - "Деплой завершен успешно!"
- ❌ **Ошибка деплоя** - "Ошибка деплоя на сервер"
- 📊 **Статистика встреч** - "Обработано 5 встреч"
- 🔧 **Системные события** - "Сервис перезапущен"

## 🛠️ Команды

### Основные команды

```bash
# Полный деплой (коммит + деплой)
python auto_deploy.py

# Только коммит в GitHub
python auto_deploy.py --commit

# Только деплой на сервер
python auto_deploy.py --deploy

# Проверка статуса
python auto_deploy.py --status

# Настройка автоматического деплоя
python auto_deploy.py --setup
```

### Скрипты

```bash
# Быстрый деплой
./quick_deploy.sh          # Linux/Mac
deploy_automation.bat      # Windows

# Настройка
./setup_auto_deploy.sh     # Linux/Mac
setup_auto_deploy.bat      # Windows
```

## 🔍 Мониторинг

### Проверка статуса

```bash
# Статус сервиса
ssh user@server 'systemctl status meeting-bot'

# Логи сервиса
ssh user@server 'journalctl -u meeting-bot -f'

# Логи деплоя
tail -f auto_deploy.log

# GitHub Actions
# Перейдите в репозиторий → Actions
```

### Веб-интерфейс

```bash
# Статус API (если настроен)
curl http://your_server:3000/status

# Метрики (если включены)
curl http://your_server:9090/metrics
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Ошибка SSH подключения

```bash
# Проверьте SSH ключи
ssh -T git@github.com
ssh user@your_server

# Проверьте права
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

#### 2. Ошибка GitHub токена

```bash
# Проверьте токен
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

#### 3. Ошибка деплоя на сервер

```bash
# Проверьте доступ
ssh user@server 'whoami'

# Проверьте права
ssh user@server 'ls -la /opt/meeting-bot'

# Проверьте сервис
ssh user@server 'systemctl status meeting-bot'
```

#### 4. Откат к предыдущей версии

```bash
# На сервере
ssh user@server
cd /opt/meeting-bot
git log --oneline -10
git reset --hard COMMIT_HASH
systemctl restart meeting-bot
```

## 📊 Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Локальная     │    │     GitHub      │    │     Сервер      │
│   разработка    │    │                 │    │                 │
│                 │    │                 │    │                 │
│ 1. Изменения    │───▶│ 2. GitHub       │───▶│ 3. Автоматический│
│    в коде       │    │    Actions      │    │    деплой       │
│                 │    │                 │    │                 │
│ 4. Уведомления  │◀───│ 5. Webhook      │◀───│ 6. Статус       │
│    в Telegram   │    │    уведомления  │    │    сервиса      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

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

## 📚 Документация

- [📖 Подробное руководство](AUTO_DEPLOY_GUIDE.md)
- [🖥️ Настройка сервера](SERVER_DEPLOYMENT_GUIDE.md)
- [🐳 Docker деплой](docker-compose.server.yml)
- [⚡ Быстрый старт](QUICK_START_SERVER.md)

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи: `tail -f auto_deploy.log`
2. Проверьте GitHub Actions
3. Проверьте статус сервиса на сервере
4. Создайте issue в репозитории

## 🎉 Готово!

Теперь у вас есть **полностью автоматизированная система деплоя**:

- ✅ Любые изменения в коде автоматически попадают на сервер
- ✅ Получаете уведомления о статусе деплоя
- ✅ Можете откатиться к любой версии
- ✅ Система мониторит работоспособность

**Просто работайте с кодом, а деплой происходит автоматически!** 🚀
