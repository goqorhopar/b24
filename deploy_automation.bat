@echo off
REM ===========================================
REM АВТОМАТИЧЕСКИЙ ДЕПЛОЙ ДЛЯ WINDOWS
REM ===========================================

echo 🚀 Начинаю автоматический деплой Meeting Bot...

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

echo 🔍 Проверяю конфигурацию...

REM Проверяем обязательные переменные
findstr /C:"TELEGRAM_BOT_TOKEN=" .env | findstr /V "your_telegram_bot_token_here" >nul
if errorlevel 1 (
    echo ❌ TELEGRAM_BOT_TOKEN не настроен в .env
    pause
    exit /b 1
)

findstr /C:"GEMINI_API_KEY=" .env | findstr /V "your_gemini_api_key_here" >nul
if errorlevel 1 (
    echo ❌ GEMINI_API_KEY не настроен в .env
    pause
    exit /b 1
)

echo ✅ Конфигурация проверена

REM Коммит и пуш в GitHub
echo 📤 Отправляю изменения в GitHub...
python auto_deploy.py --commit

if errorlevel 1 (
    echo ❌ Ошибка отправки в GitHub
    pause
    exit /b 1
)

echo ✅ Изменения отправлены в GitHub

REM Деплой на сервер
echo 🖥️ Деплою на сервер...
python auto_deploy.py --deploy

if errorlevel 1 (
    echo ❌ Ошибка деплоя на сервер
    pause
    exit /b 1
)

echo ✅ Деплой на сервер завершен

echo.
echo 🎉 Автоматический деплой завершен успешно!
echo.
echo 📋 Что было сделано:
echo    ✅ Изменения отправлены в GitHub
echo    ✅ Код развернут на сервере
echo    ✅ Сервис перезапущен
echo.
echo 🔍 Для проверки статуса сервиса:
echo    ssh user@server "systemctl status meeting-bot"
echo.
echo 📋 Для просмотра логов:
echo    ssh user@server "journalctl -u meeting-bot -f"
echo.
pause
