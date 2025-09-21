#!/usr/bin/env python3
"""
Скрипт для запуска бота на сервере
"""

import os
import sys
import logging
import signal
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
