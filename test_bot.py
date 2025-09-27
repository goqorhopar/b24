#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import time

# Устанавливаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
os.environ["GEMINI_API_KEY"] = "AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI"
os.environ["BITRIX_WEBHOOK_URL"] = "https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/"
os.environ["ADMIN_CHAT_ID"] = "7537953397"
os.environ["PORT"] = "3000"
os.environ["USE_POLLING"] = "true"

print("✅ Переменные окружения установлены")

# Тестируем отправку сообщения
token = os.environ["TELEGRAM_BOT_TOKEN"]
chat_id = os.environ["ADMIN_CHAT_ID"]

url = f'https://api.telegram.org/bot{token}/sendMessage'
data = {
    'chat_id': chat_id,
    'text': '🤖 Бот запущен через Python скрипт!\n\n✅ Все переменные установлены\n✅ Готов к работе\n\nОтправьте ссылку на встречу!'
}

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Статус отправки: {response.status_code}")
    if response.status_code == 200:
        print("✅ Сообщение отправлено успешно!")
    else:
        print(f"❌ Ошибка: {response.text}")
except Exception as e:
    print(f"❌ Ошибка отправки: {e}")

print("\n🚀 Запускаем основной бот...")
print("Нажмите Ctrl+C для остановки")

# Импортируем и запускаем основной бот
try:
    from main import main
    main()
except KeyboardInterrupt:
    print("\n👋 Бот остановлен")
except Exception as e:
    print(f"❌ Ошибка запуска бота: {e}")
