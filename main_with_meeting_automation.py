# main.py with meeting automation
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

# Попытка импорта meeting_link_processor с обработкой ошибок GUI
try:
    from meeting_link_processor import meeting_link_processor
    MEETING_AUTOMATION_AVAILABLE = True
    print("✅ Meeting automation modules loaded successfully")
except ImportError as e:
    MEETING_AUTOMATION_AVAILABLE = False
    print(f"⚠️  Meeting automation not available: {e}")
except Exception as e:
    MEETING_AUTOMATION_AVAILABLE = False
    print(f"⚠️  Error loading meeting automation: {e}")

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

        # Проверка на поддерживаемые платформы
        supported_domains = [
            'zoom.us', 'meet.google.com', 'teams.microsoft.com',
            'talk.kontur.ru', 'ktalk.ru', 'telemost.yandex.ru',
            '2a14p7ld.ktalk.ru', 'us05web.zoom.us'
        ]

        return any(domain in parsed.netloc.lower() for domain in supported_domains)

    except Exception:
        return False


def process_message(msg: dict):
    """Обрабатывает одно сообщение от Telegram (для polling)."""
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    # Инициализация состояния для нового пользователя
    if chat_id not in user_states:
        user_states[chat_id] = {"state": "idle", "last_analysis": None}

    state = user_states[chat_id]["state"]

    # --- Обработка команд ---
    if text.lower() in ("/start", "start"):
        welcome_msg = "👋 Привет! Отправь мне ссылку на встречу!"
        if MEETING_AUTOMATION_AVAILABLE:
            welcome_msg += "\n🚀 Я автоматически присоединюсь, запишу и проанализирую встречу."
        else:
            welcome_msg += "\n📋 Я проанализирую ссылку на встречу."
        
        send_message(chat_id, welcome_msg)
        user_states[chat_id] = {"state": "idle", "last_analysis": None}
        return

    if text.lower() in ("/help", "help"):
        help_msg = "ℹ️ Просто отправь мне ссылку на встречу, и я:\n"
        if MEETING_AUTOMATION_AVAILABLE:
            help_msg += "• Автоматически присоединюсь\n• Запишу аудио\n• Сделаю транскрипцию\n• Проведу анализ\n• Обновлю лид в Bitrix"
        else:
            help_msg += "• Проанализирую ссылку\n• Определю платформу\n• Предоставлю информацию о встрече"
        
        help_msg += "\n\nПоддерживаемые платформы: Zoom, Google Meet, Microsoft Teams, Контур.Толк, Яндекс Телемост"
        send_message(chat_id, help_msg)
        return

    # --- Проверка на ссылку встречи (основной режим) ---
    if _is_meeting_url(text):
        if MEETING_AUTOMATION_AVAILABLE:
            # Полная автоматизация встречи
            send_message(chat_id, "🚀 Получил ссылку на встречу! Начинаю процесс автоматического присоединения...")
            
            # Запуск обработки встречи в отдельном потоке
            def process_meeting():
                try:
                    result = meeting_link_processor.process_meeting_link(
                        text, 
                        chat_id, 
                        msg.get("from", {}).get("first_name", "Пользователь")
                    )
                    if result['success']:
                        send_message(chat_id, result['message'])
                    else:
                        send_message(chat_id, result['message'])
                        user_states[chat_id] = {"state": "idle", "last_analysis": None}
                except Exception as e:
                    log.error(f"Ошибка при обработке встречи: {e}")
                    send_message(chat_id, f"❌ Ошибка при обработке встречи: {e}")
                    user_states[chat_id] = {"state": "idle", "last_analysis": None}
            
            # Запуск в отдельном потоке
            meeting_thread = threading.Thread(target=process_meeting, daemon=True)
            meeting_thread.start()
            
            # Изменение состояния на ожидание анализа
            user_states[chat_id] = {"state": "awaiting_meeting_analysis", "last_analysis": None}
        else:
            # Только анализ ссылки
            send_message(chat_id, "🚀 Получил ссылку на встречу! Анализирую...")
            
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
                elif 'ktalk.ru' in parsed.netloc or 'talk.kontur.ru' in parsed.netloc:
                    platform = "Контур.Толк"
                elif 'telemost.yandex.ru' in parsed.netloc:
                    platform = "Яндекс Телемост"
                
                analysis_msg = f"📋 Анализ ссылки:\n• Платформа: {platform}\n• URL: {text}\n\n"
                analysis_msg += "⚠️ Для автоматического присоединения к встречам нужно настроить виртуальный дисплей на сервере."
                
                send_message(chat_id, analysis_msg)
                
            except Exception as e:
                log.error(f"Ошибка при анализе ссылки: {e}")
                send_message(chat_id, f"❌ Ошибка при анализе ссылки: {e}")
        
        return

    # --- FSM логика для обработки статусов (только если доступна автоматизация) ---
    if MEETING_AUTOMATION_AVAILABLE:
        if state == "awaiting_meeting_analysis":
            # Проверка статуса встречи
            meeting_status = meeting_link_processor.get_meeting_status(chat_id)
            if meeting_status == "awaiting_lead_id":
                user_states[chat_id] = {"state": "awaiting_lead_id_after_meeting", "last_analysis": None}
                send_message(chat_id, "✅ Встреча завершена и проанализирована! Теперь введите ID лида для обновления:")
            elif meeting_status in ["joining", "in_meeting", "recording", "processing"]:
                send_message(chat_id, f"⏳ Встреча в процессе... Статус: {meeting_status}")
            elif meeting_status in ["failed", "error", "no_audio", "transcription_failed", "analysis_failed"]:
                send_message(chat_id, f"❌ Процесс встречи завершился с ошибкой. Статус: {meeting_status}")
                user_states[chat_id] = {"state": "idle", "last_analysis": None}
            else:
                send_message(chat_id, "⏳ Статус встречи неизвестен. Пожалуйста, подождите или попробуйте снова.")
        
        elif state == "awaiting_lead_id_after_meeting":
            # Обработка ID лида после автоматической встречи
            if text.isdigit():
                lead_id = text
                send_message(chat_id, f"🔗 Обновляю лид {lead_id} на основе анализа встречи...")
                
                try:
                    result = meeting_link_processor.update_lead_from_meeting(chat_id, lead_id)
                    if result['success']:
                        send_message(chat_id, result['message'])
                        log.info(f"Lead {lead_id} updated from meeting: {result}")
                    else:
                        send_message(chat_id, result['message'])
                        log.error(f"Error updating lead {lead_id} from meeting: {result}")
                except Exception as e:
                    send_message(chat_id, f"❌ Ошибка при обновлении лида {lead_id}: {e}")
                    log.error(f"Error updating lead {lead_id} from meeting: {e}")
                
                user_states[chat_id] = {"state": "idle", "last_analysis": None}
            else:
                send_message(chat_id, "❗ Введи корректный ID лида (только цифры).")

    # --- Обработка других сообщений ---
    if state == "idle":
        send_message(chat_id, "👋 Отправь мне ссылку на встречу!")


def polling_worker():
    """Фоновый процесс для polling."""
    offset = 0
    log.info("Запущен polling для получения сообщений...")
    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                updates = data.get("result", [])
                for update in updates:
                    if "message" in update:
                        process_message(update["message"])
                    offset = update["update_id"] + 1
        except requests.exceptions.RequestException as e:
            log.error(f"Ошибка сети в polling: {e}")
            time.sleep(5)
        except Exception as e:
            log.error(f"Критическая ошибка в polling: {e}")
            time.sleep(15)


# --- Маршруты ---
@app.route("/", methods=["GET"])
def index():
    """Проверка, что сервис работает"""
    status = "running"
    if MEETING_AUTOMATION_AVAILABLE:
        status += " with meeting automation"
    else:
        status += " with limited functionality"
    
    return {"ok": True, "message": f"Telegram bot is {status}"}, 200


# --- Точка входа ---
if __name__ == "__main__":
    init_db()
    log.info("База данных успешно инициализирована")
    
    if MEETING_AUTOMATION_AVAILABLE:
        log.info("✅ Бот запущен с полной автоматизацией встреч")
    else:
        log.info("⚠️ Бот запущен с ограниченной функциональностью (только анализ ссылок)")

    if USE_POLLING:
        # На всякий случай удалим вебхук, чтобы не мешал polling
        try:
            log.info("Удаление существующего вебхука...")
            requests.get(f"{BASE_URL}/deleteWebhook", timeout=5)
        except Exception as e:
            log.warning(f"Не удалось удалить вебхук (можно игнорировать): {e}")

        polling_thread = threading.Thread(target=polling_worker, daemon=True)
        polling_thread.start()
        log.info("Polling запущен в фоновом режиме.")

    # Запускаем веб-сервер для healthcheck и/или режима вебхуков
    app.run(host="0.0.0.0", port=PORT, use_reloader=False)
