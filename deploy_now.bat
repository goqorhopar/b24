@echo off
echo 🚀 ДЕПЛОЙ БОТА НА СЕРВЕР
echo ================================

echo 📦 Создаем архив для деплоя...
powershell -Command "Compress-Archive -Path '*.py', '*.txt', '*.md', '*.sh', '.env', 'requirements.txt' -DestinationPath 'bot_deploy.zip' -Force"

echo ✅ Архив создан: bot_deploy.zip
echo.
echo 📋 ИНСТРУКЦИИ ДЛЯ ДЕПЛОЯ:
echo.
echo 1. Загрузите файл bot_deploy.zip на ваш сервер
echo 2. Подключитесь к серверу по SSH:
echo    ssh ваш_пользователь@ваш_сервер_ip
echo.
echo 3. На сервере выполните:
echo    unzip bot_deploy.zip
echo    chmod +x quick_start_server.sh
echo    ./quick_start_server.sh
echo.
echo 4. Проверьте работу:
echo    tail -f bot.log
echo.
echo 🎯 Бот будет работать на сервере и присоединяться к встречам!
echo.
pause
