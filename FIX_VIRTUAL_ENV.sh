#!/bin/bash
# FIX_VIRTUAL_ENV.sh - Создание виртуального окружения для бота

echo "🐍 СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ ДЛЯ БОТА"
echo "==========================================="

# 1. Останавливаем бота
echo "⏹️ Останавливаю бота..."
sudo systemctl stop telegram-bot

# 2. Создаем виртуальное окружение
echo "🔧 Создаю виртуальное окружение..."
cd /opt/telegram-bot
python3 -m venv venv

# 3. Активируем виртуальное окружение и устанавливаем пакеты
echo "📦 Устанавливаю пакеты в виртуальное окружение..."
source venv/bin/activate
pip install --upgrade pip
pip install flask requests selenium python-telegram-bot python-dotenv

# 4. Проверяем установку пакетов
echo "🧪 Проверяю установку пакетов..."
python -c "
try:
    import flask
    print(\"✅ Flask:\", flask.__version__)
except Exception as e:
    print(\"❌ Flask не найден:\", e)

try:
    import requests
    print(\"✅ Requests:\", requests.__version__)
except Exception as e:
    print(\"❌ Requests не найден:\", e)

try:
    import selenium
    print(\"✅ Selenium:\", selenium.__version__)
except Exception as e:
    print(\"❌ Selenium не найден:\", e)

try:
    import telegram
    print(\"✅ Python-telegram-bot установлен\")
except Exception as e:
    print(\"❌ Python-telegram-bot не найден:\", e)

try:
    import dotenv
    print(\"✅ Python-dotenv установлен\")
except Exception as e:
    print(\"❌ Python-dotenv не найден:\", e)
"

# 5. Обновляем systemd сервис для использования виртуального окружения
echo "🔧 Обновляю systemd сервис..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << "EOF"
[Unit]
Description=Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/telegram-bot
ExecStart=/opt/telegram-bot/venv/bin/python /opt/telegram-bot/main.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/telegram-bot
Environment=DISPLAY=:99

[Install]
WantedBy=multi-user.target
EOF

# 6. Перезагружаем systemd
echo "🔄 Перезагружаю systemd..."
sudo systemctl daemon-reload

# 7. Очищаем кеш Python
echo "🧹 Очищаю кеш Python..."
sudo find /opt/telegram-bot -type f -name "*.pyc" -delete
sudo find /opt/telegram-bot -type d -name "__pycache__" -exec rm -rf {} +

# 8. Запускаем бота
echo "🚀 Запускаю бота..."
sudo systemctl start telegram-bot

# 9. Проверяем статус
echo "✅ Проверяю статус бота..."
sudo systemctl status telegram-bot --no-pager

# 10. Показываем последние логи
echo ""
echo "📋 Последние 10 строк логов:"
journalctl -u telegram-bot -n 10 --no-pager

echo ""
echo "🎉 СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ ЗАВЕРШЕНО!"
echo "📋 Для мониторинга логов: journalctl -u telegram-bot -f"
echo "📋 Виртуальное окружение: /opt/telegram-bot/venv"
