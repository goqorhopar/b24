#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

def check_bot_health():
    """Проверка здоровья бота через health endpoint"""
    try:
        # Пробуем разные порты
        ports = [3000, 8080, 80, 443]
        
        for port in ports:
            try:
                url = f"http://109.172.47.253:{port}/health"
                print(f"🔍 Проверяем {url}...")
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Бот отвечает на порту {port}")
                    print(f"   Ответ: {response.json()}")
                    return True
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Порт {port} недоступен: {e}")
                continue
                
        return False
        
    except Exception as e:
        print(f"💥 Ошибка проверки: {e}")
        return False

def test_telegram_bot():
    """Тестирование Telegram бота"""
    try:
        token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        print("🤖 Проверяем Telegram бота...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data.get("result", {})
                print(f"✅ Telegram бот активен")
                print(f"   Имя: {bot_info.get('first_name', 'N/A')}")
                print(f"   Username: @{bot_info.get('username', 'N/A')}")
                return True
            else:
                print(f"❌ Telegram API ошибка: {data}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка проверки Telegram: {e}")
        return False

def check_webhook():
    """Проверка webhook"""
    try:
        token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        
        print("🔗 Проверяем webhook...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                webhook_info = data.get("result", {})
                print(f"✅ Webhook информация получена")
                print(f"   URL: {webhook_info.get('url', 'N/A')}")
                print(f"   Ожидает обновления: {webhook_info.get('pending_update_count', 0)}")
                return True
            else:
                print(f"❌ Webhook API ошибка: {data}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка проверки webhook: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("🔍 Проверяем статус бота...")
    print("=" * 50)
    
    # Проверяем Telegram бота
    telegram_ok = test_telegram_bot()
    print()
    
    # Проверяем webhook
    webhook_ok = check_webhook()
    print()
    
    # Проверяем health endpoint
    health_ok = check_bot_health()
    print()
    
    # Итоговый результат
    print("=" * 50)
    print("📊 ИТОГОВЫЙ СТАТУС:")
    print(f"   Telegram бот: {'✅ Работает' if telegram_ok else '❌ Не работает'}")
    print(f"   Webhook: {'✅ Настроен' if webhook_ok else '❌ Не настроен'}")
    print(f"   Health endpoint: {'✅ Доступен' if health_ok else '❌ Недоступен'}")
    
    if not telegram_ok:
        print("\n❌ ПРОБЛЕМА: Telegram бот не отвечает")
        print("   Возможные причины:")
        print("   - Неправильный токен")
        print("   - Бот заблокирован")
        print("   - Проблемы с интернетом")
        
    if not health_ok:
        print("\n❌ ПРОБЛЕМА: Сервер не отвечает")
        print("   Возможные причины:")
        print("   - Сервис не запущен")
        print("   - Неправильный порт")
        print("   - Файрвол блокирует")
        
    if telegram_ok and not health_ok:
        print("\n💡 РЕШЕНИЕ: Нужно перезапустить сервис на сервере")

if __name__ == "__main__":
    main()
