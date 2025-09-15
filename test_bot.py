#!/usr/bin/env python3
"""
Тестовый скрипт для проверки бота
"""

import os
import sys
import requests
import time

def test_bot():
    """Тестирует основные функции бота"""
    
    print("🧪 Тестируем бота...")
    
    # Проверяем переменные окружения
    print("\n1. Проверяем переменные окружения...")
    
    # Загружаем .env если есть
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")
    except ImportError:
        print("⚠️ python-dotenv не установлен")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки .env: {e}")
    
    # Проверяем токены
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден!")
        print("   Создайте файл .env с токеном бота")
        return False
    
    if not gemini_key:
        print("❌ GEMINI_API_KEY не найден!")
        print("   Добавьте ключ Gemini в .env файл")
        return False
    
    print("✅ Токены найдены")
    
    # Проверяем подключение к Telegram API
    print("\n2. Проверяем подключение к Telegram API...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Бот подключен: @{bot_info['username']} ({bot_info['first_name']})")
        else:
            print(f"❌ Ошибка API: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False
    
    # Проверяем импорты
    print("\n3. Проверяем импорты...")
    
    try:
        from config import config
        print("✅ config.py импортирован")
        
        from gemini_client import analyze_transcript_structured
        print("✅ gemini_client.py импортирован")
        
        from bitrix import update_lead_comprehensive
        print("✅ bitrix.py импортирован")
        
        from db import init_db
        print("✅ db.py импортирован")
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    # Проверяем конфигурацию
    print("\n4. Проверяем конфигурацию...")
    
    validation = config.validate()
    if validation['valid']:
        print("✅ Конфигурация валидна")
    else:
        print(f"❌ Отсутствуют переменные: {validation['missing_vars']}")
        return False
    
    # Проверяем базу данных
    print("\n5. Проверяем базу данных...")
    
    try:
        init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False
    
    print("\n✅ Все тесты пройдены! Бот готов к работе.")
    print("\n📝 Для запуска бота выполните:")
    print("   python main.py")
    
    return True

if __name__ == "__main__":
    success = test_bot()
    sys.exit(0 if success else 1)
