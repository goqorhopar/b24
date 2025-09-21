#!/usr/bin/env python3
"""
Исправленный скрипт для запуска бота без emoji
"""

import os
import sys
import logging
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
    
    print("Переменные окружения загружены")

# Настройка логирования без emoji
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger(__name__)

def main():
    """Основная функция"""
    print("Запуск Telegram бота для автоматизации встреч")
    print("=" * 60)
    print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_env_manually()
    
    # Проверяем переменные
    required_vars = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY', 'BITRIX_WEBHOOK_URL']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ОШИБКА: Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print("Все необходимые переменные окружения настроены")
    
    # Проверяем зависимости
    try:
        import flask, requests, google.generativeai, selenium, whisper, torch
        print("Все основные зависимости установлены")
    except ImportError as e:
        print(f"ОШИБКА: Отсутствует зависимость: {e}")
        sys.exit(1)
    
    # Запускаем бота
    print("Все проверки пройдены. Запускаю бота...")
    
    try:
        # Импортируем и запускаем main.py
        from main import main as bot_main
        print("Бот запущен успешно!")
        print("Для остановки нажмите Ctrl+C")
        
        # Запускаем бота
        bot_main()
            
    except KeyboardInterrupt:
        print("Получен сигнал остановки. Завершение работы...")
    except Exception as e:
        print(f"ОШИБКА при запуске бота: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("Бот завершил работу")

if __name__ == "__main__":
    main()
