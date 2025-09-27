@echo off
echo 🔄 Перезапускаем сервис на сервере...

echo.
echo Шаг 1: Остановка сервиса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl stop meeting-bot.service"

echo.
echo Шаг 2: Проверка статуса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl status meeting-bot.service --no-pager"

echo.
echo Шаг 3: Запуск сервиса...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl start meeting-bot.service"

echo.
echo Шаг 4: Проверка статуса после запуска...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "systemctl status meeting-bot.service --no-pager"

echo.
echo Шаг 5: Проверка логов...
echo MmSS0JSm%%6vb | ssh -o StrictHostKeyChecking=no root@109.172.47.253 "journalctl -u meeting-bot.service --no-pager -n 20"

echo.
echo ✅ Перезапуск завершен!
echo 📱 Теперь попробуйте отправить боту сообщение
pause
