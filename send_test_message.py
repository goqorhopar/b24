#!/usr/bin/env python3
"""
Отправка тестового сообщения боту
"""

import os
import requests
import time

def send_test_message():
    """Отправляет тестовое сообщение боту"""
    
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
    
    print("🤖 Отправляем тестовое сообщение боту...")
    
    # Отправляем сообщение боту
    chat_id = 7537953397  # ID администратора
    
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "👋 Привет! Это тестовое сообщение для проверки работы бота."
            }
        )
        
        if response.json().get('ok'):
            print("✅ Сообщение отправлено боту!")
            print("📱 Проверьте Telegram - бот должен ответить")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

if __name__ == "__main__":
    send_test_message()
