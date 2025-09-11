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
                
                # Находим последний перенос строки в пределах лимита
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
            health_message = f"""{status_emoji}
