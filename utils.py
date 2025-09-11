import os
import re
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
from functools import wraps
import hashlib

# Настройка логирования
log = logging.getLogger(__name__)


def validate_env_vars() -> Dict[str, Any]:
    """Комплексная проверка всех переменных окружения"""
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GEMINI_API_KEY',
        'RENDER_EXTERNAL_URL'
    ]

    optional_vars = [
        'BITRIX_WEBHOOK_URL',
        'ADMIN_CHAT_ID',
        'BITRIX_RESPONSIBLE_ID',
        'BITRIX_CREATED_BY_ID',
        'BITRIX_TASK_DEADLINE_DAYS',
        'LOG_LEVEL',
        'NODE_ENV',
        'GEMINI_MODEL',
        'DB_PATH',
        'MAX_RETRIES',
        'REQUEST_TIMEOUT',
        'MAX_COMMENT_LENGTH'
    ]

    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'required_vars': {},
        'optional_vars': {},
        'recommendations': []
    }

    # Проверка обязательных переменных
    for var in required_vars:
        value = os.getenv(var)
        validation_result['required_vars'][var] = bool(value)

        if not value:
            validation_result['valid'] = False
            validation_result['errors'].append(f"❌ Отсутствует обязательная переменная: {var}")

    # Проверка опциональных переменных
    for var in optional_vars:
        value = os.getenv(var)
        validation_result['optional_vars'][var] = bool(value)

        if not value:
            validation_result['warnings'].append(f"⚠️ Не установлена переменная: {var}")

    # Специфичные проверки и рекомендации
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token:
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35,}$', telegram_token):
            validation_result['errors'].append("❌ Неверный формат TELEGRAM_BOT_TOKEN")
        else:
            validation_result['recommendations'].append("✅ Токен Telegram корректен")

    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        if len(gemini_key) < 20:
            validation_result['warnings'].append("⚠️ GEMINI_API_KEY кажется слишком коротким")

    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        if not render_url.startswith('https://'):
            validation_result['errors'].append("❌ RENDER_EXTERNAL_URL должен начинаться с https://")
        else:
            validation_result['recommendations'].append("✅ URL Render корректен")

    bitrix_webhook = os.getenv('BITRIX_WEBHOOK_URL')
    if bitrix_webhook:
        if not bitrix_webhook.startswith('https://'):
            validation_result['errors'].append("❌ BITRIX_WEBHOOK_URL должен начинаться с https://")
        else:
            validation_result['recommendations'].append("✅ Bitrix webhook URL корректен")

    admin_chat_id = os.getenv('ADMIN_CHAT_ID')
    if admin_chat_id:
        try:
            int(admin_chat_id)
            validation_result['recommendations'].append("✅ ADMIN_CHAT_ID - корректное число")
        except ValueError:
            validation_result['warnings'].append("⚠️ ADMIN_CHAT_ID должен быть числом")

    # Проверка числовых переменных
    numeric_vars = {
        'BITRIX_RESPONSIBLE_ID': (1, 999999),
        'BITRIX_CREATED_BY_ID': (1, 999999),
        'BITRIX_TASK_DEADLINE_DAYS': (1, 30),
        'MAX_RETRIES': (1, 10),
        'REQUEST_TIMEOUT': (5, 120),
        'MAX_COMMENT_LENGTH': (100, 10000)
    }

    for var, (min_val, max_val) in numeric_vars.items():
        value = os.getenv(var)
        if value:
            try:
                num_val = int(value)
                if not (min_val <= num_val <= max_val):
                    validation_result['warnings'].append(
                        f"⚠️ {var}={num_val} вне рекомендуемого диапазона ({min_val}-{max_val})"
                    )
            except ValueError:
                validation_result['warnings'].append(f"⚠️ {var} должен быть числом")

    # Проверка NODE_ENV
    node_env = os.getenv('NODE_ENV', '').lower()
    if node_env and node_env not in ['development', 'production', 'test']:
        validation_result['warnings'].append("⚠️ NODE_ENV должен быть: development, production или test")

    # Проверка LOG_LEVEL
    log_level = os.getenv('LOG_LEVEL', '').upper()
    if log_level and log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        validation_result['warnings'].append("⚠️ LOG_LEVEL должен быть: DEBUG, INFO, WARNING, ERROR, CRITICAL")

    return validation_result


def sanitize_text(text: str, max_length: Optional[int] = None,
                  preserve_html: bool = True) -> str:
    """Очистка и санитизация текста для безопасного использования"""

    if not text:
        return ""

    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text.strip())

    # Санитизация HTML если не сохраняем
    if not preserve_html:
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    else:
        # Разрешаем только безопасные HTML теги для Telegram
        allowed_tags = ['b', 'i', 'u', 's', 'code', 'pre', 'a']
        pattern = r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]*>'
        text = re.sub(pattern, '', text)

    # Ограничиваем длину если нужно
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + '...'

    return text


def format_datetime(dt: datetime, format_type: str = 'default',
                    timezone: Optional[str] = None) -> str:
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'short': '%d.%m.%Y %H:%M',
        'date_only': '%d.%m.%Y',
        'time_only': '%H:%M:%S',
        'iso': '%Y-%m-%dT%H:%M:%S',
        'russian': '%d %B %Y года в %H:%M',
        'telegram': '%d.%m.%Y в %H:%M',
        'filename': '%Y%m%d_%H%M%S'
    }

    if timezone == 'MSK':
        dt = dt + timedelta(hours=3)
    elif timezone == 'UTC':
        pass

    return dt.strftime(formats.get(format_type, formats['default']))


def get_current_time(timezone: str = 'UTC') -> datetime:
    current = datetime.utcnow()

    if timezone.upper() == 'MSK':
        return current + timedelta(hours=3)
    elif timezone.upper() == 'EET':
        return current + timedelta(hours=2)
    elif timezone.upper() == 'UTC':
        return current
    else:
        return datetime.now()


def health_check() -> Dict[str, Any]:
    """Проверка ключевых сервисов — Gemini и Bitrix (если настроены)"""
    details = {}
    status = 'healthy'

    # Проверка Gemini
    from gemini_client import test_gemini_connection, get_gemini_info  # локальный импорт чтобы избежать циклов
    try:
        gemini_ok = test_gemini_connection()
        details['gemini'] = bool(gemini_ok)
        if not gemini_ok:
            status = 'degraded'
    except Exception as e:
        details['gemini'] = False
        status = 'degraded'
        log.exception("Ошибка при проверке Gemini: %s", e)

    # Проверка Bitrix (опционально)
    try:
        from bitrix import test_bitrix_connection
        bitrix_ok = test_bitrix_connection()
        details['bitrix'] = bool(bitrix_ok)
        if not bitrix_ok:
            status = 'degraded'
    except Exception:
        details['bitrix'] = False

    # Проверка интернет
    try:
        r = requests.get("https://api.telegram.org", timeout=5)
        details['internet_to_telegram'] = r.status_code < 400
        if not details['internet_to_telegram']:
            status = 'degraded'
    except Exception:
        details['internet_to_telegram'] = False
        status = 'degraded'

    return {'status': status, 'details': details, 'time': datetime.utcnow().isoformat()}


RESPONSE_TEMPLATES = {
    'help': "Используйте /analyze <текст транскрипта> для анализа или /update_lead <lead_id> <текст> для обновления лида."
}


def create_message(template_key: str, **kwargs) -> str:
    t = RESPONSE_TEMPLATES.get(template_key, '')
    return t.format(**kwargs)


def validate_lead_id(lead_id: str) -> bool:
    if not lead_id or not str(lead_id).strip():
        return False
    try:
        id_num = int(str(lead_id).strip())
        return 1 <= id_num <= 999999999
    except (ValueError, TypeError):
        return False
