@echo off
echo ========================================
echo 🚀 НАСТРОЙКА CI/CD ДЛЯ TELEGRAM БОТА
echo ========================================
echo.

echo 📋 Шаг 1: Инициализация Git репозитория...
if not exist .git (
    git init
    git add .
    git commit -m "Initial commit"
    echo ✅ Git репозиторий инициализирован
) else (
    echo ✅ Git репозиторий уже существует
)

echo.
echo 📋 Шаг 2: Настройка SSH ключей...
bash setup_ssh_keys.sh

echo.
echo 📋 Шаг 3: Настройка уведомлений...
python setup_notifications.py

echo.
echo 📋 Шаг 4: Создание GitHub репозитория...
echo ⚠️ ВАЖНО: Создайте репозиторий на GitHub вручную:
echo    1. Перейдите на https://github.com/new
echo    2. Название: telegram-bot
echo    3. Описание: Telegram bot with Gemini AI and Bitrix24 integration
echo    4. Сделайте репозиторий приватным
echo    5. НЕ добавляйте README, .gitignore или лицензию

echo.
echo 📋 Шаг 5: Добавление remote origin...
echo Введите URL вашего GitHub репозитория:
set /p GITHUB_URL="GitHub URL: "
git remote add origin %GITHUB_URL%

echo.
echo 📋 Шаг 6: Настройка GitHub Secrets...
echo ⚠️ ВАЖНО: Добавьте следующие секреты в настройках репозитория:
echo    VPS_HOST: 109.172.47.253
echo    VPS_USERNAME: root
echo    VPS_SSH_KEY: содержимое ~/.ssh/id_rsa
echo    SLACK_WEBHOOK: ваш_webhook_url (опционально)

echo.
echo 📋 Шаг 7: Настройка webhook...
echo ⚠️ ВАЖНО: Разместите deploy_webhook.php на VPS:
echo    1. Скопируйте deploy_webhook.php на VPS в корень веб-сервера
echo    2. Настройте права: chmod 755 /var/www/html/deploy_webhook.php
echo    3. В GitHub добавьте webhook:
echo       URL: http://109.172.47.253/deploy_webhook.php
echo       Secret: your-secret-key-here

echo.
echo 📋 Шаг 8: Первый деплой...
git add .
git commit -m "Setup CI/CD pipeline"
git push -u origin main

echo.
echo ========================================
echo ✅ НАСТРОЙКА CI/CD ЗАВЕРШЕНА!
echo ========================================
echo.
echo 🎉 Что дальше:
echo    1. Создайте GitHub репозиторий
echo    2. Добавьте секреты в GitHub
echo    3. Настройте webhook на VPS
echo    4. Запустите первый деплой
echo.
echo 📚 Подробная инструкция: CI_CD_SETUP.md
echo.
pause
