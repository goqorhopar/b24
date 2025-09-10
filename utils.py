import re
from typing import Optional

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    if not text:
        return ""
    # Telegram-safe sanitize (минимально)
    text = re.sub(r'\s+', ' ', text.strip())
    if max_length and len(text) > max_length:
        text = text[:max_length] + '...'
    return text

import os
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import requests
from functools import wraps

# Настройка логирования
log = logging.getLogger(__name__)

def validate_env_vars() -> Dict[str, Any]:
    """Проверка всех переменных окружения"""
    
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
        'DB_PATH'
    ]
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'required_vars': {},
        'optional_vars': {}
    }
    
    # Проверка обязательных переменных
    for var in required_vars:
        value = os.getenv(var)
        validation_result['required_vars'][var] = bool(value)
        
        if not value:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Отсутствует обязательная переменная: {var}")
    
    # Проверка опциональных переменных
    for var in optional_vars:
        value = os.getenv(var)
        validation_result['optional_vars'][var] = bool(value)
        
        if not value:
            validation_result['warnings'].append(f"Не установлена переменная: {var}")
    
    # Специфичные проверки
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token and not re.match(r'^\d+:[A-Za-z0-9_-]+$', telegram_token):
        validation_result['valid'] = False
        validation_result['errors'].append("Неверный формат TELEGRAM_BOT_TOKEN")
    
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key and not gemini_key.startswith('AIza'):
        validation_result['warnings'].append("Возможно неверный формат GEMINI_API_KEY")
    
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url and not render_url.startswith('https://'):
        validation_result['valid'] = False
        validation_result['errors'].append("RENDER_EXTERNAL_URL должен начинаться с https://")
    
    return validation_result

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для повторных попыток при ошибках"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    log.warning(f"Попытка {attempt + 1}/{max_retries} провалена для {func.__name__}: {e}")
                    
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log.error(f"Все попытки исчерпаны для {func.__name__}")
                        raise last_exception
            
            raise last_exception
        return wrapper
    return decorator

def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """Очистка и санитизация текста"""
    
    if not text:
        return ""
    
    # Убираем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Убираем потенциально опасные символы для HTML
    text = text.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
    
    # Ограничиваем длину если нужно
    if max_length and len(text) > max_length:
        text = text[:max_length] + '...'
    
    return text

def format_datetime(dt: datetime, format_type: str = 'default') -> str:
    """Форматирование даты и времени"""
    
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'short': '%d.%m.%Y %H:%M',
        'date_only': '%d.%m.%Y',
        'time_only': '%H:%M:%S',
        'iso': '%Y-%m-%dT%H:%M:%S',
        'russian': '%d %B %Y года в %H:%M'
    }
    
    return dt.strftime(formats.get(format_type, formats['default']))

def get_current_time(timezone: str = 'UTC') -> datetime:
    """Получение текущего времени с учётом временной зоны"""
    
    # Простая реализация, можно расширить с pytz
    if timezone == 'UTC':
        return datetime.utcnow()
    elif timezone == 'MSK':
        return datetime.utcnow() + timedelta(hours=3)
    else:
        return datetime.now()

def calculate_processing_time(start_time: float) -> str:
    """Расчёт времени обработки"""
    
    processing_time = time.time() - start_time
    
    if processing_time < 1:
        return f"{processing_time*1000:.0f}мс"
    elif processing_time < 60:
        return f"{processing_time:.1f}с"
    else:
        minutes = int(processing_time // 60)
        seconds = int(processing_time % 60)
        return f"{minutes}м {seconds}с"

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Обрезка текста с умным сохранением слов"""
    
    if len(text) <= max_length:
        return text
    
    # Пытаемся обрезать по словам
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.7:  # Если пробел не слишком далеко
        truncated = truncated[:last_space]
    
    return truncated + suffix

def extract_numbers(text: str) -> List[str]:
    """Извлечение чисел из текста"""
    return re.findall(r'\d+', text)

def validate_lead_id(lead_id: str) -> bool:
    """Валидация ID лида"""
    
    if not lead_id or not lead_id.strip():
        return False
    
    # Проверяем что это число
    try:
        int(lead_id.strip())
        return True
    except ValueError:
        return False

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла"""
    
    if size_bytes == 0:
        return "0 Б"
    
    size_names = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_system_info() -> Dict[str, Any]:
    """Получение информации о системе"""
    
    try:
        import psutil
        
        # Информация о памяти
        memory = psutil.virtual_memory()
        
        # Информация о диске
        disk = psutil.disk_usage('/')
        
        # Информация о CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            'memory': {
                'total': format_file_size(memory.total),
                'available': format_file_size(memory.available),
                'percent': memory.percent,
                'used': format_file_size(memory.used)
            },
            'disk': {
                'total': format_file_size(disk.total),
                'used': format_file_size(disk.used),
                'free': format_file_size(disk.free),
                'percent': (disk.used / disk.total) * 100
            },
            'cpu': {
                'percent': cpu_percent
            }
        }
    except ImportError:
        return {'error': 'psutil не установлен'}
    except Exception as e:
        return {'error': str(e)}

def check_internet_connection(url: str = "https://8.8.8.8", timeout: int = 5) -> bool:
    """Проверка интернет-соединения"""
    
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def generate_session_id() -> str:
    """Генерация уникального ID сессии"""
    
    import uuid
    return str(uuid.uuid4())[:8]

def mask_sensitive_data(data: str, mask_char: str = "*") -> str:
    """Маскировка чувствительных данных для логов"""
    
    if not data:
        return data
    
    if len(data) <= 4:
        return mask_char * len(data)
    
    visible_chars = 2
    masked_length = len(data) - (visible_chars * 2)
    
    return data[:visible_chars] + (mask_char * masked_length) + data[-visible_chars:]

def parse_telegram_entities(text: str, entities: List[Dict]) -> str:
    """Парсинг entity от Telegram (форматирование текста)"""
    
    if not entities:
        return text
    
    # Сортируем по offset для правильной обработки
    sorted_entities = sorted(entities, key=lambda x: x['offset'])
    
    result = ""
    last_offset = 0
    
    for entity in sorted_entities:
        # Добавляем текст до entity
        result += text[last_offset:entity['offset']]
        
        # Получаем текст entity
        entity_text = text[entity['offset']:entity['offset'] + entity['length']]
        
        # Форматируем в зависимости от типа
        if entity['type'] == 'bold':
            result += f"<b>{entity_text}</b>"
        elif entity['type'] == 'italic':
            result += f"<i>{entity_text}</i>"
        elif entity['type'] == 'code':
            result += f"<code>{entity_text}</code>"
        elif entity['type'] == 'pre':
            result += f"<pre>{entity_text}</pre>"
        elif entity['type'] == 'url':
            result += f'<a href="{entity_text}">{entity_text}</a>'
        else:
            result += entity_text
        
        last_offset = entity['offset'] + entity['length']
    
    # Добавляем оставшийся текст
    result += text[last_offset:]
    
    return result

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Создание текстового прогресс-бара"""
    
    if total == 0:
        return "█" * length
    
    progress = min(current / total, 1.0)
    filled_length = int(length * progress)
    
    bar = "█" * filled_length + "░" * (length - filled_length)
    percentage = progress * 100
    
    return f"{bar} {percentage:.1f}%"

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Безопасный парсинг JSON"""
    
    try:
        import json
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        log.warning(f"Не удалось распарсить JSON: {json_string[:100]}...")
        return default

def get_app_version() -> str:
    """Получение версии приложения"""
    
    try:
        with open('version.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"
    except Exception:
        return "error"

def health_check() -> Dict[str, Any]:
    """Проверка здоровья приложения"""
    
    checks = {
        'timestamp': get_current_time().isoformat(),
        'status': 'healthy',
        'checks': {}
    }
    
    # Проверка переменных окружения
    env_validation = validate_env_vars()
    checks['checks']['environment'] = {
        'status': 'ok' if env_validation['valid'] else 'error',
        'errors': env_validation['errors']
    }
    
    # Проверка базы данных
    try:
        from db import get_stats
        db_stats = get_stats()
        checks['checks']['database'] = {
            'status': 'ok',
            'stats': db_stats
        }
    except Exception as e:
        checks['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Проверка интернет-соединения
    checks['checks']['internet'] = {
        'status': 'ok' if check_internet_connection() else 'error'
    }
    
    # Общий статус
    if any(check.get('status') == 'error' for check in checks['checks'].values()):
        checks['status'] = 'unhealthy'
    
    return checks

# Константы для использования в приложении
TELEGRAM_LIMITS = {
    'message_length': 4096,
    'caption_length': 1024,
    'button_text_length': 64,
    'callback_data_length': 64
}

RESPONSE_TEMPLATES = {
    'error': "❌ <b>Ошибка:</b> {error}",
    'success': "✅ <b>Успех:</b> {message}",
    'warning': "⚠️ <b>Внимание:</b> {message}",
    'info': "ℹ️ <b>Информация:</b> {message}",
    'processing': "🔄 <b>Обработка...</b> {message}"
}

# Утилита для создания красивых сообщений
def create_message(template_type: str, **kwargs) -> str:
    """Создание форматированного сообщения"""
    
    template = RESPONSE_TEMPLATES.get(template_type, "{message}")
    return template.format(**kwargs)
