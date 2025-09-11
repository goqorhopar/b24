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
    create_message, RESPONSE_TEMPLATES
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
                # Находим ближайший разделитель
                split_point = text.rfind('\n\n', 0, MAX_MESSAGE_LENGTH)
                if split_point == -1:
                    split_point = text.rfind('\n', 0, MAX_MESSAGE_LENGTH)
                if split_point == -1:
                    split_point = MAX_MESSAGE_LENGTH
                chunks.append(text[:split_point])
                text = text[split_point:].strip()

            for chunk in chunks:
                response = requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={
                        'chat_id': chat_id,
                        'text': chunk,
                        'parse_mode': parse_mode,
                        'disable_web_page_preview': disable_preview
                    }
                )
                response.raise_for_status()
                time.sleep(1) # Задержка для обхода лимитов
            return True

        else:
            response = requests.post(
                f"{TELEGRAM_API_URL}/sendMessage",
                json={
                    'chat_id': chat_id,
                    'text': text,
                    'parse_mode': parse_mode,
                    'disable_web_page_preview': disable_preview
                }
            )
            response.raise_for_status()
            return True
            
    except requests.exceptions.RequestException as e:
        log.error(f"Ошибка при отправке сообщения в чат {chat_id}: {e}")
        return False
    except Exception as e:
        log.error(f"Неизвестная ошибка при отправке сообщения: {e}")
        return False

def handle_start_command(chat_id: int) -> None:
    """Обработка команды /start"""
    send_telegram_message(chat_id, RESPONSE_TEMPLATES['START_MSG'])
    set_session(chat_id, STATE_WAIT_TRANSCRIPT)
    log_operation(chat_id, 'start', 'success')

def handle_help_command(chat_id: int) -> None:
    """Обработка команды /help"""
    send_telegram_message(chat_id, RESPONSE_TEMPLATES['HELP_MSG'])
    log_operation(chat_id, 'help', 'success')

def handle_analyze_command(chat_id: int, transcript: str) -> None:
    """Обработка команды /analyze"""
    if not transcript or len(transcript.strip()) < 50:
        send_telegram_message(chat_id, RESPONSE_TEMPLATES['TRANSCRIPT_TOO_SHORT'])
        log_operation(chat_id, 'analyze', 'error', 'Короткий транскрипт')
        return

    # Устанавливаем статус "в обработке"
    set_session(chat_id, STATE_PROCESSING, transcript)
    log_operation(chat_id, 'analyze', 'pending', f"Запуск анализа для чата {chat_id}")
    send_telegram_message(chat_id, RESPONSE_TEMPLATES['ANALYSIS_STARTED'])

    try:
        # 1. Анализ транскрипта с помощью Gemini
        log.info(f"Начинаю анализ транскрипта для чата {chat_id}")
        structured_data = analyze_transcript_structured(transcript)
        log.info(f"Анализ завершен. Получено структурированных данных: {len(structured_data)}")
        
        # 2. Формирование отчета
        analysis_summary = create_analysis_summary(structured_data)
        full_analysis_text = f"<b>Отчет об анализе звонка:</b>\n\n{analysis_summary}"
        
        # 3. Отправка отчета в Telegram
        send_telegram_message(chat_id, full_analysis_text)
        log.info(f"Отчет успешно отправлен в чат {chat_id}")

        # 4. Обновление лида в Bitrix24
        lead_id = structured_data.get('lead_id')
        if lead_id:
            try:
                log.info(f"Попытка обновления лида {lead_id} в Bitrix24")
                update_lead_comprehensive(lead_id, structured_data)
                send_telegram_message(chat_id, RESPONSE_TEMPLATES['BITRIX_UPDATE_SUCCESS'])
                log.info(f"Лид {lead_id} успешно обновлен")
                log_operation(chat_id, 'bitrix_update', 'success', f"Лид {lead_id} обновлен")
            except BitrixError as e:
                error_msg = f"Ошибка Bitrix: {e}"
                send_telegram_message(chat_id, f"❌ Ошибка Bitrix24: {e}")
                log.error(error_msg)
                log_operation(chat_id, 'bitrix_update', 'error', error_msg)
        else:
            log.warning("ID лида не найден в анализе Gemini. Пропускаю обновление Bitrix.")
            send_telegram_message(chat_id, RESPONSE_TEMPLATES['NO_LEAD_ID'])
            log_operation(chat_id, 'bitrix_update', 'skip', 'ID лида не найден')

        # Завершение сессии
        clear_session(chat_id)
        log_operation(chat_id, 'analyze', 'success', 'Анализ завершен успешно')
    
    except Exception as e:
        error_msg = f"Непредвиденная ошибка при анализе: {e}"
        log.error(error_msg, exc_info=True)
        send_telegram_message(chat_id, RESPONSE_TEMPLATES['ANALYSIS_FAILED'])
        # Исправлено: теперь details всегда строка
        log_operation(chat_id, 'analyze', 'error', details=str(e))
        clear_session(chat_id)

def handle_message(update: Dict[str, Any]) -> None:
    """Основной обработчик входящих сообщений"""
    message = update.get('message', {})
    chat_id = message.get('chat', {}).get('id')
    user_id = message.get('from', {}).get('id')
    text = message.get('text', '')

    if not chat_id or not text:
        return

    log.info(f"Получено сообщение от чата {chat_id} (пользователь {user_id}): {text[:50]}...")
    
    # Обработка команд
    if text.startswith('/'):
        command = text.split(None, 1)[0]
        # Обработка команды /analyze
        if command == '/analyze':
            transcript = text.replace('/analyze', '', 1).strip()
            handle_analyze_command(chat_id, transcript)
            return

        # Обработка других команд
        if command == '/start':
            handle_start_command(chat_id)
        elif command == '/help':
            handle_help_command(chat_id)
        elif command in ADMIN_COMMANDS:
            handle_admin_command(chat_id, text)
        else:
            send_telegram_message(chat_id, RESPONSE_TEMPLATES['UNKNOWN_COMMAND'])
            log_operation(chat_id, 'command', 'error', 'Неизвестная команда')
    else:
        # Обработка текста без команды
        session = get_session(chat_id)
        if session and session['state'] == STATE_WAIT_TRANSCRIPT:
            handle_analyze_command(chat_id, text)
        else:
            send_telegram_message(chat_id, RESPONSE_TEMPLATES['GENERIC_RESPONSE'])
            log_operation(chat_id, 'generic_response', 'info', 'Ответ по умолчанию')

def handle_admin_command(chat_id: int, command: str) -> None:
    """Обработка команд администратора"""
    if str(chat_id) != ADMIN_CHAT_ID:
        send_telegram_message(chat_id, RESPONSE_TEMPLATES['ACCESS_DENIED'])
        log_operation(chat_id, 'admin_command', 'error', 'Доступ запрещен')
        return

    log.info(f"Администратор {chat_id} выполняет команду: {command}")
    
    if command == '/stats':
        try:
            stats = get_stats()
            response_text = "<b>Статистика бота:</b>\n"
            response_text += f"• Всего сессий: {stats.get('total_sessions')}\n"
            response_text += f"• Активные сессии: {stats.get('active_sessions')}\n"
            response_text += f"• Всего операций: {stats.get('total_operations')}\n"
            response_text += f"• Успешных операций: {stats.get('successful_operations')}\n"
            response_text += f"• Последние 24 часа: {stats.get('operations_last_24h')}\n"
            send_telegram_message(chat_id, response_text)
            log_operation(chat_id, 'admin_stats', 'success', 'Статистика отправлена')
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Ошибка получения статистики: {e}")
            log_operation(chat_id, 'admin_stats', 'error', str(e))

    elif command == '/health':
        try:
            health_status = health_check()
            response_text = "<b>Проверка здоровья системы:</b>\n"
            for service, status in health_status['services'].items():
                response_text += f"• {service}: {'✅' if status['ok'] else '❌'}\n"
            if health_status.get('bitrix_info'):
                 response_text += f"• Bitrix: ✅ (Версия: {health_status['bitrix_info'].get('version')})\n"
            send_telegram_message(chat_id, response_text)
            log_operation(chat_id, 'admin_health', 'success', 'Статус здоровья отправлен')
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Ошибка проверки здоровья: {e}")
            log_operation(chat_id, 'admin_health', 'error', str(e))

    elif command == '/cleanup':
        try:
            deleted_sessions, deleted_logs = cleanup_old_sessions()
            response_text = f"✅ Очистка завершена: удалено {deleted_sessions} старых сессий и {deleted_logs} логов."
            send_telegram_message(chat_id, response_text)
            log_operation(chat_id, 'admin_cleanup', 'success', 'Очистка завершена')
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Ошибка при очистке: {e}")
            log_operation(chat_id, 'admin_cleanup', 'error', str(e))

    elif command == '/info':
        try:
            gemini_info = get_gemini_info()
            bitrix_info = get_bitrix_info()
            
            info_text = "<b>Информация о боте:</b>\n"
            info_text += f"• Версия: 2.0.0\n"
            info_text += f"• Окружение: {NODE_ENV}\n"
            info_text += f"• Gemini модель: {gemini_info.get('model_name')}\n"
            info_text += f"• Bitrix ID ответственного: {bitrix_info.get('responsible_id')}\n"
            info_text += f"• Bitrix URL: {bitrix_info.get('webhook_url')[:30]}...\n"
            send_telegram_message(chat_id, info_text)
            log_operation(chat_id, 'admin_info', 'success', 'Информация отправлена')
        except Exception as e:
            send_telegram_message(chat_id, f"❌ Ошибка получения информации: {e}")
            log_operation(chat_id, 'admin_info', 'error', str(e))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка входящих вебхуков Telegram"""
    update = request.get_json()
    if update:
        log.info(f"Получен вебхук: {update.get('update_id')}")
        handle_message(update)
    return jsonify({'status': 'ok'})

@app.route('/set_webhook', methods=['GET'])
def setup_webhook():
    """Установка вебхука для Telegram"""
    try:
        url = f"{TELEGRAM_API_URL}/setWebhook?url={WEBHOOK_URL}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get('ok'):
            log.info(f"Webhook установлен: {WEBHOOK_URL}")
            return jsonify({"status": "success", "result": result})
        else:
            log.error(f"Ошибка установки webhook: {result}")
            return jsonify({"status": "error", "result": result}), 500
            
    except Exception as e:
        log.error(f"Ошибка установки webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    """Корневой endpoint"""
    return jsonify({
        "status": "running",
        "service": "Telegram Meeting Analysis Bot",
        "version": "1.0.0",
        "environment": NODE_ENV,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Проверка соединений при запуске
    try:
        log.info("Запуск приложения...")
        
        # Проверка здоровья сервисов
        health = health_check()
        log.info(f"Статус здоровья: {health['status']}")
        
        # Установка webhook в production
        if NODE_ENV == 'production':
            setup_webhook()
            log.info("Production mode: Webhook configured")
        else:
            log.info("Development mode: Polling can be used")
        
        # Запуск Flask приложения
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=(NODE_ENV == 'development'),
            use_reloader=False
        )
        
    except Exception as e:
        log.critical(f"Критическая ошибка запуска приложения: {e}")
        # Отправка уведомления администратору
        if ADMIN_CHAT_ID:
            try:
                requests.post(
                    f"{TELEGRAM_API_URL}/sendMessage",
                    json={'chat_id': ADMIN_CHAT_ID, 'text': f"❌ Критическая ошибка при запуске бота: {e}"}
                )
            except Exception as notify_e:
                log.error(f"Не удалось отправить уведомление админу: {notify_e}")
        os._exit(1)
