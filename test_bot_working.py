#!/usr/bin/env python3
"""
Тест работы бота
"""

import requests
import time

def test_telegram_bot():
    """Тест подключения к Telegram боту"""
    print("Тестирование Telegram бота...")
    
    token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот работает: @{bot_info.get('username')}")
                print(f"   Имя: {bot_info.get('first_name')}")
                print(f"   ID: {bot_info.get('id')}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_webhook_status():
    """Тест статуса webhook"""
    print("\nТестирование webhook...")
    
    token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print(f"✅ Webhook статус: {webhook_info.get('url', 'Не установлен')}")
                print(f"   Последняя ошибка: {webhook_info.get('last_error_message', 'Нет')}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("Проверка работы бота")
    print("=" * 40)
    
    # Тест бота
    bot_ok = test_telegram_bot()
    
    # Тест webhook
    webhook_ok = test_webhook_status()
    
    print("\n" + "=" * 40)
    if bot_ok and webhook_ok:
        print("✅ Бот работает корректно!")
        print("\nДля тестирования:")
        print("1. Найдите бота: @TranscriptionleadBot")
        print("2. Отправьте команду: /start")
        print("3. Отправьте ссылку на встречу")
    else:
        print("❌ Есть проблемы с ботом")
        if not bot_ok:
            print("- Проблема с Telegram API")
        if not webhook_ok:
            print("- Проблема с webhook")

if __name__ == "__main__":
    main()
