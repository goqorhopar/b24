#!/usr/bin/env python3
"""
Скрипт для запуска бота с исправленными переменными окружения
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
    
    print("✅ Переменные окружения загружены")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    log.info(f"Получен сигнал {signum}. Завершение работы...")
    sys.exit(0)

def check_environment():
    """Проверка переменных окружения"""
    log.info("🔧 Проверка переменных окружения...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GEMINI_API_KEY',
        'BITRIX_WEBHOOK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        return False
    
    log.info("✅ Все необходимые переменные окружения настроены")
    return True

def check_dependencies():
    """Проверка зависимостей"""
    log.info("📦 Проверка зависимостей...")
    
    try:
        import flask
        import requests
        import google.generativeai as genai
        import selenium
        import whisper
        import torch
        log.info("✅ Все основные зависимости установлены")
        return True
    except ImportError as e:
        log.error(f"❌ Отсутствует зависимость: {e}")
        return False

def start_bot():
    """Запуск бота"""
    log.info("🚀 Запуск Telegram бота...")
    
    try:
        from main import main
        main()
    except Exception as e:
        log.error(f"❌ Ошибка при запуске бота: {e}")
        return False
    
    return True

def main():
    """Основная функция"""
    print("🤖 Запуск Telegram бота для автоматизации встреч")
    print("=" * 60)
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_env_manually()
    
    # Регистрация обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Проверки
    if not check_environment():
        log.error("❌ Проверка переменных окружения не пройдена")
        sys.exit(1)
    
    if not check_dependencies():
        log.error("❌ Проверка зависимостей не пройдена")
        sys.exit(1)
    
    # Запуск бота
    log.info("🎯 Все проверки пройдены. Запускаю бота...")
    
    try:
        start_bot()
    except KeyboardInterrupt:
        log.info("⏹️ Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        log.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)
    
    log.info("✅ Бот завершил работу")

if __name__ == "__main__":
    main()
