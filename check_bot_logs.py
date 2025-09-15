#!/usr/bin/env python3
"""
Проверка логов бота
"""

import os
import requests
import time

def check_bot_logs():
    """Проверяет логи бота"""
    
    print("🔍 Проверяем логи бота...")
    
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
    
    # Проверяем, что бот запущен
    print("🔍 Проверяем, что бот запущен...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Бот подключен: @{bot_info['username']}")
        else:
            print(f"❌ Ошибка API: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False
    
    # Проверяем обновления
    print("\n📨 Проверяем обновления...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getUpdates", timeout=10)
        data = response.json()
        
        if data.get('ok'):
            updates = data.get('result', [])
            print(f"📨 Получено {len(updates)} обновлений")
            
            if updates:
                print("📋 Последние обновления:")
                for i, update in enumerate(updates[-3:]):
                    if 'message' in update:
                        message = update['message']
                        text = message.get('text', '')
                        user = message.get('from', {})
                        print(f"  {i+1}. От {user.get('first_name', 'Unknown')}: {text}")
            else:
                print("ℹ️ Нет новых сообщений")
        else:
            print(f"❌ Ошибка получения обновлений: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка получения обновлений: {e}")
    
    # Проверяем webhook
    print("\n🔗 Проверяем webhook...")
    
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10)
        data = response.json()
        
        if data.get('ok'):
            webhook_info = data['result']
            if webhook_info.get('url'):
                print(f"⚠️ Webhook установлен: {webhook_info['url']}")
            else:
                print("✅ Webhook не установлен")
        else:
            print(f"❌ Ошибка получения webhook: {data}")
            
    except Exception as e:
        print(f"❌ Ошибка проверки webhook: {e}")
    
    print("\n✅ Проверка завершена!")
    return True

if __name__ == "__main__":
    check_bot_logs()
