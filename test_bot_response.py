#!/usr/bin/env python3
"""
Тест ответа бота
"""

import os
import requests
import time

def test_bot_response():
    """Тестирует ответ бота на сообщение"""
    
    # Загружаем .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден!")
        return False
    
    print("🤖 Тестируем ответ бота...")
    
    # Отправляем тестовое сообщение боту
    chat_id = 7537953397  # ID администратора
    
    print(f"📤 Отправляем тестовое сообщение в чат {chat_id}...")
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "🧪 Тестовое сообщение для проверки работы бота"
            }
        )
        
        if response.json().get('ok'):
            print("✅ Тестовое сообщение отправлено!")
        else:
            print(f"❌ Ошибка отправки: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False
    
    # Ждем немного
    print("⏳ Ждем 3 секунды...")
    time.sleep(3)
    
    # Проверяем, получил ли бот сообщение
    print("🔍 Проверяем получение сообщения ботом...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"📨 Получено {len(updates)} обновлений")
            
            # Ищем наше тестовое сообщение
            for update in reversed(updates[-5:]):  # Проверяем последние 5
                if 'message' in update:
                    message = update['message']
                    if message.get('text') == "🧪 Тестовое сообщение для проверки работы бота":
                        print("✅ Бот получил тестовое сообщение!")
                        return True
            
            print("⚠️ Тестовое сообщение не найдено в обновлениях")
            return False
        else:
            print(f"❌ Ошибка получения обновлений: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения обновлений: {e}")
        return False

if __name__ == "__main__":
    success = test_bot_response()
    if success:
        print("\n✅ Бот работает корректно!")
    else:
        print("\n❌ Есть проблемы с ботом")
