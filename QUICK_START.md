# 🚀 Быстрый старт - Автоматический деплой

## 1. Подготовка VPS (выполнить один раз)

### На VPS выполните:
```bash
# Скачайте и запустите скрипт настройки
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/setup_vps.sh | bash -s https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Или клонируйте репозиторий и запустите локально
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
chmod +x setup_vps.sh
./setup_vps.sh
```

## 2. Настройка GitHub Secrets

Перейдите в ваш репозиторий на GitHub:
1. Settings → Secrets and variables → Actions
2. Добавьте следующие секреты:

| Название | Значение | Описание |
|----------|----------|----------|
| `VPS_HOST` | IP адрес VPS | Например: `192.168.1.100` |
| `VPS_USERNAME` | Имя пользователя | Например: `ubuntu` |
| `VPS_SSH_KEY` | Приватный SSH ключ | Содержимое файла `~/.ssh/github_actions_key` |
| `VPS_PORT` | Порт SSH | `22` (по умолчанию) |

## 3. Настройка переменных окружения

На VPS отредактируйте файл `.env`:
```bash
nano /opt/telegram-bot/.env
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

## 4. Запуск бота

```bash
# Запустить бота
sudo systemctl start telegram-bot

# Проверить статус
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -f
```

## 5. Автоматический деплой

Теперь при каждом пуше в `main` ветку:
1. GitHub Actions автоматически проверит код
2. Подключится к VPS по SSH
3. Обновит код и перезапустит бота

### Тестирование деплоя:
```bash
# Локально проверьте код
chmod +x test_deploy.sh
./test_deploy.sh

# Запушьте изменения
git add .
git commit -m "Настройка автодеплоя"
git push origin main
```

## 6. Мониторинг

### GitHub Actions:
- Перейдите в Actions → Deploy to VPS
- Просматривайте логи деплоя

### VPS:
```bash
# Статус сервиса
sudo systemctl status telegram-bot

# Логи сервиса
sudo journalctl -u telegram-bot -f

# Логи приложения
tail -f /opt/telegram-bot/bot.log
```

## 7. Полезные команды

### Управление ботом:
```bash
# Запуск
sudo systemctl start telegram-bot

# Остановка
sudo systemctl stop telegram-bot

# Перезапуск
sudo systemctl restart telegram-bot

# Статус
sudo systemctl status telegram-bot

# Включить автозапуск
sudo systemctl enable telegram-bot

# Отключить автозапуск
sudo systemctl disable telegram-bot
```

### Обновление вручную:
```bash
cd /opt/telegram-bot
git pull origin main
sudo systemctl restart telegram-bot
```

### Откат к предыдущей версии:
```bash
cd /opt/telegram-bot
git log --oneline -5  # посмотреть последние коммиты
git reset --hard HEAD~1  # откатиться на один коммит назад
sudo systemctl restart telegram-bot
```

## 8. Troubleshooting

### Если деплой не запускается:
1. Проверьте GitHub Secrets
2. Убедитесь, что VPS доступен
3. Проверьте SSH ключи

### Если бот не запускается:
1. Проверьте логи: `sudo journalctl -u telegram-bot -f`
2. Убедитесь, что все переменные в `.env` настроены
3. Проверьте права доступа к файлам

### Если есть ошибки в коде:
1. GitHub Actions покажет ошибки компиляции
2. Исправьте ошибки локально
3. Сделайте commit и push
4. Деплой запустится автоматически

## 9. Структура файлов

```
.github/workflows/deploy.yml    # GitHub Actions workflow
deploy_vps_github.sh            # Скрипт деплоя для VPS
setup_vps.sh                    # Скрипт настройки VPS
test_deploy.sh                  # Скрипт тестирования
GITHUB_DEPLOY_SETUP.md          # Подробная инструкция
QUICK_START.md                  # Этот файл
```

## 10. Поддержка

Если возникли проблемы:
1. Проверьте логи GitHub Actions
2. Проверьте логи на VPS
3. Убедитесь, что все секреты настроены правильно
4. Проверьте, что VPS доступен по SSH
