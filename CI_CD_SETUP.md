# 🚀 Настройка CI/CD для Telegram бота

## 📋 Обзор

Этот проект настроен для автоматического деплоя на VPS Beget с использованием:
- **GitHub Actions** для CI/CD
- **Webhook** для мгновенного деплоя
- **SSH ключи** для безопасного подключения
- **Уведомления** в Telegram и Slack

## 🔧 Настройка

### 1. Настройка SSH ключей

```bash
# Создание SSH ключей
ssh-keygen -t rsa -b 4096 -C "deploy@telegram-bot"

# Добавление ключа на VPS
./setup_ssh_keys.sh
```

### 2. Настройка GitHub Secrets

В настройках репозитория GitHub добавьте секреты:

- `VPS_HOST` - IP адрес VPS (109.172.47.253)
- `VPS_USERNAME` - имя пользователя SSH (root)
- `VPS_SSH_KEY` - содержимое приватного ключа (~/.ssh/id_rsa)
- `SLACK_WEBHOOK` - URL webhook Slack (опционально)

### 3. Настройка Webhook

1. Разместите `deploy_webhook.php` в корне веб-сервера VPS
2. Настройте права доступа:
   ```bash
   chmod 755 /var/www/html/deploy_webhook.php
   chown www-data:www-data /var/www/html/deploy_webhook.php
   ```
3. В настройках GitHub репозитория добавьте webhook:
   - URL: `http://109.172.47.253/deploy_webhook.php`
   - Content type: `application/json`
   - Secret: `your-secret-key-here`

### 4. Настройка уведомлений

```bash
# Установка зависимостей для уведомлений
pip install requests

# Настройка уведомлений
python setup_notifications.py
```

Добавьте в `.env` файл:
```env
ADMIN_CHAT_ID=ваш_chat_id
SLACK_WEBHOOK=https://hooks.slack.com/services/...
```

## 🚀 Использование

### Автоматический деплой

1. **Push в main ветку** - автоматически запускает GitHub Actions
2. **Webhook** - мгновенно деплоит изменения
3. **Уведомления** - отправляются в Telegram/Slack

### Ручной деплой

```bash
# Быстрый деплой
git add -A && git commit -m "Update" && git push

# Полный деплой с проверками
Ctrl+Shift+P -> Tasks: Run Task -> Full Deploy
```

### Команды Cursor

- `Ctrl+Shift+P` -> `Tasks: Run Task`:
  - **Quick Deploy** - быстрый деплой
  - **Check Status** - проверка статуса
  - **View Logs** - просмотр логов
  - **Restart Service** - перезапуск сервиса
  - **Test Application** - тестирование приложения
  - **Full Deploy** - полный деплой с проверками

## 🔄 Rollback

```bash
# Откат на 1 коммит назад
./rollback.sh

# Откат на 3 коммита назад
./rollback.sh 3
```

## 📊 Мониторинг

### Проверка статуса
```bash
# Статус сервиса
systemctl status telegram-bot

# Логи
journalctl -u telegram-bot -f

# Тест приложения
curl http://109.172.47.253
```

### GitHub Actions
- Перейдите в раздел "Actions" репозитория
- Просматривайте логи деплоя
- Настраивайте уведомления о статусе

## 🛠️ Структура файлов

```
├── .github/workflows/
│   └── deploy.yml              # GitHub Actions
├── .vscode/
│   └── tasks.json              # Задачи Cursor
├── deploy_webhook.php          # Webhook для VPS
├── setup_ssh_keys.sh           # Настройка SSH
├── setup_notifications.py      # Настройка уведомлений
├── rollback.sh                 # Скрипт отката
├── config.py                   # Конфигурация окружений
└── .gitignore                  # Исключения Git
```

## 🔒 Безопасность

1. **SSH ключи** - используйте только для деплоя
2. **Webhook секрет** - сложный случайный ключ
3. **Права доступа** - минимальные необходимые права
4. **Логи** - регулярно проверяйте логи доступа

## 🚨 Устранение неполадок

### Проблемы с SSH
```bash
# Проверка подключения
ssh -v root@109.172.47.253

# Проверка ключей
ssh-add -l
```

### Проблемы с деплоем
```bash
# Проверка логов GitHub Actions
# Проверка логов webhook
tail -f /var/log/deploy.log

# Ручной деплой
cd /opt/telegram-bot
git pull origin main
systemctl restart telegram-bot
```

### Проблемы с сервисом
```bash
# Перезапуск сервиса
systemctl restart telegram-bot

# Проверка конфигурации
systemctl daemon-reload

# Проверка nginx
nginx -t
systemctl reload nginx
```

## 📈 Оптимизация

1. **Кэширование** - настройте кэш для зависимостей
2. **Параллельный деплой** - используйте несколько серверов
3. **Blue-Green деплой** - для zero-downtime обновлений
4. **Мониторинг** - настройте алерты и дашборды

## 📚 Дополнительные ресурсы

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [SSH Key Management](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [Webhook Security](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks)
- [Systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
