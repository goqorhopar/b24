#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests

def send_deployment_notification():
    """Отправить уведомление о развертывании бота"""
    try:
        url = "https://api.telegram.org/bot7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI/sendMessage"
        data = {
            "chat_id": "7537953397",
            "text": """🤖 **БОТ РАЗВЕРНУТ НА СЕРВЕРЕ!**

✅ **Работает на сервере 109.172.47.253**
✅ **Автоматический запуск при загрузке сервера**
✅ **Автоперезапуск при сбоях**
✅ **Реальный AI анализ с Gemini**
✅ **Интеграция с Bitrix24 готова**

🚀 **Бот работает 24/7 без вашего участия!**
📱 **Отправьте ссылку на встречу для тестирования!**

**Команды для управления:**
• systemctl status meeting-bot
• systemctl restart meeting-bot
• systemctl stop meeting-bot"""
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
    send_deployment_notification()
