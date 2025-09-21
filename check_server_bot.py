#!/usr/bin/env python3
"""
Скрипт для проверки работы бота на сервере
"""

import requests
import json
import os
from dotenv import load_dotenv

def check_bot_status():
    """Проверяем статус бота через Telegram API"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return False
    
    print(f"🤖 Проверяем бота с токеном: {bot_token[:10]}...")
    
    # Проверяем информацию о боте
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info['result']
                print(f"✅ Бот активен: @{bot_data.get('username', 'N/A')}")
                print(f"   Имя: {bot_data.get('first_name', 'N/A')}")
                print(f"   ID: {bot_data.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Ошибка API: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False

def check_webhook_status():
    """Проверяем статус webhook"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                webhook_data = webhook_info['result']
                print(f"📡 Webhook URL: {webhook_data.get('url', 'Не установлен')}")
                print(f"   Последняя ошибка: {webhook_data.get('last_error_message', 'Нет ошибок')}")
                return True
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка проверки webhook: {e}")
        return False

def send_test_message():
    """Отправляем тестовое сообщение"""
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    
    if not bot_token or not admin_chat_id:
        print("❌ Не хватает TELEGRAM_BOT_TOKEN или ADMIN_CHAT_ID")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': admin_chat_id,
            'text': '🤖 Тестовое сообщение от бота!\n\nБот работает и готов к встречам!'
        }
        
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Тестовое сообщение отправлено!")
                return True
            else:
                print(f"❌ Ошибка отправки: {result.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка отправки сообщения: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверяем статус бота...")
    print("=" * 50)
    
    # Проверяем статус бота
    bot_ok = check_bot_status()
    print()
    
    # Проверяем webhook
    print("📡 Проверяем webhook...")
    check_webhook_status()
    print()
    
    # Отправляем тестовое сообщение
    if bot_ok:
        print("📤 Отправляем тестовое сообщение...")
        send_test_message()
    
    print("=" * 50)
    if bot_ok:
        print("✅ Бот готов к работе!")
    else:
        print("❌ Есть проблемы с ботом")
