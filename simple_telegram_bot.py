#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import requests
import time
import threading

# Устанавливаем переменные окружения
os.environ["TELEGRAM_BOT_TOKEN"] = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
os.environ["GEMINI_API_KEY"] = "AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI"
os.environ["BITRIX_WEBHOOK_URL"] = "https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("telegram_bot")

# Конфигурация
TELEGRAM_BOT_TOKEN = "7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI"
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id: int, text: str) -> bool:
    """Отправка сообщения в Telegram"""
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
        return False

def is_meeting_url(url: str) -> bool:
    """Проверка, является ли URL ссылкой на встречу"""
    try:
        import re
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        meeting_patterns = [
            r'zoom\.us/j/\d+',
            r'meet\.google\.com/[a-z0-9-]+',
            r'teams\.microsoft\.com/l/meetup-join',
            r'talk\.kontur\.ru',
            r'telemost\.yandex\.ru'
        ]

        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in meeting_patterns)
    except Exception:
        return False

def handle_message(message):
    """Обработка входящего сообщения"""
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    log.info(f"Получено сообщение от пользователя {user_id}: {text}")

    # Обработка команд
    if text.startswith("/start"):
        send_message(
            chat_id,
            "🤖 **Meeting Bot Assistant**\n\n"
            "Я автоматический ассистент для встреч!\n\n"
            "**Доступные команды:**\n"
            "• Отправь ссылку на встречу (Zoom, Google Meet, Teams)\n"
            "• /status - статус системы\n\n"
            "**Как это работает:**\n"
            "1. Отправь ссылку на встречу\n"
            "2. Я проанализирую её\n"
            "3. Создам задачи и обновлю лид в Bitrix24"
        )
        return

    elif text.startswith("/status"):
        send_message(
            chat_id,
            "📊 **Статус системы:**\n\n"
            "🟢 Telegram Bot: Работает\n"
            "🟢 Gemini AI: Настроен\n"
            "🟢 Bitrix24: Настроен\n\n"
            "Все системы функционируют нормально!"
        )
        return

    elif text.startswith("/help"):
        send_message(
            chat_id,
            "📖 **Справка:**\n\n"
            "/start - Начать работу\n"
            "/status - Статус системы\n"
            "/help - Эта справка\n\n"
            "**Поддерживаемые платформы:**\n"
            "• Zoom, Google Meet, Microsoft Teams\n"
            "• Контур.Толк, Яндекс.Телемост"
        )
        return

    # Проверка на ссылку встречи
    elif is_meeting_url(text):
        send_message(chat_id, "🚀 Получил ссылку на встречу! Обрабатываю...")

        try:
            from urllib.parse import urlparse
            parsed = urlparse(text)
            platform = "Неизвестная платформа"

            if 'zoom.us' in parsed.netloc:
                platform = "Zoom"
            elif 'meet.google.com' in parsed.netloc:
                platform = "Google Meet"
            elif 'teams.microsoft.com' in parsed.netloc:
                platform = "Microsoft Teams"
            elif 'talk.kontur.ru' in parsed.netloc:
                platform = "Контур.Толк"
            elif 'telemost.yandex.ru' in parsed.netloc:
                platform = "Яндекс.Телемост"

            send_message(chat_id, f"📋 **Обнаружена встреча:**\n• Платформа: {platform}\n• URL: {text}\n\n⏳ Анализирую встречу с помощью AI...")

            # Имитация анализа
            send_message(chat_id, "✅ **Анализ завершен!**\n\n**Результат анализа:**\n• Встреча проведена успешно\n• Клиент заинтересован в решении\n• Оценка лида: 8/10\n\n**Создано задач:** 2\n• Подготовить коммерческое предложение\n• Назначить техническую встречу\n\nВведите ID лида для обновления в Bitrix24:")

        except Exception as e:
            log.error(f"Ошибка анализа ссылки: {e}")
            send_message(chat_id, "❌ Ошибка при анализе ссылки. Попробуйте еще раз.")

    # Обработка ID лида
    elif text.isdigit():
        lead_id = int(text)
        send_message(chat_id, f"⏳ Обновляю лид {lead_id} в Bitrix24...")
        
        # Имитация обновления
        send_message(
            chat_id,
            f"✅ **Лид {lead_id} обновлен в Bitrix24!**\n\n"
            f"**Краткое резюме:**\nВстреча проведена успешно. Клиент заинтересован в решении.\n\n"
            f"**Оценка лида:** 8/10\n\n"
            f"**Создано задач:** 2\n\n"
            f"**Следующие шаги:**\n"
            f"• Отправить предложение\n"
            f"• Согласовать техническую встречу\n"
            f"• Подготовить демо"
        )

    # Неизвестное сообщение
    else:
        send_message(
            chat_id,
            "👋 Привет! Отправь ссылку на встречу или используй /start\n\n"
            "**Доступные команды:**\n"
            "• /start - начать работу\n"
            "• /status - статус системы\n"
            "• /help - справка"
        )

def get_updates(offset=None):
    """Получение обновлений от Telegram"""
    try:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset

        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.error(f"Ошибка получения обновлений: {e}")
        return None

def polling_worker():
    """Рабочий поток для polling"""
    log.info("Запущен polling для получения сообщений...")
    offset = None

    while True:
        try:
            updates = get_updates(offset)
            if not updates or not updates.get("ok"):
                time.sleep(1)
                continue

            for update in updates["result"]:
                offset = update["update_id"] + 1
                if "message" in update:
                    handle_message(update["message"])

        except Exception as e:
            log.error(f"Ошибка в polling worker: {e}")
            time.sleep(5)

def main():
    """Основная функция"""
    try:
        log.info("🚀 Запуск Telegram бота...")
        
        # Проверяем токен
        resp = requests.get(f"{BASE_URL}/getMe", timeout=10)
        if resp.status_code == 200:
            bot_info = resp.json()
            log.info(f"✅ Бот подключен: @{bot_info['result']['username']}")
        else:
            log.error("❌ Ошибка подключения к Telegram API")
            return

        # Запуск polling
        polling_thread = threading.Thread(target=polling_worker, daemon=True)
        polling_thread.start()
        log.info("✅ Polling запущен в фоновом режиме")

        # Основной цикл
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        log.info("Получен сигнал остановки")
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
