#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

# Устанавливаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
os.environ["GEMINI_API_KEY"] = "AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI"
os.environ["BITRIX_WEBHOOK_URL"] = "https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/"

print("🚀 Запуск автономного бота...")

try:
    # Запускаем бота
    subprocess.run([sys.executable, "autonomous_bot.py"], check=True)
except KeyboardInterrupt:
    print("🛑 Бот остановлен")
except Exception as e:
    print(f"❌ Ошибка: {e}")
