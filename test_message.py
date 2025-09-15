#!/usr/bin/env python3
"""
Скрипт для тестирования отправки сообщений боту
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
        return
    
    # Получаем информацию о боте
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        bot_info = response.json()['result']
        print(f"🤖 Бот: @{bot_info['username']}")
    except Exception as e:
        print(f"❌ Ошибка получения информации о боте: {e}")
        return
    
    # Получаем последние обновления
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates")
        updates = response.json()['result']
        
        if not updates:
            print("❌ Нет сообщений от пользователей")
            print("   Отправьте сообщение боту @TranscriptionleadBot в Telegram")
            return
        
        # Берем последнее сообщение
        last_update = updates[-1]
        if 'message' in last_update:
            message = last_update['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            user = message.get('from', {})
            
            print(f"📨 Последнее сообщение:")
            print(f"   От: {user.get('first_name', 'Unknown')} (@{user.get('username', 'no_username')})")
            print(f"   Чат ID: {chat_id}")
            print(f"   Текст: {text}")
            
            # Отправляем ответ
            print(f"\n📤 Отправляем ответ...")
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "✅ Бот работает! Я получил ваше сообщение."
                }
            )
            
            if response.json().get('ok'):
                print("✅ Ответ отправлен успешно!")
            else:
                print(f"❌ Ошибка отправки: {response.json()}")
        else:
            print("❌ Последнее обновление не содержит сообщения")
            
    except Exception as e:
        print(f"❌ Ошибка получения обновлений: {e}")

if __name__ == "__main__":
    send_test_message()
