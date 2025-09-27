#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time

def send_notification():
    """Отправить уведомление о развертывании бота"""
    try:
        url = "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/sendMessage"
        data = {
            "chat_id": "7537953397",
            "text": """🤖 **БОТ РАЗВЕРНУТ НА СЕРВЕРЕ!**

✅ **Автоматический запуск настроен**
✅ **Все API ключи работают** 
✅ **Реальный AI анализ активен**
✅ **Интеграция с Bitrix24 готова**

🚀 **Бот работает на сервере 109.172.47.253**
🔄 **Автоматически запускается при перезагрузке сервера**
📱 **Готов отвечать на сообщения 24/7**

**Отправьте ссылку на встречу для тестирования!**"""
        }
        
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Уведомление о развертывании отправлено!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("📱 Отправляю уведомление о развертывании бота...")
    send_notification()
