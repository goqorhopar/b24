#!/usr/bin/env python3
"""
Скрипт для диагностики бота
"""

import os
import sys
import requests
import time

def debug_bot():
    """Диагностирует проблемы с ботом"""
    
    print("🔍 Диагностика бота...")
    
    # Загружаем .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")
    except Exception as e:
        print(f"⚠️ Ошибка загрузки .env: {e}")
    
    # Проверяем токены
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден!")
        return False
    
    print(f"✅ TELEGRAM_BOT_TOKEN найден: {bot_token[:10]}...")
    
    # Проверяем подключение к Telegram API
    print("\n📡 Проверяем подключение к Telegram API...")
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
    print("\n📦 Проверяем импорты...")
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
    print("\n⚙️ Проверяем конфигурацию...")
    validation = config.validate()
    if validation['valid']:
        print("✅ Конфигурация валидна")
    else:
        print(f"❌ Отсутствуют переменные: {validation['missing_vars']}")
        return False
    
    # Проверяем базу данных
    print("\n🗄️ Проверяем базу данных...")
    try:
        init_db()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False
    
    # Проверяем polling
    print("\n🔄 Проверяем polling...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=10)
        data = response.json()
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"✅ Polling работает, получено {len(updates)} обновлений")
        else:
            print(f"❌ Ошибка polling: {data}")
            return False
    except Exception as e:
        print(f"❌ Ошибка polling: {e}")
        return False
    
    print("\n✅ Диагностика завершена успешно!")
    print("📝 Бот должен работать. Попробуйте отправить ему сообщение в Telegram.")
    
    return True

if __name__ == "__main__":
    success = debug_bot()
    sys.exit(0 if success else 1)
