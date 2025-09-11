import os
import logging
import requests
import time
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, Optional

# Импорты модулей проекта
from db import (
    init_db, set_session, get_session, clear_session,
    log_operation, get_stats, cleanup_old_sessions
)
from gemini_client import (
    analyze_transcript_structured, create_analysis_summary,
    get_gemini_info, test_gemini_connection
)
from bitrix import (
    update_lead_comprehensive, test_bitrix_connection,
    get_bitrix_info, BitrixError, get_lead_info
)
from utils import (
    sanitize_text, validate_env_vars, health_check,
    create_message, RESPONSE_TEMPLATES, validate_lead_id
)

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8') if os.getenv('NODE_ENV') != 'production' else logging.NullHandler()
    ]
)
log = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL')
PORT = int(os.getenv('PORT', 3000))
NODE_ENV = os.getenv('NODE_ENV', 'development')

# Проверка критических переменных
required_vars = {
    'TELEGRAM_BOT_TOKEN': TOKEN,
    'GEMINI_API_KEY': GEMINI_API_KEY,
    'RENDER_EXTERNAL_URL': RENDER_EXTERNAL_URL
}

missing_vars = [name for name, value in required_vars.items() if not value]
if missing_vars:
    raise RuntimeError(f"Отсутствуют критические переменные окружения: {missing_vars}")

# Telegram API настройки
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
WEBHOOK_URL = f"{RENDER_EXTERNAL_URL.rstrip('/')}/webhook"

# Инициализация Flask приложения
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Инициализация базы данных
try:
    init_db()
    log.info("База данных успешно инициализирована")
except Exception as e:
    log.critical(f"Критическая ошибка инициализации БД: {e}")
    raise

# Константы состояний
STATE_WAIT_TRANSCRIPT = "WAIT_TRANSCRIPT"
STATE_WAIT_LEAD_ID = "WAIT_LEAD_ID"
STATE_PROCESSING = "PROCESSING"

# Системные настройки
MAX_MESSAGE_LENGTH = 4096
PROCESSING_TIMEOUT = 300  # 5 минут
ADMIN_COMMANDS = ['/stats', '/health', '/cleanup', '/info']


def send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML",
                          disable_preview: bool = True) -> bool:
    """Отправка сообщения в Telegram с обработкой ошибок и разбивкой длинных сообщений"""
    try:
        if not text or not text.strip():
            log.warning(f"Попытка отправить пустое сообщение в чат {chat_id}")
            return False

        text = text.strip()

        # Разбиваем длинные сообщения
        if len(text) > MAX_MESSAGE_LENGTH:
            chunks = []
            while text:
                if len(text) <= MAX_MESSAGE_LENGTH:
                    chunks.append(text)
                    break

                cut_pos = text.rfind('\n', 0, MAX_MESSAGE_LENGTH)
                if cut_pos == -1:
                    cut_pos = MAX_MESSAGE_LENGTH - 3

                chunk = text[:cut_pos]
                if len(text) > cut_pos:
                    chunk += "..."
                chunks.append(chunk)
                text = "..." + text[cut_pos:].lstrip()

            # Отправляем части с задержкой
            for i, chunk in enumerate(chunks):
                success = send_telegram_message(chat_id, chunk, parse_mode, disable_preview)
                if not success:
                    return False
                if i < len(chunks) - 1:
                    time.sleep(0.5)  # Задержка между частями
            return True

        # Отправка одного сообщения
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview
        }

        response = requests.post(
            f"{TELEGRAM_API_URL}/sendMessage",
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        if not result.get('ok'):
            log.error(f"Telegram API вернул ошибку: {result}")
            return False

        log.debug(f"Сообщение отправлено в чат {chat_id}")
        return True

    except requests.exceptions.RequestException as e:
        log.error(f"Ошибка HTTP при отправке сообщения в чат {chat_id}: {e}")
        notify_admin(f"❌ Ошибка отправки сообщения в чат {chat_id}: {str(e)[:200]}")
        return False
    except Exception as e:
        log.error(f"Неожиданная ошибка отправки сообщения в чат {chat_id}: {e}")
        return False


def notify_admin(message: str, urgent: bool = False) -> None:
    """Уведомление администратора"""
    if not ADMIN_CHAT_ID:
        return

    try:
        prefix = "🚨 URGENT:" if urgent else "🔔 Admin:"
        admin_message = f"{prefix} {message}"

        send_telegram_message(int(ADMIN_CHAT_ID), admin_message)
        log.debug("Администратор уведомлен")
    except Exception as e:
        log.error(f"Ошибка уведомления администратора: {e}")


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Основной webhook для приёма сообщений от Telegram (настраивается как вебхук).
    Ожидаем минимально: {"message": {"chat": {"id": ...}, "text": "..."}}
    """
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "invalid json"}), 400

    # Поддержка разных форматов update
    message = payload.get('message') or payload.get('edited_message') or payload.get('callback_query', {}).get('message')
    if not message:
        return jsonify({"ok": True})

    chat = message.get('chat', {})
    chat_id = int(chat.get('id'))
    text = message.get('text', '') or message.get('caption', '')

    # Логируем входящее
    log.debug(f"Incoming message from {chat_id}: {text[:200]}")

    # Админ-команды
    if str(chat_id) == str(ADMIN_CHAT_ID) and text and text.startswith('/'):
        handled = handle_admin_command(chat_id, text.strip(), chat.get('username', 'admin'))
        if handled:
            return jsonify({"ok": True})

    # Обработка команд пользователя
    if text and text.strip().lower().startswith('/analyze'):
        # Ожидаем что далее присылают транскрипт или записывают команду отдельно
        args = text.split(' ', 1)
        if len(args) == 1:
            # Попросим прислать транскрипт
            set_session(chat_id, STATE_WAIT_TRANSCRIPT)
            send_telegram_message(chat_id, "Пришлите текст транскрипта встреч в следующем сообщении.")
            return jsonify({"ok": True})
        else:
            transcript = args[1].strip()
            return _process_transcript(chat_id, transcript)

    # Если в сессии ожидали транскрипт — обработаем
    sess = get_session(chat_id)
    if sess and sess.get('state') == STATE_WAIT_TRANSCRIPT:
        transcript = text.strip()
        # Переводим в обработку
        return _process_transcript(chat_id, transcript)

    # Команда для привязки lead id и запуска обновления
    if text and text.strip().lower().startswith('/update_lead'):
        parts = text.split()
        if len(parts) < 3:
            send_telegram_message(chat_id, "Использование: /update_lead <lead_id> <короткий текст транскрипта>")
            return jsonify({"ok": True})
        lead_id = parts[1].strip()
        transcript = " ".join(parts[2:]).strip()
        if not validate_lead_id(lead_id):
            send_telegram_message(chat_id, "Неверный lead_id")
            return jsonify({"ok": True})

        # Анализ
        send_telegram_message(chat_id, "Начинаю анализ и обновление лида...")
        data = analyze_transcript_structured(transcript)
        try:
            res = update_lead_comprehensive(lead_id, data)
            send_telegram_message(chat_id, "Лид обновлён: " + str(res.get('updated', False)))
        except BitrixError as be:
            send_telegram_message(chat_id, f"Ошибка Bitrix: {be}")
        except Exception as e:
            log.exception("Ошибка при update_lead:")
            send_telegram_message(chat_id, f"Ошибка при обновлении лида: {e}")
        return jsonify({"ok": True})

    # По умолчанию — подсказка
    send_telegram_message(chat_id, "Используйте /analyze <текст транскрипта> или /update_lead <id> <текст>")
    return jsonify({"ok": True})


def _process_transcript(chat_id: int, transcript: str):
    """Обработать присланный транскрипт: анализ + отправка результата"""
    start = time.time()
    set_session(chat_id, STATE_PROCESSING, transcript)
    send_telegram_message(chat_id, "🔎 Начинаю анализ транскрипта — это может занять несколько секунд...")

    try:
        structured = analyze_transcript_structured(transcript)
        summary = create_analysis_summary(structured)
        # Отправляем пользователю
        send_telegram_message(chat_id, summary)
        # Логируем операцию
        log_operation(chat_id, 'analyze', 'success', details=f"processed_fields={len([k for k,v in structured.items() if v is not None])}")
    except Exception as e:
        log.exception("Ошибка при обработке транскрипта")
        send_telegram_message(chat_id, f"❌ Ошибка при анализе: {e}")
        log_operation(chat_id, 'analyze', 'failure', details=str(e))
    finally:
        # Возвращаем сессию в нейтральное состояние
        clear_session(chat_id)
        duration = time.time() - start
        log.debug(f"Processing time for {chat_id}: {duration:.2f}s")

    return jsonify({"ok": True})


def handle_admin_command(chat_id: int, command: str, user_name: str) -> bool:
    """Обработка административных команд"""
    if str(chat_id) != str(ADMIN_CHAT_ID):
        return False

    try:
        if command == '/stats':
            stats = get_stats()
            gemini_info = get_gemini_info()
            bitrix_info = get_bitrix_info()

            stats_message = f"""📊 <b>Статистика системы</b>

🗄 <b>База данных:</b>
• Всего сессий: {stats.get('total_sessions', 0)}
• Активных сессий (24ч): {stats.get('active_sessions', 0)}
• Операций за 24ч: {stats.get('operations_24h', 0)}
• Успешных за 24ч: {stats.get('successful_ops_24h', 0)}
• Процент успеха: {stats.get('success_rate_24h', 0):.1f}%

🤖 <b>Gemini:</b>
• Подключение: {'✅' if gemini_info.get('connection_test') else '❌'}
• Модель: {gemini_info.get('model_name', 'неизвестно')}
• Максимум попыток: {gemini_info.get('max_retries', 0)}

🏢 <b>Bitrix24:</b>
• Настроен: {'✅' if bitrix_info.get('webhook_configured') else '❌'}
• Подключение: {'✅' if bitrix_info.get('connection_test') else '❌'}
• Доступных полей: {bitrix_info.get('available_fields', 0)}
• Пользовательских полей: {bitrix_info.get('custom_fields', 0)}

⚙️ <b>Система:</b>
• Окружение: {NODE_ENV}
• Порт: {PORT}
• Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            send_telegram_message(chat_id, stats_message)
            return True

        elif command == '/health':
            health_info = health_check()
            status_emoji = "✅" if health_info['status'] == 'healthy' else "❌"
            health_message = f"{status_emoji} <b>Проверка здоровья системы</b>\n\n"
            health_message += f"Статус: {health_info['status']}\n"
            health_message += f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            health_message += "Детали:\n"
            for service, status in health_info['details'].items():
                health_message += f"• {service}: {'✅' if status else '❌'}\n"

            if health_info['status'] != 'healthy':
                health_message += "\n⚠️ <i>Для детальной информации проверьте логи системы</i>"

            send_telegram_message(chat_id, health_message)
            return True

        elif command == '/cleanup':
            cleaned_count = cleanup_old_sessions()
            send_telegram_message(chat_id, f"🧹 Очищено {cleaned_count} устаревших сессий")
            return True

        elif command == '/info':
            gemini_info = get_gemini_info()
            bitrix_info = get_bitrix_info()

            info_message = f"""ℹ️ <b>Информация о системе</b>

🤖 <b>Gemini AI:</b>
• Модель: {gemini_info.get('model_name', 'неизвестно')}
• Подключение: {'✅' if gemini_info.get('connection_test') else '❌'}

🏢 <b>Bitrix24:</b>
• Webhook: {'✅' if bitrix_info.get('webhook_configured') else '❌'}
• Подключение: {'✅' if bitrix_info.get('connection_test') else '❌'}"""

            send_telegram_message(chat_id, info_message)
            return True

    except Exception as e:
        log.exception("Ошибка обработки админ команды")
        return False


@app.route('/healthz', methods=['GET'])
def healthz():
    """Простой эндпоинт здоровья"""
    info = health_check()
    status_code = 200 if info['status'] == 'healthy' else 503
    return jsonify(info), status_code


if __name__ == '__main__':
    # Для локального запуска
    app.run(host='0.0.0.0', port=PORT)
