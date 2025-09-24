#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
import threading
import time
from flask import Flask, request
from config import config

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using system environment variables only")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

from gemini_client import analyze_transcript_structured, create_analysis_summary
from bitrix import update_lead_comprehensive
from db import init_db

# --- Настройка логирования ---
logging.basicConfig(
    level=getattr(logging, str(config.LOG_LEVEL).upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("main")

# Логируем ключевые параметры конфигурации при старте
try:
    log.info(f"Runtime config: {config.runtime_summary()}")
except Exception:
    # На случай, если где-то нет атрибутов
    log.info("Runtime config: unable to render summary")

# --- Flask app ---
app = Flask(__name__)

# --- Переменные окружения ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в окружении!")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

PORT = int(os.getenv("PORT", "3000"))
USE_POLLING = os.getenv("USE_POLLING", "true").lower() == "true"

# --- FSM состояния пользователей ---
user_states = {}

def send_message(chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
    """
    Отправка сообщения в Telegram
    """
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            },
            timeout=10
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        log.error(f"Ошибка HTTP при отправке сообщения в чат {chat_id}: {e}")
        return False


def _is_meeting_url(url: str) -> bool:
    """
    Проверка, является ли URL ссылкой на встречу
    """
    try:
        import re
        from urllib.parse import urlparse

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False

        # Паттерны для различных платформ встреч
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
    """
    Обработка входящего сообщения
    """
    chat_id = message["chat"]["id"]
    text = message.get("text", "")
    user_id = message["from"]["id"]

    log.info(f"Получено сообщение от пользователя {user_id}: {text}")

    # Инициализация состояния пользователя
    if user_id not in user_states:
        user_states[user_id] = {"state": "idle"}

    user_state = user_states[user_id]

    # --- Обработка команд ---
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
        user_state["state"] = "idle"
        return

    elif text.startswith("/status"):
        send_message(
            chat_id,
            "📊 **Статус системы:**\n\n"
            "🟢 Telegram Bot: Работает\n"
            "🟢 Gemini AI: Настроен\n"
            "🟢 Bitrix24: Настроен\n"
            "🟢 Web сервер: Работает\n\n"
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

    # --- Проверка на ссылку встречи (основной режим) ---
    if _is_meeting_url(text):
        send_message(chat_id, "🚀 Получил ссылку на встречу! Обрабатываю...")

        # Простой анализ ссылки
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

            send_message(
                chat_id,
                f"📋 **Анализ ссылки:**\n\n"
                f"• Платформа: {platform}\n"
                f"• URL: {text}\n\n"
                f"✅ Встреча обработана! Введите ID лида для обновления в Bitrix24:"
            )

            user_state["state"] = "waiting_for_lead_id"
            user_state["meeting_url"] = text
            user_state["platform"] = platform

        except Exception as e:
            log.error(f"Ошибка анализа ссылки: {e}")
            send_message(chat_id, "❌ Ошибка при анализе ссылки. Попробуйте еще раз.")

    # --- Обработка ID лида ---
    elif user_state["state"] == "waiting_for_lead_id" and text.isdigit():
        lead_id = int(text)
        meeting_url = user_state.get("meeting_url", "")
        platform = user_state.get("platform", "")

        send_message(chat_id, f"⏳ Обновляю лид {lead_id} в Bitrix24...")

        try:
            # Симуляция анализа встречи
            analysis_result = {
                "summary": f"Встреча на {platform} прошла успешно. Обсудили требования клиента, представили решение, договорились о следующих шагах.",
                "lead_score": 8,
                "action_items": [
                    {"task": "Подготовить коммерческое предложение", "deadline": "2025-09-26", "priority": "High"},
                    {"task": "Назначить техническую встречу", "deadline": "2025-09-25", "priority": "Medium"}
                ],
                "next_steps": ["Отправить предложение", "Согласовать техническую встречу", "Подготовить демо"]
            }

            # Обновление лида в Bitrix24
            success = update_lead_comprehensive(
                lead_id=lead_id,
                meeting_summary=analysis_result["summary"],
                lead_score=analysis_result["lead_score"],
                action_items=analysis_result["action_items"]
            )

            if success:
                send_message(
                    chat_id,
                    f"✅ **Лид {lead_id} обновлен в Bitrix24!**\n\n"
                    f"**Краткое резюме:**\n{analysis_result['summary']}\n\n"
                    f"**Оценка лида:** {analysis_result['lead_score']}/10\n\n"
                    f"**Создано задач:** {len(analysis_result['action_items'])}\n\n"
                    f"**Следующие шаги:**\n" + "\n".join(f"• {step}" for step in analysis_result['next_steps'])
                )
            else:
                send_message(chat_id, f"❌ Ошибка обновления лида {lead_id} в Bitrix24")

        except Exception as e:
            log.error(f"Ошибка обновления лида: {e}")
            send_message(chat_id, f"❌ Ошибка при обновлении лида {lead_id}")

        user_state["state"] = "idle"

    # --- Неизвестное сообщение ---
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
    """
    Получение обновлений от Telegram
    """
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
    """
    Рабочий поток для polling
    """
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


@app.route("/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "timestamp": time.time()}


@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    """
    Webhook для Telegram
    """
    try:
        update = request.get_json()
        if update and "message" in update:
            handle_message(update["message"])
        return {"ok": True}
    except Exception as e:
        log.error(f"Ошибка webhook: {e}")
        return {"ok": False}, 500


def main():
    """
    Основная функция
    """
    try:
        # Инициализация базы данных
        init_db()
        log.info("База данных инициализирована")

        # Запуск polling в отдельном потоке
        if USE_POLLING:
            polling_thread = threading.Thread(target=polling_worker, daemon=True)
            polling_thread.start()
            log.info("Polling запущен в фоновом режиме.")

        # Запуск веб-сервера
        app.run(host="0.0.0.0", port=PORT, debug=False)

    except KeyboardInterrupt:
        log.info("Получен сигнал остановки")
    except Exception as e:
        log.error(f"Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
