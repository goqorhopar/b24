#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Устанавливаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
os.environ["GEMINI_API_KEY"] = "AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI"
os.environ["BITRIX_WEBHOOK_URL"] = "https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/"
os.environ["USE_POLLING"] = "true"
os.environ["PORT"] = "3000"
os.environ["LOG_LEVEL"] = "INFO"

# Импортируем и запускаем main
if __name__ == "__main__":
    try:
        from main import main
        print("🚀 Запускаем бота...")
        main()
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
