@echo off
echo Starting Autonomous Meeting Bot...
set TELEGRAM_BOT_TOKEN=7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI
set GEMINI_API_KEY=AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI
set BITRIX_WEBHOOK_URL=https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/

python autonomous_bot.py
pause
