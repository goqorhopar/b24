#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging

# Устанавливаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
os.environ["GEMINI_API_KEY"] = "AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI"
os.environ["BITRIX_WEBHOOK_URL"] = "https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/"
os.environ["USE_POLLING"] = "true"
os.environ["PORT"] = "3000"
os.environ["LOG_LEVEL"] = "INFO"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("telegram_bot")

# Импортируем и запускаем main
if __name__ == "__main__":
    try:
        log.info("🚀 Запуск Telegram бота...")
        from main import main
        main()
    except Exception as e:
        log.error(f"❌ Ошибка запуска: {e}")
        sys.exit(1)
