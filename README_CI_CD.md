# 🚀 Полная настройка CI/CD для Telegram бота

## 📋 Что включено

✅ **GitHub Actions** - автоматический деплой при push  
✅ **Webhook** - мгновенный деплой при изменениях  
✅ **SSH ключи** - безопасное подключение к VPS  
✅ **Уведомления** - Telegram и Slack уведомления  
✅ **Rollback** - откат к предыдущей версии  
✅ **Мониторинг** - проверка статуса и логов  
✅ **Cursor задачи** - быстрый деплой из IDE  

## 🚀 Быстрый старт

### 1. Автоматическая настройка
```bash
# Запустите скрипт настройки
setup_cicd.bat
```

### 2. Ручная настройка

#### Шаг 1: Создание GitHub репозитория
1. Перейдите на https://github.com/new
2. Название: `telegram-bot`
3. Сделайте репозиторий приватным
4. НЕ добавляйте README, .gitignore или лицензию

#### Шаг 2: Настройка SSH ключей
```bash
# Создание SSH ключей
ssh-keygen -t rsa -b 4096 -C "deploy@telegram-bot"

# Добавление ключа на VPS
./setup_ssh_keys.sh
```

#### Шаг 3: Настройка GitHub Secrets
В настройках репозитория добавьте:
- `VPS_HOST` = `109.172.47.253`
- `VPS_USERNAME` = `root`
- `VPS_SSH_KEY` = содержимое `~/.ssh/id_rsa`
- `SLACK_WEBHOOK` = ваш webhook URL (опционально)

#### Шаг 4: Настройка webhook
1. Скопируйте `deploy_webhook.php` на VPS в корень веб-сервера
2. Настройте права:
   ```bash
   chmod 755 /var/www/html/deploy_webhook.php
   chown www-data:www-data /var/www/html/deploy_webhook.php
   ```
3. В GitHub добавьте webhook:
   - URL: `http://109.172.47.253/deploy_webhook.php`
   - Secret: `your-secret-key-here`

#### Шаг 5: Первый деплой
```bash
git add .
git commit -m "Setup CI/CD pipeline"
git push -u origin main
```

## 🔧 Использование

### Автоматический деплой
- **Push в main** → автоматический деплой через GitHub Actions
- **Webhook** → мгновенный деплой при изменениях

### Ручной деплой
```bash
# Быстрый деплой
git add -A && git commit -m "Update" && git push

# Или используйте Cursor задачи:
# Ctrl+Shift+P -> Tasks: Run Task -> Quick Deploy
```

### Команды Cursor
- `Ctrl+Shift+P` → `Tasks: Run Task`:
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
├── .gitignore                  # Исключения Git
└── CI_CD_SETUP.md             # Подробная инструкция
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

## 🎉 Готово!

Теперь у вас есть полноценный CI/CD пайплайн для вашего Telegram бота:

- ✅ Автоматический деплой при push
- ✅ Мгновенный деплой через webhook
- ✅ Уведомления о статусе деплоя
- ✅ Возможность отката
- ✅ Мониторинг и логирование
- ✅ Интеграция с Cursor IDE

**Следующий шаг:** Создайте GitHub репозиторий и запустите первый деплой!
