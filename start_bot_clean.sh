#!/bin/bash
echo "🔄 Остановка всех процессов..."
pkill -f python
pkill -f Xvfb
pkill -f main.py
sleep 2

echo "🧹 Очистка блокировок..."
rm -f /tmp/.X99-lock /tmp/.X100-lock

echo "🖥️  Запуск виртуального дисплея..."
export DISPLAY=:100
Xvfb :100 -screen 0 1920x1080x24 &
sleep 3

echo "📱 Сброс Telegram..."
curl -X GET "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/deleteWebhook"
curl -X GET "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/getUpdates?offset=-1"

echo "🤖 Запуск бота..."
python main.py