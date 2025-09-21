#!/bin/bash
# Скрипт для развертывания бота на Linux сервере

echo "🚀 Развертывание Telegram бота на Linux сервере"
echo "=============================================="

# Проверка операционной системы
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Этот скрипт предназначен для Linux!"
    exit 1
fi

echo "✅ Операционная система: Linux"

# Обновление системы
echo "📦 Обновление системы..."
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
echo "🐍 Установка Python..."
sudo apt install -y python3 python3-pip python3-venv

# Установка системных зависимостей
echo "🔧 Установка системных зависимостей..."
sudo apt install -y \
    pulseaudio \
    pulseaudio-utils \
    pavucontrol \
    alsa-utils \
    ffmpeg \
    wget \
    curl \
    unzip \
    xvfb \
    x11vnc \
    fluxbox

# Установка Chrome/Chromium
echo "🌐 Установка Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Установка ChromeDriver
echo "🚗 Установка ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1-3)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm /tmp/chromedriver.zip

# Создание пользователя для бота
echo "👤 Создание пользователя bot..."
sudo useradd -m -s /bin/bash bot
sudo usermod -aG audio bot
sudo usermod -aG pulse-access bot

# Создание директории для бота
echo "📁 Создание директории для бота..."
sudo mkdir -p /opt/meeting-bot
sudo chown bot:bot /opt/meeting-bot

# Копирование файлов бота
echo "📋 Копирование файлов бота..."
sudo cp -r . /opt/meeting-bot/
sudo chown -R bot:bot /opt/meeting-bot

# Создание виртуального окружения
echo "🔧 Создание виртуального окружения..."
sudo -u bot python3 -m venv /opt/meeting-bot/venv
sudo -u bot /opt/meeting-bot/venv/bin/pip install --upgrade pip

# Установка Python зависимостей
echo "📦 Установка Python зависимостей..."
sudo -u bot /opt/meeting-bot/venv/bin/pip install -r /opt/meeting-bot/requirements.txt

# Создание systemd сервиса
echo "⚙️ Создание systemd сервиса..."
sudo tee /etc/systemd/system/meeting-bot.service > /dev/null <<EOF
[Unit]
Description=Meeting Bot
After=network.target

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=/opt/meeting-bot
Environment=PATH=/opt/meeting-bot/venv/bin
ExecStart=/opt/meeting-bot/venv/bin/python /opt/meeting-bot/start_bot_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Переменные окружения
Environment=DISPLAY=:99
Environment=PULSE_RUNTIME_PATH=/run/user/1000/pulse

[Install]
WantedBy=multi-user.target
EOF

# Создание скрипта запуска для сервера
echo "📝 Создание скрипта запуска..."
sudo tee /opt/meeting-bot/start_bot_server.py > /dev/null <<'EOF'
#!/usr/bin/env python3
"""
Скрипт запуска бота на Linux сервере
"""

import os
import sys
import logging
import signal
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ручная загрузка переменных окружения
def load_env_manually():
    """Загрузка переменных окружения вручную"""
    env_vars = {
        'TELEGRAM_BOT_TOKEN': '7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI',
        'GEMINI_API_KEY': 'AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI',
        'GEMINI_MODEL': 'gemini-1.5-pro',
        'GEMINI_TEMPERATURE': '0.1',
        'GEMINI_TOP_P': '0.2',
        'GEMINI_MAX_TOKENS': '1200',
        'BITRIX_WEBHOOK_URL': 'https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31',
        'BITRIX_RESPONSIBLE_ID': '1',
        'BITRIX_CREATED_BY_ID': '1',
        'BITRIX_TASK_DEADLINE_DAYS': '3',
        'PORT': '3000',
        'DB_PATH': 'bot_state.db',
        'LOG_LEVEL': 'INFO',
        'NODE_ENV': 'production',
        'MAX_RETRIES': '3',
        'RETRY_DELAY': '2',
        'REQUEST_TIMEOUT': '30',
        'MAX_COMMENT_LENGTH': '8000',
        'ADMIN_CHAT_ID': '7537953397',
        'MEETING_DISPLAY_NAME': 'Ассистент Григория Сергеевича',
        'MEETING_HEADLESS': 'true',
        'MEETING_AUTO_LEAVE': 'true',
        'MEETING_DURATION_MINUTES': '60'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/meeting-bot/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    log.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)

def main():
    """Основная функция"""
    print("🤖 Запуск Telegram бота на Linux сервере")
    print("=" * 50)
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Загружаем переменные окружения
    load_env_manually()
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Проверяем переменные
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY', 'BITRIX_WEBHOOK_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        log.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        sys.exit(1)
    
    log.info("✅ Все необходимые переменные окружения настроены")
    
    # Проверяем зависимости
    try:
        import flask, requests, google.generativeai, selenium, whisper, torch
        log.info("✅ Все основные зависимости установлены")
    except ImportError as e:
        log.error(f"❌ Отсутствует зависимость: {e}")
        sys.exit(1)
    
    # Запускаем бота
    log.info("🎯 Все проверки пройдены. Запускаю бота...")
    
    try:
        from main import main as bot_main
        log.info("🚀 Бот запущен успешно!")
        bot_main()
            
    except KeyboardInterrupt:
        log.info("⏹️ Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        log.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    log.info("✅ Бот завершил работу")

if __name__ == "__main__":
    main()
EOF

# Создание скрипта управления
echo "🔧 Создание скрипта управления..."
sudo tee /opt/meeting-bot/manage_bot.sh > /dev/null <<'EOF'
#!/bin/bash
# Скрипт управления ботом

case "$1" in
    start)
        echo "🚀 Запуск бота..."
        sudo systemctl start meeting-bot
        sudo systemctl status meeting-bot
        ;;
    stop)
        echo "⏹️ Остановка бота..."
        sudo systemctl stop meeting-bot
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        sudo systemctl restart meeting-bot
        sudo systemctl status meeting-bot
        ;;
    status)
        echo "📊 Статус бота:"
        sudo systemctl status meeting-bot
        ;;
    logs)
        echo "📋 Логи бота:"
        sudo journalctl -u meeting-bot -f
        ;;
    enable)
        echo "✅ Включение автозапуска..."
        sudo systemctl enable meeting-bot
        ;;
    disable)
        echo "❌ Отключение автозапуска..."
        sudo systemctl disable meeting-bot
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|status|logs|enable|disable}"
        exit 1
        ;;
esac
EOF

sudo chmod +x /opt/meeting-bot/manage_bot.sh

# Настройка PulseAudio для пользователя bot
echo "🔊 Настройка PulseAudio..."
sudo -u bot mkdir -p /home/bot/.config/pulse
sudo -u bot tee /home/bot/.config/pulse/client.conf > /dev/null <<EOF
default-server = unix:/run/user/1000/pulse/native
autospawn = no
daemon-binary = /bin/true
enable-shm = false
EOF

# Перезагрузка systemd
echo "🔄 Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включение автозапуска
echo "✅ Включение автозапуска..."
sudo systemctl enable meeting-bot

# Запуск бота
echo "🚀 Запуск бота..."
sudo systemctl start meeting-bot

echo ""
echo "🎉 Развертывание завершено!"
echo "=========================="
echo ""
echo "📋 Команды управления:"
echo "  sudo /opt/meeting-bot/manage_bot.sh start    - запустить бота"
echo "  sudo /opt/meeting-bot/manage_bot.sh stop     - остановить бота"
echo "  sudo /opt/meeting-bot/manage_bot.sh restart  - перезапустить бота"
echo "  sudo /opt/meeting-bot/manage_bot.sh status   - статус бота"
echo "  sudo /opt/meeting-bot/manage_bot.sh logs     - логи бота"
echo ""
echo "📊 Проверка статуса:"
sudo systemctl status meeting-bot
echo ""
echo "📋 Логи:"
echo "sudo journalctl -u meeting-bot -f"
echo ""
echo "✅ Бот готов к работе на сервере!"
