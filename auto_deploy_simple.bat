@echo off
chcp 65001 >nul
echo Автоматический деплой бота на сервер
echo ======================================

set /p SERVER_IP="Введите IP адрес сервера: "
set /p USERNAME="Введите имя пользователя на сервере: "
set /p SSH_PORT="Введите SSH порт (по умолчанию 22): "

if "%SSH_PORT%"=="" set SSH_PORT=22

echo.
echo Сервер: %USERNAME%@%SERVER_IP%:%SSH_PORT%
echo.

echo Создаем архив для деплоя...
powershell -Command "Compress-Archive -Path '*.py', '*.txt', '*.md', '*.sh', '.env', 'requirements.txt' -DestinationPath 'bot_deploy.zip' -Force"

echo Загружаем файлы на сервер...
scp -P %SSH_PORT% bot_deploy.zip %USERNAME%@%SERVER_IP%:~/

echo Настраиваем бота на сервере...
ssh -p %SSH_PORT% %USERNAME%@%SERVER_IP% "unzip -o bot_deploy.zip && pip3 install -r requirements.txt && pkill -f 'python.*start_bot' || true && pkill -f 'python.*main' || true && chmod +x quick_start_server.sh && nohup ./quick_start_server.sh > bot.log 2>&1 & && sleep 5 && ps aux | grep python | grep -v grep && tail -10 bot.log"

echo.
echo ДЕПЛОЙ ЗАВЕРШЕН!
echo Протестируйте бота: @TranscriptionleadBot
pause
