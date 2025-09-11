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
                
                # Находим последний перенос строкя в пределах лимита
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

def validate_lead_id(lead_id: str) -> bool:
    """Валидация ID лида"""
    try:
        id_num = int(str(lead_id).strip())
        return 1 <= id_num <= 999999999  # Разумные пределы
    except (ValueError, TypeError):
        return False

def format_analysis_message(analysis_text: str, structured_data: Dict[str, Any]) -> str:
    """Форматирование сообщения с анализом для отправки пользователю"""
    
    # Основной анализ
    message_parts = ["✅ <b>Анализ встречи завершен</b>\n"]
    
    # Краткое резюме
    is_lpr = structured_data.get('is_lpr', False)
    meeting_done = structured_data.get('meeting_done', False) 
    kp_done = structured_data.get('kp_done_text', '').lower() == 'да'
    
    message_parts.append("📊 <b>Ключевые индикаторы:</b>")
    message_parts.append(f"• ЛПР: {'✅ Найден' if is_lpr else '❌ Не найден'}")
    message_parts.append(f"• Встреча: {'✅ Проведена' if meeting_done else '❌ Не проведена'}")
    message_parts.append(f"• КП: {structured_data.get('kp_done_text', 'Не указано')}")
    
    # Дополнительная информация
    client_type = structured_data.get('client_type_text')
    if client_type:
        message_parts.append(f"• Тип клиента: <b>{client_type}</b>")
    
    budget = structured_data.get('ad_budget')
    if budget:
        message_parts.append(f"• Бюджет: <b>{budget}</b>")
    
    product = structured_data.get('product')
    if product and len(product) > 5:
        product_short = product[:80] + "..." if len(product) > 80 else product
        message_parts.append(f"• Продукт клиента: <i>{product_short}</i>")
    
    # WOW-эффект
    wow_effect = structured_data.get('wow_effect')
    if wow_effect and len(wow_effect) > 5:
        message_parts.append(f"\n💡 <b>WOW-эффект:</b>\n<i>{wow_effect[:200]}{'...' if len(wow_effect) > 200 else ''}</i>")
    
    # Анализ (укороченная версия)
    if analysis_text and len(analysis_text) > 50:
        analysis_short = analysis_text[:500] + "..." if len(analysis_text) > 500 else analysis_text
        message_parts.append(f"\n📝 <b>Детальный анализ:</b>\n{analysis_short}")
    
    message_parts.append(f"\n<i>Обработано полей: {len([k for k, v in structured_data.items() if v is not None])}</i>")
    
    return "\n".join(message_parts)

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
• Активных сессий: {stats.get('active_sessions', 0)}
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
• Время работы: {datetime.now().strftime('%H:%M:%S')}"""

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
• Доступность: {'✅ Доступен' if gemini_info.get('connection_test') else '❌ Недоступен'}
• Токенов в минуту: {gemini_info.get('tokens_per_minute', 'неизвестно')}

🏢 <b>Bitrix24:</b>
• Вебхук: {'✅ Настроен' if bitrix_info.get('webhook_configured') else '❌ Не настроен'}
• Подключение: {'✅ Работает' if bitrix_info.get('connection_test') else '❌ Ошибка'}
• Поля для обновления: {bitrix_info.get('available_fields', 0)}

📊 <b>Статистика:</b>
• Окружение: {NODE_ENV}
• Сервер: {RENDER_EXTERNAL_URL}
• Версия Python: {os.sys.version.split()[0]}"""

            send_telegram_message(chat_id, info_message)
            return True
            
    except Exception as e:
        log.error(f"Ошибка обработки административной команды {command}: {e}")
        send_telegram_message(chat_id, f"❌ Ошибка выполнения команды: {str(e)[:200]}")
        return False
    
    return False

def handle_start(chat_id: int, user_name: str) -> None:
    """Обработка команды /start"""
    welcome_message = f"""👋 Добро пожаловать, {user_name}!

🤖 <b>Я бот для анализа стенограмм встреч</b>

📝 <b>Как работать со мной:</b>
1. Отправьте команду /analyze
2. Пришлите стенограмму встречи
3. Укажите ID лида в Bitrix24
4. Я проанализирую текст и обновлю данные лида

⚡ <b>Основные команды:</b>
• /start - показать это сообщение
• /analyze - начать анализ новой встречи
• /cancel - отменить текущую операцию
• /help - справка по использованию

📊 Я могу определить:
• Проведена ли встреча
• Найден ли ЛПР
• Бюджет на рекламу
• Тип клиента
• WOW-эффект
• И многое другое"""

    send_telegram_message(chat_id, welcome_message)
    log_operation(chat_id, "start_command", {"user_name": user_name})

def handle_help(chat_id: int, user_name: str) -> None:
    """Обработка команды /help"""
    help_message = """📖 <b>Справка по использованию бота</b>

🔹 <b>Процесс анализа:</b>
1. Используйте /analyze для начала
2. Пришлите текст стенограммы встречи
3. Укажите ID лида из Bitrix24
4. Дождитесь обработки (1-2 минуты)

🔹 <b>Требования к тексту:</b>
• Минимум 100 символов
• Лучше всего - полная расшифровка
• Можно на русском или английском
• Поддерживается форматирование

🔹 <b>Доступные команды:</b>
• /start - начать работу
• /analyze - анализ встречи
• /cancel - отмена операции
• /status - статус системы
• /help - эта справка

🔹 <b>Поддерживаемые поля Bitrix24:</b>
• Статус встречи
• Комментарии менеджера
• Бюджет на рекламу
• Тип клиента
• Продукт клиента
• WOW-эффект
• И многие другие

💡 <b>Совет:</b> Чем детальнее стенограмма, тем точнее анализ!"""

    send_telegram_message(chat_id, help_message)
    log_operation(chat_id, "help_command", {"user_name": user_name})

def handle_analyze(chat_id: int, user_name: str) -> None:
    """Обработка команды /analyze"""
    try:
        # Проверяем доступность сервисов
        health = health_check()
        if not health['details'].get('gemini', False):
            send_telegram_message(chat_id, "❌ Сервис анализа временно недоступен. Попробуйте позже.")
            return
        
        # Устанавливаем состояние ожидания транскрипта
        set_session(chat_id, {
            'state': STATE_WAIT_TRANSCRIPT,
            'created_at': datetime.now().isoformat(),
            'user_name': user_name
        })
        
        analyze_message = """📝 <b>Режим анализа встречи</b>

Пожалуйста, пришлите текст стенограммы вашей встречи.

🔹 <b>Рекомендации:</b>
• Минимум 100 символов
• Полная расшифровка лучше фрагментов
• Можно включить несколько реплик
• Поддерживаются русский и английский

📋 <b>Что я ищу в тексте:</b>
• Была ли встреча проведена
• Найден ли ЛПР (лицо, принимающее решение)
• Бюджет на рекламу
• Тип бизнеса клиента
• Продукт/услуги клиента
• WOW-эффект от встречи
• Договоренности по КП

⏳ <b>Время обработки:</b> 1-2 минуты"""

        send_telegram_message(chat_id, analyze_message)
        log_operation(chat_id, "analyze_started", {"user_name": user_name})
        
    except Exception as e:
        log.error(f"Ошибка начала анализа для чата {chat_id}: {e}")
        send_telegram_message(chat_id, "❌ Ошибка при запуске анализа. Попробуйте позже.")
        notify_admin(f"Ошибка начала анализа для {user_name} ({chat_id}): {e}")

def handle_cancel(chat_id: int, user_name: str) -> None:
    """Обработка команды /cancel"""
    session = get_session(chat_id)
    if session and session.get('state') != 'IDLE':
        clear_session(chat_id)
        send_telegram_message(chat_id, "✅ Текущая операция отменена.")
        log_operation(chat_id, "operation_cancelled", {
            "user_name": user_name,
            "previous_state": session.get('state')
        })
    else:
        send_telegram_message(chat_id, "ℹ️ Нет активных операций для отмены.")

def process_transcript(chat_id: int, transcript_text: str, user_name: str) -> None:
    """Обработка полученной транскрипции"""
    try:
        # Валидация текста
        if len(transcript_text.strip()) < 100:
            send_telegram_message(chat_id, "❌ Текст слишком короткий. Нужно минимум 100 символов для анализа.")
            return
        
        # Обновляем состояние и сохраняем транскрипт
        set_session(chat_id, {
            'state': STATE_WAIT_LEAD_ID,
            'transcript': transcript_text[:10000],  # Ограничиваем размер
            'created_at': datetime.now().isoformat(),
            'user_name': user_name
        })
        
        send_telegram_message(chat_id, 
            "✅ Текст получен! Теперь пришлите ID лида из Bitrix24.\n\n"
            "🔹 ID лида можно найти в карточке лида в Bitrix24\n"
            "🔹 Обычно это число в адресной строке или в информации о лиде\n"
            "🔹 Пример: https://company.bitrix24.ru/crm/lead/details/12345/ - ID = 12345"
        )
        log_operation(chat_id, "transcript_received", {
            "text_length": len(transcript_text),
            "user_name": user_name
        })
        
    except Exception as e:
        log.error(f"Ошибка обработки транскрипта для чата {chat_id}: {e}")
        send_telegram_message(chat_id, "❌ Ошибка обработки текста. Попробуйте еще раз.")
        clear_session(chat_id)

def process_lead_id(chat_id: int, lead_id_input: str, user_name: str) -> None:
    """Обработка полученного ID лида"""
    try:
        # Валидация ID лида
        if not validate_lead_id(lead_id_input):
            send_telegram_message(chat_id, 
                "❌ Неверный формат ID лида. \n\n"
                "🔹 ID должен быть числом (например: 12345)\n"
                "🔹 Проверьте правильность ввода\n"
                "🔹 Попробуйте еще раз или используйте /cancel для отмены"
            )
            return
        
        lead_id = int(lead_id_input.strip())
        session = get_session(chat_id)
        
        if not session or 'transcript' not in session:
            send_telegram_message(chat_id, "❌ Сессия устарела. Начните заново с /analyze")
            clear_session(chat_id)
            return
        
        # Переходим в состояние обработки
        set_session(chat_id, {
            'state': STATE_PROCESSING,
            'transcript': session['transcript'],
            'lead_id': lead_id,
            'started_at': datetime.now().isoformat(),
            'user_name': user_name
        })
        
        # Запускаем обработку в фоновом режиме
        send_telegram_message(chat_id, 
            f"⏳ <b>Начинаю анализ...</b>\n\n"
            f"• Лид ID: {lead_id}\n"
            f"• Длина текста: {len(session['transcript'])} символов\n"
            f"• Ожидайте результат (1-3 минуты)"
        )
        
        # Запускаем асинхронную обработку
        import threading
        thread = threading.Thread(
            target=process_analysis,
            args=(chat_id, session['transcript'], lead_id, user_name)
        )
        thread.daemon = True
        thread.start()
        
        log_operation(chat_id, "analysis_started", {
            "lead_id": lead_id,
            "text_length": len(session['transcript']),
            "user_name": user_name
        })
        
    except Exception as e:
        log.error(f"Ошибка обработки ID лида для чата {chat_id}: {e}")
        send_telegram_message(chat_id, "❌ Ошибка обработки ID лида. Попробуйте еще раз.")
        clear_session(chat_id)

def process_analysis(chat_id: int, transcript: str, lead_id: int, user_name: str) -> None:
    """Фоновая обработка анализа"""
    try:
        log.info(f"Начало анализа для лида {lead_id}, чат {chat_id}")
        
        # Анализ транскрипта
        analysis_result = analyze_transcript_structured(transcript)
        
        if not analysis_result or 'error' in analysis_result:
            error_msg = analysis_result.get('error', 'Неизвестная ошибка анализа')
            send_telegram_message(chat_id, f"❌ Ошибка анализа: {error_msg}")
            log_operation(chat_id, "analysis_failed", {
                "lead_id": lead_id,
                "error": error_msg,
                "user_name": user_name
            })
            clear_session(chat_id)
            return
        
        # Обновление лида в Bitrix24
        update_result = update_lead_comprehensive(lead_id, analysis_result)
        
        if not update_result.get('success', False):
            error_msg = update_result.get('error', 'Неизвестная ошибка обновления')
            send_telegram_message(chat_id, f"❌ Ошибка обновления лида: {error_msg}")
            log_operation(chat_id, "update_failed", {
                "lead_id": lead_id,
                "error": error_msg,
                "analysis_data": analysis_result,
                "user_name": user_name
            })
            clear_session(chat_id)
            return
        
        # Создаем сводку анализа
        analysis_summary = create_analysis_summary(analysis_result)
        
        # Отправляем результат пользователю
        result_message = format_analysis_message(analysis_summary, analysis_result)
        send_telegram_message(chat_id, result_message)
        
        # Дополнительная информация
        send_telegram_message(chat_id,
            f"✅ <b>Лид успешно обновлен!</b>\n\n"
            f"🔗 <a href='{BITRIX_WEBHOOK_URL.replace('/rest/', '/crm/lead/details/')}{lead_id}/'>Открыть лид в Bitrix24</a>\n\n"
            f"📊 Обновлено полей: {update_result.get('updated_fields', 0)}\n"
            f"⏱ Время обработки: {update_result.get('processing_time', 0):.1f}с"
        )
        
        log_operation(chat_id, "analysis_completed", {
            "lead_id": lead_id,
            "updated_fields": update_result.get('updated_fields', 0),
            "processing_time": update_result.get('processing_time', 0),
            "user_name": user_name,
            "analysis_data": {k: v for k, v in analysis_result.items() if v is not None}
        })
        
        # Уведомление администратора об успешном анализе
        notify_admin(f"✅ Успешный анализ для {user_name} (Лид {lead_id}, полей: {update_result.get('updated_fields', 0)})")
        
    except Exception as e:
        log.error(f"Критическая ошибка обработки анализа для чата {chat_id}: {e}")
        send_telegram_message(chat_id, "❌ Критическая ошибка при обработке. Администратор уведомлен.")
        notify_admin(f"🚨 Критическая ошибка анализа для {user_name} (чат {chat_id}, лид {lead_id}): {e}", urgent=True)
        log_operation(chat_id, "analysis_critical_error", {
            "lead_id": lead_id,
            "error": str(e),
            "user_name": user_name
        })
    finally:
        clear_session(chat_id)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработка входящих webhook-запросов от Telegram"""
    try:
        data = request.get_json()
        if not data:
            log.warning("Пустой webhook запрос")
            return jsonify({"status": "error", "message": "Empty request"}), 400
        
        log.debug(f"Received webhook: {json.dumps(data, ensure_ascii=False)[:500]}")
        
        # Обработка сообщения
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user_name = message['from'].get('first_name', 'Unknown')
            text = message.get('text', '').strip()
            
            # Логирование входящего сообщения
            log_operation(chat_id, "message_received", {
                "text": text[:200],
                "user_name": user_name,
                "message_id": message.get('message_id')
            })
            
            # Проверка команд администратора
            if text in ADMIN_COMMANDS:
                if handle_admin_command(chat_id, text, user_name):
                    return jsonify({"status": "ok"})
            
            # Получение текущей сессии
            session = get_session(chat_id)
            current_state = session.get('state', 'IDLE') if session else 'IDLE'
            
            # Обработка команд
            if text == '/start':
                handle_start(chat_id, user_name)
                
            elif text == '/help':
                handle_help(chat_id, user_name)
                
            elif text == '/analyze':
                handle_analyze(chat_id, user_name)
                
            elif text == '/cancel':
                handle_cancel(chat_id, user_name)
                
            elif text == '/status':
                health_info = health_check()
                status_msg = "✅ Система работает нормально" if health_info['status'] == 'healthy' else "⚠️ Есть проблемы с системой"
                send_telegram_message(chat_id, f"{status_msg}\nИспользуйте /health для детальной информации")
                
            # Обработка состояний
            elif current_state == STATE_WAIT_TRANSCRIPT:
                process_transcript(chat_id, text, user_name)
                
            elif current_state == STATE_WAIT_LEAD_ID:
                process_lead_id(chat_id, text, user_name)
                
            elif current_state == STATE_PROCESSING:
                send_telegram_message(chat_id, "⏳ Идет обработка предыдущего запроса. Подождите завершения.")
                
            else:
                # Стандартный ответ на неизвестные сообщения
                send_telegram_message(chat_id,
                    "🤖 <b>Не понимаю команду</b>\n\n"
                    "Используйте /analyze для начала анализа встречи\n"
                    "или /help для получения справки по командам"
                )
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        log.error(f"Ошибка обработки webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_endpoint():
    """Endpoint для проверки здоровья сервиса"""
    try:
        health_info = health_check()
        return jsonify(health_info), 200 if health_info['status'] == 'healthy' else 503
    except Exception as e:
        log.error(f"Ошибка health check: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/setup-webhook', methods=['POST'])
def setup_webhook():
    """Установка webhook для Telegram"""
    try:
        payload = {
            "url": WEBHOOK_URL,
            "drop_pending_updates": True
        }
        
        response = requests.post(
            f"{TELEGRAM_API_URL}/setWebhook",
            json=payload,
            timeout=10
        )
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
        raise
