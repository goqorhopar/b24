#!/bin/bash

echo "🔍 Диагностика бота и автоматизации встреч"
echo "=========================================="

# Проверяем статус бота
echo "1. Статус бота:"
systemctl status telegram-bot --no-pager -l

echo -e "\n2. Последние логи бота:"
journalctl -u telegram-bot -n 20 --no-pager

echo -e "\n3. Проверяем наличие виртуального дисплея:"
if command -v Xvfb &> /dev/null; then
    echo "✅ Xvfb установлен"
    ps aux | grep Xvfb | grep -v grep || echo "❌ Xvfb не запущен"
else
    echo "❌ Xvfb не установлен"
fi

echo -e "\n4. Проверяем переменную DISPLAY:"
echo "DISPLAY = $DISPLAY"

echo -e "\n5. Проверяем браузеры:"
if command -v firefox &> /dev/null; then
    echo "✅ Firefox установлен"
else
    echo "❌ Firefox не установлен"
fi

if command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium установлен"
else
    echo "❌ Chromium не установлен"
fi

echo -e "\n6. Проверяем Python модули:"
cd /opt/telegram-bot
source venv/bin/activate
python -c "
try:
    import pyautogui
    print('✅ pyautogui доступен')
except ImportError as e:
    print(f'❌ pyautogui недоступен: {e}')

try:
    import selenium
    print('✅ selenium доступен')
except ImportError as e:
    print(f'❌ selenium недоступен: {e}')

try:
    from meeting_link_processor import meeting_link_processor
    print('✅ meeting_link_processor доступен')
except ImportError as e:
    print(f'❌ meeting_link_processor недоступен: {e}')
except Exception as e:
    print(f'⚠️ meeting_link_processor ошибка: {e}')
"

echo -e "\n7. Проверяем конфигурацию:"
if [ -f "/opt/telegram-bot/.env" ]; then
    echo "✅ .env файл существует"
    if grep -q "TELEGRAM_BOT_TOKEN" /opt/telegram-bot/.env; then
        echo "✅ TELEGRAM_BOT_TOKEN найден"
    else
        echo "❌ TELEGRAM_BOT_TOKEN не найден"
    fi
else
    echo "❌ .env файл не найден"
fi

echo -e "\n8. Проверяем текущий main.py:"
if grep -q "MEETING_AUTOMATION_AVAILABLE" /opt/telegram-bot/main.py; then
    echo "✅ main.py поддерживает автоматизацию встреч"
else
    echo "❌ main.py не поддерживает автоматизацию встреч"
fi

echo -e "\n9. Тест подключения к Telegram API:"
cd /opt/telegram-bot
source venv/bin/activate
python -c "
import os
import requests
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
if token:
    try:
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print(f'✅ Бот подключен: {data[\"result\"][\"first_name\"]}')
            else:
                print(f'❌ Ошибка API: {data}')
        else:
            print(f'❌ HTTP ошибка: {response.status_code}')
    except Exception as e:
        print(f'❌ Ошибка подключения: {e}')
else:
    print('❌ Токен не найден')
"

echo -e "\n10. Рекомендации по исправлению:"
echo "=================================="

# Проверяем, что нужно исправить
if ! command -v Xvfb &> /dev/null; then
    echo "📦 Установите виртуальный дисплей:"
    echo "   apt update && apt install -y xvfb x11vnc fluxbox firefox-esr chromium-browser pulseaudio alsa-utils"
fi

if ! grep -q "MEETING_AUTOMATION_AVAILABLE" /opt/telegram-bot/main.py; then
    echo "🔄 Обновите main.py:"
    echo "   cp main_with_meeting_automation.py main.py"
fi

if [ ! -f "/opt/telegram-bot/start_with_display.sh" ]; then
    echo "📝 Создайте скрипт запуска с дисплеем"
fi

echo -e "\n✅ Диагностика завершена!"
