#!/usr/bin/env python3
"""
Простой тестовый бот для проверки работы
"""

import os
import requests
import time
import threading

# Загружаем .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Получаем токен
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
if not bot_token:
    print("❌ TELEGRAM_BOT_TOKEN не найден!")
    exit(1)

BASE_URL = f"https://api.telegram.org/bot{bot_token}"

def send_message(chat_id, text):
    """Отправляет сообщение в Telegram"""
    try:
        response = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15
        )
        response.raise_for_status()
        print(f"✅ Отправлено сообщение в чат {chat_id}: {text}")
    except Exception as e:
        print(f"❌ Ошибка отправки сообщения: {e}")

def process_message(msg):
    """Обрабатывает сообщение"""
    if not msg:
        return
    
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()
    user = msg.get("from", {})
    
    print(f"📨 Получено сообщение от {user.get('first_name', 'Unknown')}: {text}")
    
    # Простой ответ
    if text.lower() in ("/start", "start"):
        send_message(chat_id, "👋 Привет! Я простой тестовый бот. Отправь мне любое сообщение!")
    elif text.lower() in ("/help", "help"):
        send_message(chat_id, "ℹ️ Это простой тестовый бот. Я отвечаю на все сообщения!")
    else:
        send_message(chat_id, f"🤖 Получил твое сообщение: '{text}'. Бот работает!")

def polling_worker():
    """Фоновый процесс для polling"""
    offset = 0
    print("🔄 Запускаем polling...")
    
    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    if "message" in update:
                        process_message(update["message"])
                    offset = update["update_id"] + 1
            else:
                print(f"❌ Ошибка API: {data}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            time.sleep(15)

if __name__ == "__main__":
    print("🤖 Запускаем простой тестовый бот...")
    
    # Проверяем подключение
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        data = response.json()
        
        if data.get('ok'):
            bot_info = data['result']
            print(f"✅ Бот подключен: @{bot_info['username']} ({bot_info['first_name']})")
        else:
            print(f"❌ Ошибка подключения: {data}")
            exit(1)
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        exit(1)
    
    # Запускаем polling
    polling_thread = threading.Thread(target=polling_worker, daemon=True)
    polling_thread.start()
    
    print("✅ Бот запущен! Отправьте ему сообщение в Telegram.")
    print("📱 Бот: @TranscriptionleadBot")
    print("⏹️ Для остановки нажмите Ctrl+C")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Останавливаем бота...")
        exit(0)
