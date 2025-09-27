@echo off
echo 🧪 Тестирование MCP сервера
echo ============================

set GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
set BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/
set TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI

echo ✅ Переменные окружения установлены
echo 🧪 Запуск тестов...

python test_mcp.py

pause
