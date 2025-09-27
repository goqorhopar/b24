#!/usr/bin/env python3
import requests
import json

print("🔍 Проверяем Telegram бота...")

try:
    token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    response = requests.get(url, timeout=10)
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("ok"):
            bot_info = data.get("result", {})
            print(f"✅ Бот активен: {bot_info.get('first_name')} (@{bot_info.get('username')})")
        else:
            print(f"❌ Ошибка API: {data}")
    else:
        print(f"❌ HTTP ошибка: {response.status_code}")
        print(f"Текст ответа: {response.text}")
        
except Exception as e:
    print(f"💥 Исключение: {e}")

print("\n🔍 Проверяем webhook...")

try:
    webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    response = requests.get(webhook_url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Webhook ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        if data.get("ok"):
            webhook_info = data.get("result", {})
            print(f"Webhook URL: {webhook_info.get('url', 'Не установлен')}")
            print(f"Ожидает обновлений: {webhook_info.get('pending_update_count', 0)}")
    else:
        print(f"❌ Webhook HTTP ошибка: {response.status_code}")
        
except Exception as e:
    print(f"💥 Webhook исключение: {e}")
