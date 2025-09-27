#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def main():
    print("🔍 ДИАГНОСТИКА TELEGRAM БОТА")
    print("=" * 50)
    
    token = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
    
    # 1. Проверка бота
    print("1️⃣ Проверяем бота...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot = data["result"]
                print(f"   ✅ Бот активен: {bot['first_name']} (@{bot['username']})")
            else:
                print(f"   ❌ API ошибка: {data}")
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"   💥 Исключение: {e}")
    
    print()
    
    # 2. Проверка webhook
    print("2️⃣ Проверяем webhook...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                webhook = data["result"]
                print(f"   URL: {webhook.get('url', 'Не установлен')}")
                print(f"   Ожидает обновлений: {webhook.get('pending_update_count', 0)}")
                if webhook.get('last_error_message'):
                    print(f"   ❌ Последняя ошибка: {webhook['last_error_message']}")
            else:
                print(f"   ❌ Webhook API ошибка: {data}")
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"   💥 Исключение: {e}")
    
    print()
    
    # 3. Проверка обновлений
    print("3️⃣ Проверяем обновления...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                updates = data["result"]
                print(f"   Получено обновлений: {len(updates)}")
                if updates:
                    print("   Последние обновления:")
                    for update in updates[-3:]:  # Показываем последние 3
                        if "message" in update:
                            msg = update["message"]
                            print(f"     - От {msg['from']['first_name']}: {msg.get('text', 'Нет текста')}")
            else:
                print(f"   ❌ Updates API ошибка: {data}")
        else:
            print(f"   ❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"   💥 Исключение: {e}")
    
    print()
    
    # 4. Проверка сервера
    print("4️⃣ Проверяем сервер...")
    server_urls = [
        "http://109.172.47.253:3000/health",
        "http://109.172.47.253:8080/health",
        "http://109.172.47.253/health"
    ]
    
    for url in server_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Сервер отвечает: {url}")
                try:
                    data = response.json()
                    print(f"      Ответ: {data}")
                except:
                    print(f"      Ответ: {response.text[:100]}")
                break
        except Exception as e:
            print(f"   ❌ {url}: {e}")
    
    print()
    print("=" * 50)
    print("💡 РЕКОМЕНДАЦИИ:")
    print("1. Если бот не активен - проверьте токен")
    print("2. Если webhook не работает - настройте polling")
    print("3. Если сервер не отвечает - перезапустите сервис")
    print("4. Откройте test_bot.html в браузере для интерактивной проверки")

if __name__ == "__main__":
    main()
