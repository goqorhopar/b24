@echo off
echo 🔍 Проверяем Telegram бота...

echo.
echo 1. Проверяем бота через API...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/getMe'; Write-Host '✅ Бот активен:' $response.result.first_name '@' $response.result.username } catch { Write-Host '❌ Ошибка:' $_.Exception.Message }"

echo.
echo 2. Проверяем webhook...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/getWebhookInfo'; Write-Host 'Webhook URL:' $response.result.url; Write-Host 'Ожидает обновлений:' $response.result.pending_update_count } catch { Write-Host '❌ Ошибка:' $_.Exception.Message }"

echo.
echo 3. Проверяем обновления...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/getUpdates'; Write-Host 'Получено обновлений:' $response.result.Count } catch { Write-Host '❌ Ошибка:' $_.Exception.Message }"

echo.
echo 4. Проверяем сервер...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://109.172.47.253:3000/health' -TimeoutSec 5; Write-Host '✅ Сервер отвечает на порту 3000' } catch { Write-Host '❌ Порт 3000 недоступен' }"

powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://109.172.47.253:8080/health' -TimeoutSec 5; Write-Host '✅ Сервер отвечает на порту 8080' } catch { Write-Host '❌ Порт 8080 недоступен' }"

echo.
echo 💡 Откройте test_bot.html в браузере для интерактивной проверки
pause
