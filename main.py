import os
import logging
import requests
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from db import init_db, set_session, get_session, clear_session, log_operation
from gemini_client import analyze_transcript_structured
from bitrix import update_lead_with_checklist, BitrixError
from utils import sanitize_text

load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')
PORT = int(os.getenv('PORT', 3000))

required_vars = {
    'TELEGRAM_BOT_TOKEN': TOKEN,
    'GEMINI_API_KEY': GEMINI_API_KEY,
    'RENDER_EXTERNAL_URL': RENDER_EXTERNAL_URL
}
for var_name, var_value in required_vars.items():
    if not var_value:
        raise RuntimeError(f"Переменная окружения {var_name} обязательна!")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook"

init_db()
app = Flask(__name__)

STATE_WAIT_TRANSCRIPT = "WAIT_TRANSCRIPT"
STATE_WAIT_LEAD_ID = "WAIT_LEAD_ID"

def send_message(chat_id, text, parse_mode="HTML"):
    try:
        max_length = 4096
        text = text or ""
        if len(text) > max_length:
            for i in range(0, len(text), max_length):
                chunk = text[i:i+max_length]
                response = requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode},
                    timeout=30
                )
                response.raise_for_status()
                time.sleep(0.1)
        else:
            response = requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=30
            )
            response.raise_for_status()
    except requests.exceptions.RequestException as e:
        log.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
        if ADMIN_CHAT_ID and str(chat_id) != str(ADMIN_CHAT_ID):
            try:
                requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={"chat_id": ADMIN_CHAT_ID, "text": f"❌ Ошибка отправки в чат {chat_id}: {str(e)[:500]}"},
                    timeout=15
                )
            except:
                pass

def notify_admin(message):
    if ADMIN_CHAT_ID:
        try:
            requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={"chat_id": ADMIN_CHAT_ID, "text": f"🔔 Admin: {message}"},
                timeout=15
            )
        except Exception as e:
            log.error(f"Ошибка уведомления админа: {e}")

def validate_lead_id(lead_id: str) -> bool:
    try:
        int(str(lead_id).strip())
        return True
    except:
        return False

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"ok": True})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        message = (data or {}).get('message')
        if not message:
            return jsonify({"ok": True})

        chat_id = message['chat']['id']
        text = (message.get('text') or '').strip()
        entities = message.get('entities') or []
        user_name = message.get('from', {}).get('username', 'Unknown')

        if not text:
            send_message(chat_id, "❌ Пустое сообщение. Отправьте текст.")
            return jsonify({"ok": True})

        # Commands
        if text.startswith('/start'):
            clear_session(chat_id)
            set_session(chat_id, STATE_WAIT_TRANSCRIPT, transcript=None)
            send_message(chat_id,
                "🤖 <b>Анализ встреч с Gemini</b>\n\n"
                "Отправьте мне транскрипт встречи (текст). После анализа я попрошу ID лида из Bitrix24 и обновлю его по чеклисту.\n\n"
                "<i>Команды:</i>\n/start — начать заново\n/cancel — отменить\n/help — помощь"
            )
            return jsonify({"ok": True})

        if text.startswith('/cancel'):
            clear_session(chat_id)
            send_message(chat_id, "✅ Операция отменена. Можете отправить новый транскрипт.")
            return jsonify({"ok": True})

        if text.startswith('/help'):
            send_message(chat_id,
                "<b>Как работать:</b>\n"
                "1) Пришлите транскрипт встречи\n"
                "2) Когда анализ будет готов — пришлите ID лида\n"
                "3) Я обновлю лид: добавлю анализ в COMMENTS и заполню поля чеклиста"
            )
            return jsonify({"ok": True})

        # State
        session = get_session(chat_id) or {}
        state = session.get('state')

        # Step 1: Получаем транскрипт
        if state in (None, "", STATE_WAIT_TRANSCRIPT):
            set_session(chat_id, STATE_WAIT_TRANSCRIPT, transcript=text)
            send_message(chat_id, "🔄 Анализирую транскрипт через Gemini, подождите...")
            log_operation(chat_id, "gemini_analyze", "started", None)

            try:
                analysis_text, gemini_data = analyze_transcript_structured(text)
                # Сохраняем в сессию оба объекта
                # Запишем JSON в operation_logs для прозрачности
                import json
                log_operation(chat_id, "gemini_analyze", "success", json.dumps(gemini_data)[:1000])

                # Покажем анализ
                analysis_text_sanitized = sanitize_text(analysis_text, max_length=4000)
                send_message(chat_id, f"✅ <b>Анализ готов</b>:\n\n{analysis_text_sanitized}")

                # Попросим ID лида
                set_session(chat_id, STATE_WAIT_LEAD_ID, transcript=text)
                # Временно сохраним gemini_data в оперативном кэше бэкенда через лог/хранилище:
                # проще всего — положить в отдельную таблицу. Для простоты — в operation_logs.
                log_operation(chat_id, "gemini_payload", "cached", json.dumps(gemini_data)[:3000])

                send_message(chat_id, "ℹ️ Теперь введите <b>ID лида</b> в Bitrix24 для обновления.")
                return jsonify({"ok": True})
            except Exception as e:
                log_operation(chat_id, "gemini_analyze", "error", str(e))
                send_message(chat_id, f"❌ Ошибка анализа: {e}")
                clear_session(chat_id)
                return jsonify({"ok": True})

        # Step 2: Ждём ID лида и обновляем Bitrix
        if state == STATE_WAIT_LEAD_ID:
            lead_id = text
            if not validate_lead_id(lead_id):
                send_message(chat_id, "❌ Неверный формат ID. Пришлите числовой ID лида.")
                return jsonify({"ok": True})

            # Достаём последний payload Gemini из operation_logs
            # Для простоты: перезапускаем анализ по сохранённому транскрипту (надёжно и просто)
            try:
                transcript = session.get('transcript') or ""
                if not transcript:
                    send_message(chat_id, "⚠️ Транскрипт не найден в сессии. Пришлите его ещё раз.")
                    clear_session(chat_id)
                    return jsonify({"ok": True})

                send_message(chat_id, "🔧 Обновляю лид в Bitrix24 по чеклисту...")

                analysis_text, gemini_data = analyze_transcript_structured(transcript)

                if not os.getenv('BITRIX_WEBHOOK_URL'):
                    send_message(chat_id, "⚠️ BITRIX_WEBHOOK_URL не настроен. Не могу обновить лид в Bitrix24.")
                    clear_session(chat_id)
                    return jsonify({"ok": True})

                result = update_lead_with_checklist(lead_id, gemini_data)
                if result.get('result') is True:
                    send_message(chat_id, f"✅ Лид {lead_id} успешно обновлён.")
                else:
                    send_message(chat_id, f"⚠️ Ответ Bitrix: {result}")

                clear_session(chat_id)
                return jsonify({"ok": True})

            except BitrixError as be:
                send_message(chat_id, f"❌ Ошибка Bitrix: {be}")
                clear_session(chat_id)
                return jsonify({"ok": True})
            except Exception as e:
                send_message(chat_id, f"❌ Ошибка обновления лида: {e}")
                clear_session(chat_id)
                return jsonify({"ok": True})

        # Fallback: если состояние неизвестно — начнём заново
        clear_session(chat_id)
        set_session(chat_id, STATE_WAIT_TRANSCRIPT, transcript=None)
        send_message(chat_id, "📝 Отправьте транскрипт встречи для анализа.")
        return jsonify({"ok": True})

    except Exception as e:
        log.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"ok": True})

if __name__ == "__main__":
    # Локальный запуск: можно настроить вебхук при необходимости
    app.run(host="0.0.0.0", port=PORT)
