@echo off
REM ===========================================
REM НАСТРОЙКА АВТОМАТИЧЕСКОГО ДЕПЛОЯ ДЛЯ WINDOWS
REM ===========================================

echo ⚙️ Настраиваю автоматический деплой Meeting Bot...

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python.
    pause
    exit /b 1
)

REM Проверяем наличие git
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git не найден. Установите Git.
    pause
    exit /b 1
)

REM Проверяем наличие .env файла
if not exist .env (
    echo ❌ Файл .env не найден!
    echo 📋 Скопируйте env_example.txt в .env и заполните настройки:
    echo    copy env_example.txt .env
    echo    notepad .env
    pause
    exit /b 1
)

echo 🔍 Проверяю настройки автоматического деплоя...

REM Проверяем настройки GitHub
findstr /C:"GITHUB_REPO=" .env | findstr /V "your_username/meeting-bot" >nul
if errorlevel 1 (
    echo ❌ GITHUB_REPO не настроен в .env
    echo    Укажите ваш репозиторий в формате: username/repo-name
    pause
    exit /b 1
)

findstr /C:"GITHUB_TOKEN=" .env | findstr /V "your_github_token_here" >nul
if errorlevel 1 (
    echo ❌ GITHUB_TOKEN не настроен в .env
    echo    Получите токен в GitHub: Settings ^> Developer settings ^> Personal access tokens
    pause
    exit /b 1
)

REM Проверяем настройки сервера
findstr /C:"DEPLOY_SERVER_URL=" .env | findstr /V "your_server_ip_or_domain" >nul
if errorlevel 1 (
    echo ❌ DEPLOY_SERVER_URL не настроен в .env
    echo    Укажите IP адрес или домен вашего сервера
    pause
    exit /b 1
)

echo ✅ Настройки проверены

REM Настраиваем git
echo 🔧 Настраиваю Git...
git config user.name "Auto Deployer" 2>nul
git config user.email "auto-deployer@meeting-bot.local" 2>nul

REM Создаем директорию .github/workflows если не существует
if not exist .github mkdir .github
if not exist .github\workflows mkdir .github\workflows

REM Запускаем настройку автоматического деплоя
echo 🚀 Запускаю настройку автоматического деплоя...
python auto_deploy.py --setup

if errorlevel 1 (
    echo ❌ Ошибка настройки автоматического деплоя
    pause
    exit /b 1
)

echo ✅ Автоматический деплой настроен

echo.
echo 🎉 Настройка автоматического деплоя завершена!
echo.
echo 📋 Что было настроено:
echo    ✅ GitHub Actions workflow
echo    ✅ Скрипт быстрого деплоя
echo    ✅ Автоматические коммиты
echo.
echo 🔧 Следующие шаги:
echo    1. Добавьте SSH ключ в GitHub Secrets:
echo       - DEPLOY_SERVER_URL
echo       - DEPLOY_SERVER_USER
echo       - DEPLOY_SSH_KEY
echo       - DEPLOY_SSH_PORT (опционально)
echo       - DEPLOY_SSH_PATH (опционально)
echo.
echo    2. Для быстрого деплоя используйте:
echo       deploy_automation.bat
echo.
echo    3. Для автоматического деплоя при каждом push:
echo       git add .
echo       git commit -m "Update"
echo       git push origin main
echo.
echo 📖 Подробная документация: AUTO_DEPLOY_GUIDE.md
echo.
pause
