#!/usr/bin/env python3
"""
Простой тест бота для проверки работы
"""
import requests
import time
import json

# Конфигурация
BOT_TOKEN = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHAT_ID = "7537953397"

def send_message(text):
    """Отправляет сообщение боту"""
    url = f"{BASE_URL}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, json=data)
    return response.json()

def get_updates(offset=None):
    """Получает обновления"""
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    response = requests.get(url, params=params)
    return response.json()

def main():
    print("🤖 Тестирую бота...")
    
    # Отправляем тестовое сообщение
    print("📤 Отправляю тестовое сообщение...")
    result = send_message("🔧 Тест бота - проверка связи")
    print(f"✅ Сообщение отправлено: {result}")
    
    # Ждем и получаем обновления
    print("⏳ Жду 5 секунд...")
    time.sleep(5)
    
    print("📥 Получаю обновления...")
    updates = get_updates()
    print(f"📋 Обновления: {json.dumps(updates, indent=2, ensure_ascii=False)}")
    
    if updates.get("ok") and updates.get("result"):
        print(f"✅ Получено {len(updates['result'])} обновлений")
        for update in updates["result"]:
            if "message" in update:
                msg = update["message"]
                print(f"📨 Сообщение: {msg.get('text', 'Нет текста')}")
    else:
        print("❌ Нет обновлений")

if __name__ == "__main__":
    main()