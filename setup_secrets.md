# Настройка GitHub Secrets для автоматического деплоя

## Необходимые секреты в GitHub

Перейдите в настройки репозитория: `Settings` → `Secrets and variables` → `Actions`

### Добавьте следующие секреты:

1. **VPS_HOST** = `your_server_ip`
2. **VPS_USERNAME** = `root`
3. **VPS_PASSWORD** = `your_password`
4. **TELEGRAM_BOT_TOKEN** = `your_telegram_bot_token`
5. **TELEGRAM_CHAT_ID** = `your_chat_id`
6. **REPO_NAME** = `goqorhopar/b24`
7. **REPO_TOKEN** = `your_github_token`

## Как добавить секреты:

1. Откройте репозиторий на GitHub
2. Перейдите в `Settings` (настройки)
3. В левом меню выберите `Secrets and variables` → `Actions`
4. Нажмите `New repository secret`
5. Добавьте каждый секрет с соответствующим именем и значением

## После настройки секретов:

- При каждом push в ветку `main-fixed` будет автоматически запускаться деплой
- Можно также запустить деплой вручную через `Actions` → `Deploy Meeting Bot to Server` → `Run workflow`

## Проверка деплоя:

1. Перейдите в `Actions` в репозитории
2. Найдите последний запуск workflow
3. Проверьте логи выполнения
4. На сервере: `systemctl status meeting-bot.service`
