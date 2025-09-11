# main.py
import os
import logging
import requests
from flask import Flask, request

from gemini_client import analyze_transcript_structured, create_analysis_summary
from bitrix import update_lead_comprehensive
from db import init_db

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("main")

# --- Flask app ---
app = Flask(__name__)

# --- Переменные окружения ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не найден в окружении!")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

PORT = int(os.getenv("PORT", "3000"))

# --- FSM состояния пользователей ---
# user_states = { chat_id: {"state": "idle"/"awaiting_lead_id", "last_analysis": dict} }
user_states = {}

# --- Вспомогательные функции ---
def send_message(chat_id: int, text: str) -> None:
    """Отправка сообщения в Telegram"""
    try:
        resp = requests.post(
            f"{BASE_URL}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=15
        )
        resp.raise_for_status()
    except Exception as e:
        log.error(f"Ошибка HTTP при отправке сообщения в чат {chat_id}: {e}")


def _download_telegram_file(file_id: str) -> bytes:
    """Скачивает файл из Telegram по file_id и возвращает байты."""
    try:
        # 1) Получаем путь к файлу
        resp = requests.get(
            f"{BASE_URL}/getFile",
            params={"file_id": file_id},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict) or not data.get("ok"):
            raise RuntimeError("getFile вернул некорректный ответ")
        file_path = data.get("result", {}).get("file_path")
        if not file_path:
            raise RuntimeError("file_path не найден в ответе getFile")

        # 2) Скачиваем сам файл
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
        f = requests.get(file_url, timeout=30)
        f.raise_for_status()
        return f.content
    except Exception as e:
        log.error(f"Не удалось скачать файл {file_id}: {e}")
        raise


# --- Маршруты ---
@app.route("/", methods=["GET"])
def index():
    """Проверка, что сервис работает"""
    return {"ok": True, "message": "Telegram bot is running"}, 200


@app.route("/webhook", methods=["POST"])
def webhook():
    """Основной обработчик Telegram вебхуков"""
    data = request.json
    if not data or "message" not in data:
        return {"ok": True}

    chat_id = data["message"]["chat"]["id"]
    msg = data["message"]
    text = msg.get("text", "").strip()

    # Инициализация состояния для нового пользователя
    if chat_id not in user_states:
        user_states[chat_id] = {"state": "idle", "last_analysis": None}

    state = user_states[chat_id]["state"]

    # --- Обработка команд ---
    if text.lower() in ("/start", "start"):
        send_message(chat_id, "👋 Привет! Отправь мне транскрипт встречи, и я проведу анализ.")
        user_states[chat_id] = {"state": "idle", "last_analysis": None}
        return {"ok": True}

    if text.lower() in ("/help", "help"):
        send_message(
            chat_id,
            "ℹ️ Инструкция:\n"
            "1. Отправь мне текст транскрипта встречи.\n"
            "2. Я проведу анализ и пришлю краткое резюме.\n"
            "3. Затем введи ID лида в Bitrix, чтобы обновить его."
        )
        return {"ok": True}

    # --- FSM логика ---
    if state == "awaiting_lead_id":
        if text.isdigit():
            lead_id = int(text)
            analysis = user_states[chat_id]["last_analysis"]
            send_message(chat_id, f"🔗 Обновляю лид {lead_id}...")

            try:
                result = update_lead_comprehensive(lead_id, analysis)
                msg = f"✅ Лид {lead_id} успешно обновлён в Bitrix"
                if isinstance(result, dict) and result.get('task_created'):
                    task_id = result.get('task_id') or '—'
                    msg += f"\n🗓 Создана задача, ID: {task_id}"
                send_message(chat_id, msg)
                log.info(f"Lead {lead_id} updated: {result}")
            except Exception as e:
                send_message(chat_id, f"❌ Ошибка обновления лида {lead_id}: {e}")
                log.error(f"Ошибка при обновлении лида {lead_id}: {e}")

            # Очистка состояния
            user_states[chat_id] = {"state": "idle", "last_analysis": None}
        else:
            send_message(chat_id, "❗ Введи корректный ID (только цифры).")

    elif state == "idle":
        # Если пользователь прислал ID лида цифрами даже в idle — используем последнее сохранённое
        if text.isdigit() and user_states.get(chat_id, {}).get("last_analysis"):
            lead_id = int(text)
            analysis = user_states[chat_id]["last_analysis"]
            send_message(chat_id, f"🔗 Обновляю лид {lead_id}...")
            try:
                result = update_lead_comprehensive(lead_id, analysis)
                msg = f"✅ Лид {lead_id} успешно обновлён в Bitrix"
                if isinstance(result, dict) and result.get('task_created'):
                    task_id = result.get('task_id') or '—'
                    msg += f"\n🗓 Создана задача, ID: {task_id}"
                send_message(chat_id, msg)
                log.info(f"Lead {lead_id} updated: {result}")
            except Exception as e:
                send_message(chat_id, f"❌ Ошибка обновления лида {lead_id}: {e}")
                log.error(f"Ошибка при обновлении лида {lead_id}: {e}")
            user_states[chat_id] = {"state": "idle", "last_analysis": None}
        elif not text:
            # Проверяем документ .txt
            doc = msg.get("document")
            if doc and isinstance(doc, dict):
                file_name = doc.get("file_name", "")
                if file_name.lower().endswith(".txt"):
                    send_message(chat_id, "📥 Получил файл, загружаю и анализирую...")
                    try:
                        file_id = doc.get("file_id")
                        raw = _download_telegram_file(file_id)
                        # Пытаемся определить кодировку и преобразовать в текст
                        text_data = None
                        for enc in ("utf-8", "utf-16", "cp1251", "latin-1"):
                            try:
                                text_data = raw.decode(enc)
                                break
                            except Exception:
                                continue
                        if not text_data:
                            raise RuntimeError("Не удалось декодировать файл")

                        send_message(chat_id, "🔎 Анализирую встречу из файла, подожди немного...")
                        analysis = analyze_transcript_structured(text_data)
                        summary = create_analysis_summary(analysis)

                        user_states[chat_id] = {
                            "state": "awaiting_lead_id",
                            "last_analysis": analysis
                        }

                        send_message(chat_id, summary)
                        send_message(chat_id, "Теперь введи ID лида, чтобы обновить его в Bitrix ⬇️")
                        return {"ok": True}
                    except Exception as e:
                        log.error(f"Ошибка обработки файла: {e}")
                        send_message(chat_id, f"❌ Не удалось обработать файл: {e}")
                        return {"ok": True}

            send_message(chat_id, "❗ Отправь текст для анализа или .txt файл с транскриптом 🚀")
        else:
            send_message(chat_id, "🔎 Анализирую встречу, подожди немного...")
            analysis = analyze_transcript_structured(text)
            summary = create_analysis_summary(analysis)

            user_states[chat_id] = {
                "state": "awaiting_lead_id",
                "last_analysis": analysis
            }

            send_message(chat_id, summary)
            send_message(chat_id, "Теперь введи ID лида, чтобы обновить его в Bitrix ⬇️")

    return {"ok": True}


# --- Точка входа ---
if __name__ == "__main__":
    init_db()
    log.info("База данных успешно инициализирована")
    app.run(host="0.0.0.0", port=PORT)
