import os
import re
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union, Tuple
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
        if not re.match(r'^\d+:[A-Za-z0-9_-]{35}$', telegram_token):
            validation_result['errors'].append("❌ Неверный формат TELEGRAM_BOT_TOKEN")
        else:
            validation_result['recommendations'].append("✅ Токен Telegram корректен")

    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        if not gemini_key.startswith('AIza'):
            validation_result['warnings'].append("⚠️ Возможно неверный формат GEMINI_API_KEY")
        if len(gemini_key) < 30:
            validation_result['warnings'].append("⚠️ GEMINI_API_KEY кажется слишком коротким")

    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        if not render_url.startswith('https://'):
            validation_result['errors'].append("❌ RENDER_EXTERNAL_URL должен начинаться с https://")
        elif not re.match(r'^https://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', render_url):
            validation_result['warnings'].append("⚠️ RENDER_EXTERNAL_URL имеет необычный формат")
        else:
            validation_result['recommendations'].append("✅ URL Render корректен")

    bitrix_webhook = os.getenv('BITRIX_WEBHOOK_URL')
    if bitrix_webhook:
        if not bitrix_webhook.startswith('https://'):
            validation_result['errors'].append("❌ BITRIX_WEBHOOK_URL должен начинаться с https://")
        elif 'bitrix24' not in bitrix_webhook.lower():
            validation_result['warnings'].append("⚠️ BITRIX_WEBHOOK_URL не содержит 'bitrix24'")
        elif '/rest/' not in bitrix_webhook:
            validation_result['warnings'].append("⚠️ BITRIX_WEBHOOK_URL не содержит '/rest/'")
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


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0,
                    exceptions: tuple = (Exception,)):
    """Декоратор для повторных попыток при ошибках с экспоненциальной задержкой"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    log.warning(f"Попытка {attempt + 1}/{max_retries} провалена для {func.__name__}: {e}")

                    if attempt < max_retries - 1:
                        log.debug(f"Ожидание {current_delay:.1f}с перед повтором...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        log.error(f"Все попытки исчерпаны для {func.__name__}")
                        raise last_exception

            raise last_exception

        return wrapper

    return decorator


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
        # Удаляем все теги кроме разрешенных
        pattern = r'<(?!/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]*>'
        text = re.sub(pattern, '', text)

    # Ограничиваем длину если нужно
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + '...'

    return text


def format_datetime(dt: datetime, format_type: str = 'default',
                    timezone: Optional[str] = None) -> str:
    """Форматирование даты и времени с поддержкой различных форматов"""
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

    # Простое смещение времени (расширить при необходимости)
    if timezone == 'MSK':
        dt = dt + timedelta(hours=3)
    elif timezone == 'UTC':
        pass  # UTC по умолчанию

    return dt.strftime(formats.get(format_type, formats['default']))


def get_current_time(timezone: str = 'UTC') -> datetime:
    """Получение текущего времени с учётом временной зоны"""
    current = datetime.utcnow()

    if timezone.upper() == 'MSK':
        return current + timedelta(hours=3)
    elif timezone.upper() == 'EET':
        return current + timedelta(hours=2)
    elif timezone.upper() == 'UTC':
        return current
    else:
        return datetime.now()


def calculate_processing_time(start_time: float) -> str:
    """Красивый расчёт времени обработки"""
    processing_time = time.time() - start_time

    if processing_time < 0.001:
        return "<1мс"
    elif processing_time < 1:
        return f"{processing_time * 1000:.0f}мс"
    elif processing_time < 60:
        return f"{processing_time:.1f}с"
    else:
        minutes = int(processing_time // 60)
        seconds = int(processing_time % 60)
        return f"{minutes}м {seconds}с"


def truncate_text(text: str, max_length: int, suffix: str = "...",
                  preserve_words: bool = True) -> str:
    """Обрезка текста с умным сохранением слов"""
    if len(text) <= max_length:
        return text

    available_length = max_length - len(suffix)

    if preserve_words and available_length > max_length * 0.5:
        # Пытаемся обрезать по словам
        truncated = text[:available_length]
        last_space = truncated.rfind(' ')

        if last_space > 0:
            truncated = truncated[:last_space]
    else:
        truncated = text[:available_length]

    return truncated + suffix


def extract_numbers(text: str) -> List[str]:
    """Извлечение всех чисел из текста"""
    return re.findall(r'\d+(?:\.\d+)?', text)


def extract_integers(text: str) -> List[int]:
    """Извлечение целых чисел из текста"""
    numbers = re.findall(r'\d+', text)
    return [int(n) for n in numbers]


def validate_lead_id(lead_id: str) -> bool:
    """Валидация ID лида с расширенными проверками"""
    if not lead_id or not str(lead_id).strip():
        return False

    try:
        id_num = int(str(lead_id).strip())
        return 1 <= id_num <= 999999999  # Разумные пределы для ID
    except (ValueError, TypeError):
        return False


def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла в человекочитаемый вид"""
    if size_bytes == 0:
        return "0 Б"

    size_names = ["Б", "КБ", "МБ", "ГБ", "ТБ", "ПБ"]
    i = 0
    size = float(size_bytes)

    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"


def get_system_info() -> Dict[str, Any]:
    """Получение информации о системе"""
    info = {
        'timestamp': get_current_time().isoformat(),
        'python_version': None,
        'platform': None,
        'memory': {},
        'disk': {},
        'cpu': {},
        'process': {}
    }

    try:
        import sys
        info['python_version'] = sys.version.split()[0]

        import platform
        info['platform'] = {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine()
        }

    except ImportError:
        pass

    try:
        import psutil

        # Информация о памяти
        memory = psutil.virtual_memory()
        info['memory'] = {
            'total': format_file_size(memory.total),
            'available': format_file_size(memory.available),
            'percent': memory.percent,
            'used': format_file_size(memory.used)
        }

        # Информация о диске
        disk = psutil.disk_usage('/')
        info['disk'] = {
            'total': format_file_size(disk.total),
            'used': format_file_size(disk.used),
            'free': format_file_size(disk.free),
            'percent': round((disk.used / disk.total) * 100, 1)
        }

        # Информация о CPU
        info['cpu'] = {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'load_avg': getattr(psutil, 'getloadavg', lambda: [0, 0, 0])()
        }

        # Информация о процессе
        process = psutil.Process()
        info['process'] = {
            'pid': process.pid,
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 1),
            'cpu_percent': process.cpu_percent(),
            'threads': process.num_threads(),
            'create_time': datetime.fromtimestamp(process.create_time()).isoformat()
        }

    except ImportError:
        info['error'] = 'psutil не установлен'
    except Exception as e:
        info['error'] = str(e)

    return info


def check_internet_connection(url: str = "https://8.8.8.8", timeout: int = 5) -> bool:
    """Проверка интернет-соединения"""
    test_urls = [
        "https://8.8.8.8",
        "https://1.1.1.1",
        "https://api.telegram.org",
        "https://google.com"
    ]

    for test_url in [url] + test_urls:
        try:
            response = requests.get(test_url, timeout=timeout)
            if response.status_code < 400:
                return True
        except Exception:
            continue

    return False


def generate_session_id(length: int = 8) -> str:
    """Генерация уникального ID сессии"""
    import uuid
    return str(uuid.uuid4()).replace('-', '')[:length]


def generate_hash(data: str, algorithm: str = 'md5') -> str:
    """Генерация хеша для данных"""
    data_bytes = data.encode('utf-8')

    if algorithm.lower() == 'md5':
        return hashlib.md5(data_bytes).hexdigest()
    elif algorithm.lower() == 'sha1':
        return hashlib.sha1(data_bytes).hexdigest()
    elif algorithm.lower() == 'sha256':
        return hashlib.sha256(data_bytes).hexdigest()
    else:
        return hashlib.md5(data_bytes).hexdigest()


def mask_sensitive_data(data: str, mask_char: str = "*",
                       show_start: int = 2, show_end: int = 2) -> str:
    """Маскировка чувствительных данных для логов"""
    if not data:
        return data

    data_str = str(data)

    if len(data_str) <= show_start + show_end:
        return mask_char * len(data_str)

    masked_length = len(data_str) - show_start - show_end

    return (data_str[:show_start] +
            (mask_char * masked_length) +
            data_str[-show_end:])


def parse_telegram_entities(text: str, entities: List[Dict]) -> str:
    """Парсинг entity от Telegram для правильного форматирования"""
    if not entities:
        return text

    # Сортируем по offset для правильной обработки (с конца)
    sorted_entities = sorted(entities, key=lambda x: x['offset'], reverse=True)

    result = text

    for entity in sorted_entities:
        start = entity['offset']
        end = start + entity['length']
        entity_text = text[start:end]

        # Форматируем в зависимости от типа
        if entity['type'] == 'bold':
            formatted_text = f"<b>{entity_text}</b>"
        elif entity['type'] == 'italic':
            formatted_text = f"<i>{entity_text}</i>"
        elif entity['type'] == 'underline':
            formatted_text = f"<u>{entity_text}</u>"
        elif entity['type'] == 'strikethrough':
            formatted_text = f"<s>{entity_text}</s>"
        elif entity['type'] == 'code':
            formatted_text = f"<code>{entity_text}</code>"
        elif entity['type'] == 'pre':
            formatted_text = f"<pre>{entity_text}</pre>"
        elif entity['type'] == 'url':
            formatted_text = f'<a href="{entity_text}">{entity_text}</a>'
        elif entity['type'] == 'text_link':
            url = entity.get('url', entity_text)
            formatted_text = f'<a href="{url}">{entity_text}</a>'
        else:
            formatted_text = entity_text

        result = result[:start] + formatted_text + result[end:]

    return result


def create_progress_bar(current: int, total: int, length: int = 20,
                        filled_char: str = "█", empty_char: str = "░") -> str:
    """Создание текстового прогресс-бара"""
    if total == 0:
        bar = filled_char * length
        return f"{bar} 100.0%"

    progress = min(max(current / total, 0), 1)
    filled_length = int(length * progress)
    empty_length = length - filled_length

    bar = filled_char * filled_length + empty_char * empty_length
    percentage = progress * 100

    return f"{bar} {percentage:.1f}%"


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Безопасный парсинг JSON с обработкой ошибок"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        log.debug(f"Не удалось распарсить JSON: {e}")
        return default


def safe_json_dumps(data: Any, default: Any = "{}") -> str:
    """Безопасная сериализация в JSON"""
    try:
        return json.dumps(data, ensure_ascii=False, indent=None)
    except (TypeError, ValueError) as e:
        log.debug(f"Не удалось сериализовать в JSON: {e}")
        return str(default)


def get_app_version() -> str:
    """Получение версии приложения"""
    version_sources = [
        'version.txt',
        'VERSION',
        '.version'
    ]

    for source in version_sources:
        try:
            with open(source, 'r', encoding='utf-8') as f:
                version = f.read().strip()
                if version:
                    return version
        except FileNotFoundError:
            continue
        except Exception:
            continue

    # Пробуем получить из git
    try:
        import subprocess
        result = subprocess.run(['git', 'describe', '--tags', '--always'],
                                capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    return "unknown"


def health_check() -> Dict[str, Any]:
    """Комплексная проверка здоровья приложения"""
    checks = {
        'timestamp': get_current_time().isoformat(),
        'status': 'healthy',
        'version': get_app_version(),
        'checks': {},
        'metrics': {}
    }

    # Проверка переменных окружения
    try:
        env_validation = validate_env_vars()
        checks['checks']['environment'] = {
            'status': 'ok' if env_validation['valid'] else 'error',
            'errors_count': len(env_validation['errors']),
            'warnings_count': len(env_validation['warnings']),
            'required_vars_ok': sum(bool(v) for v in env_validation['required_vars'].values()),
            'optional_vars_ok': sum(bool(v) for v in env_validation['optional_vars'].values())
        }

        if env_validation['errors']:
            checks['checks']['environment']['errors'] = env_validation['errors'][:3]

    except Exception as e:
        checks['checks']['environment'] = {
            'status': 'error',
            'error': str(e)
        }

    # Проверка базы данных
    try:
        from db import get_stats, init_db  # optional, may raise if not present

        # Пробуем получить статистику
        db_stats = get_stats()

        checks['checks']['database'] = {
            'status': 'ok',
            'total_sessions': db_stats.get('total_sessions', 0),
            'active_sessions': db_stats.get('active_sessions', 0),
            'operations_24h': db_stats.get('operations_24h', 0),
            'success_rate_24h': db_stats.get('success_rate_24h', 0)
        }

        # Добавляем метрики
        checks['metrics']['database'] = db_stats

    except Exception as e:
        checks['checks']['database'] = {
            'status': 'error',
            'error': str(e)
        }

    # Проверка Gemini
    try:
        from gemini_client import test_gemini_connection, get_gemini_info

        gemini_ok = test_gemini_connection()
        gemini_info = get_gemini_info()

        checks['checks']['gemini'] = {
            'status': 'ok' if gemini_ok else 'error',
            'connection_test': gemini_ok,
            'model': gemini_info.get('model_name'),
            'api_configured': gemini_info.get('api_key_configured')
        }

    except Exception as e:
        checks['checks']['gemini'] = {
            'status': 'error',
            'error': str(e)
        }

    # Проверка Bitrix24
    try:
        from bitrix import test_bitrix_connection, get_bitrix_info

        bitrix_info = get_bitrix_info()

        if bitrix_info.get('webhook_configured'):
            bitrix_ok = test_bitrix_connection()
            checks['checks']['bitrix'] = {
                'status': 'ok' if bitrix_ok else 'error',
                'connection_test': bitrix_ok,
                'webhook_configured': True,
                'available_fields': bitrix_info.get('available_fields', 0)
            }
        else:
            checks['checks']['bitrix'] = {
                'status': 'warning',
                'message': 'Not configured',
                'webhook_configured': False
            }

    except Exception as e:
        checks['checks']['bitrix'] = {
            'status': 'error',
            'error': str(e)
        }

    # Проверка интернет-соединения
    internet_ok = check_internet_connection()
    checks['checks']['internet'] = {
        'status': 'ok' if internet_ok else 'error',
        'connection_test': internet_ok
    }

    # Проверка системных ресурсов
    try:
        system_info = get_system_info()

        if 'memory' in system_info and 'percent' in system_info['memory']:
            memory_usage = system_info['memory']['percent']
            disk_usage = system_info.get('disk', {}).get('percent', 0)

            checks['checks']['system'] = {
                'status': 'ok' if memory_usage < 90 and disk_usage < 90 else 'warning',
                'memory_usage': memory_usage,
                'disk_usage': disk_usage
            }

            checks['metrics']['system'] = system_info

    except Exception as e:
        checks['checks']['system'] = {
            'status': 'error',
            'error': str(e)
        }

    # Определение общего статуса
    error_count = sum(1 for check in checks['checks'].values()
                      if isinstance(check, dict) and check.get('status') == 'error')
    warning_count = sum(1 for check in checks['checks'].values()
                        if isinstance(check, dict) and check.get('status') == 'warning')

    if error_count > 0:
        checks['status'] = 'unhealthy'
    elif warning_count > 2:
        checks['status'] = 'degraded'
    else:
        checks['status'] = 'healthy'

    checks['summary'] = {
        'total_checks': len(checks['checks']),
        'errors': error_count,
        'warnings': warning_count,
        'ok': len(checks['checks']) - error_count - warning_count
    }

    return checks


# Константы для использования в приложении
TELEGRAM_LIMITS = {
    'message_length': 4096,
    'caption_length': 1024,
    'button_text_length': 64,
    'callback_data_length': 64,
    'file_size_mb': 50,
    'photo_size_mb': 10,
    'video_size_mb': 50
}

RESPONSE_TEMPLATES = {
    'error': "❌ <b>Ошибка:</b> {error}",
    'success': "✅ <b>Успех:</b> {message}",
    'warning': "⚠️ <b>Внимание:</b> {message}",
    'info': "ℹ️ <b>Информация:</b> {message}",
    'processing': "🔄 <b>Обработка...</b> {message}",
    'completed': "🎉 <b>Завершено:</b> {message}",
    'debug': "🐛 <b>Отладка:</b> {message}"
}


def create_message(template_type: str, **kwargs) -> str:
    """Создание форматированного сообщения по шаблону"""
    template = RESPONSE_TEMPLATES.get(template_type, "{message}")

    try:
        return template.format(**kwargs)
    except KeyError as e:
        log.warning(f"Отсутствует параметр {e} для шаблона {template_type}")
        return f"Ошибка форматирования сообщения: {kwargs}"


def log_performance(func_name: str, start_time: float,
                   additional_info: Optional[Dict] = None):
    """Логирование производительности функций"""
    duration = time.time() - start_time

    log_message = f"Производительность {func_name}: {calculate_processing_time(start_time)}"

    if additional_info:
        details = ", ".join([f"{k}={v}" for k, v in additional_info.items()])
        log_message += f" ({details})"

    if duration > 5:
        log.warning(log_message + " - МЕДЛЕННО")
    elif duration > 1:
        log.info(log_message)
    else:
        log.debug(log_message)


def benchmark_function(func, *args, **kwargs) -> Tuple[Any, float]:
    """Бенчмарк функции с замером времени выполнения"""
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    except Exception as e:
        duration = time.time() - start_time
        log.error(f"Ошибка в бенчмарке функции {func.__name__}: {e}")
        raise


def create_backup_filename(base_name: str, extension: str = 'json') -> str:
    """Создание имени файла резервной копии с timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_name}_backup_{timestamp}.{extension}"


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Простая валидация JSON по схеме"""
    errors: List[str] = []

    # Проверяем обязательные поля
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Отсутствует обязательное поле: {field}")

    # Проверяем типы полей
    properties = schema.get('properties', {})
    for field_name, field_schema in properties.items():
        if field_name in data:
            expected_type = field_schema.get('type')
            value = data[field_name]

            if expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Поле {field_name} должно быть строкой")
            elif expected_type == 'integer' and not isinstance(value, int):
                errors.append(f"Поле {field_name} должно быть целым числом")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Поле {field_name} должно быть числом")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Поле {field_name} должно быть булевым")
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append(f"Поле {field_name} должно быть массивом")
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Поле {field_name} должно быть объектом")

            # Проверяем enum значения
            if 'enum' in field_schema and value not in field_schema['enum']:
                errors.append(f"Недопустимое значение для {field_name}: {value}")

    return len(errors) == 0, errors


def clean_html_tags(text: str, allowed_tags: List[str] = None) -> str:
    """Очистка HTML тегов с возможностью сохранения разрешенных"""
    if not text:
        return text

    if allowed_tags is None:
        # Удаляем все HTML теги
        clean_text = re.sub(r'<[^>]+>', '', text)
    else:
        # Удаляем только неразрешенные теги
        allowed_pattern = '|'.join(re.escape(tag) for tag in allowed_tags)
        pattern = rf'<(?!/?(?:{allowed_pattern})\b)[^>]*>'
        clean_text = re.sub(pattern, '', text)

    # Заменяем HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }

    for entity, char in html_entities.items():
        clean_text = clean_text.replace(entity, char)

    return clean_text


def extract_urls(text: str) -> List[str]:
    """Извлечение всех URL из текста"""
    url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.-]*)*(?:\?(?:[\w&=%.+-]*)*)?(?:#(?:[\w.])*)?)?'
    return re.findall(url_pattern, text, re.IGNORECASE)


def extract_emails(text: str) -> List[str]:
    """Извлечение email адресов из текста"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """Извлечение номеров телефонов из текста (российский формат)"""
    phone_patterns = [
        r'\+7\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}',  # +7 (XXX) XXX-XX-XX
        r'8\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}',     # 8 (XXX) XXX-XX-XX
        r'\d{11}',                                              # 11 цифр подряд
        r'\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}'               # XXX-XXX-XX-XX
    ]

    phones = []
    for pattern in phone_patterns:
        phones.extend(re.findall(pattern, text))

    return list(set(phones))  # Убираем дубли


def normalize_phone_number(phone: str) -> str:
    """Нормализация номера телефона к единому формату"""
    # Удаляем все кроме цифр и +
    clean_phone = re.sub(r'[^\d+]', '', phone)

    # Преобразуем в формат +7XXXXXXXXXX
    if clean_phone.startswith('8') and len(clean_phone) == 11:
        return '+7' + clean_phone[1:]
    elif clean_phone.startswith('7') and len(clean_phone) == 11:
        return '+' + clean_phone
    elif clean_phone.startswith('+7') and len(clean_phone) == 12:
        return clean_phone
    elif len(clean_phone) == 10:
        return '+7' + clean_phone
    else:
        return phone  # Возвращаем как есть если не удалось нормализовать


def create_telegram_deep_link(bot_username: str, start_parameter: str = None) -> str:
    """Создание deep link для Telegram бота"""
    base_url = f"https://t.me/{bot_username.lstrip('@')}"
    if start_parameter:
        return f"{base_url}?start={start_parameter}"
    else:
        return base_url


def generate_random_string(length: int = 10, chars: str = None) -> str:
    """Генерация случайной строки"""
    import random
    import string

    if chars is None:
        chars = string.ascii_letters + string.digits

    return ''.join(random.choice(chars) for _ in range(length))


def is_business_hours(hour: int = None, timezone: str = 'MSK',
                      start_hour: int = 9, end_hour: int = 18) -> bool:
    """Проверка рабочего времени"""
    if hour is None:
        current_time = get_current_time(timezone)
        hour = current_time.hour

    return start_hour <= hour < end_hour


def calculate_business_days(start_date: datetime, days: int) -> datetime:
    """Расчет рабочих дней (исключая выходные)"""
    current_date = start_date
    added_days = 0

    while added_days < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Понедельник = 0, Воскресенье = 6
            added_days += 1

    return current_date


def format_currency(amount: Union[int, float], currency: str = 'RUB') -> str:
    """Форматирование валютных сумм"""
    currency_symbols = {
        'RUB': '₽',
        'USD': '$',
        'EUR': '€',
        'GBP': '£'
    }

    symbol = currency_symbols.get(currency.upper(), currency)

    try:
        numeric_amount = float(amount)
    except Exception:
        return f"{amount} {symbol}"

    if numeric_amount >= 1000000:
        return f"{numeric_amount / 1000000:.1f}M {symbol}"
    elif numeric_amount >= 1000:
        return f"{numeric_amount / 1000:.1f}K {symbol}"
    else:
        # Отображаем без дробной части, с пробелами как разделителем тысяч
        return f"{int(round(numeric_amount)):,} {symbol}".replace(',', ' ')


def parse_duration_string(duration_str: str) -> Optional[timedelta]:
    """Парсинг строки длительности в timedelta"""
    if not duration_str or not isinstance(duration_str, str):
        return None

    # Паттерны для разных форматов
    patterns: List[Tuple[str, Any]] = [
        (r'(\d+)h', lambda m: timedelta(hours=int(m.group(1)))),
        (r'(\d+)m', lambda m: timedelta(minutes=int(m.group(1)))),
        (r'(\d+)s', lambda m: timedelta(seconds=int(m.group(1)))),
        (r'(\d+)d', lambda m: timedelta(days=int(m.group(1)))),
        (r'(\d+):(\d+):(\d+)', lambda m: timedelta(
            hours=int(m.group(1)),
            minutes=int(m.group(2)),
            seconds=int(m.group(3))
        )),
        (r'(\d+):(\d+)', lambda m: timedelta(
            hours=int(m.group(1)),
            minutes=int(m.group(2))
        ))
    ]

    for pattern, converter in patterns:
        match = re.search(pattern, duration_str.lower())
        if match:
            return converter(match)

    return None


def rate_limiter(max_calls: int, time_window: int):
    """Декоратор для ограничения частоты вызовов функций"""
    calls: Dict[str, List[float]] = {}

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            func_key = f"{func.__name__}_{id(args)}_{id(frozenset(kwargs.items()))}"

            if func_key not in calls:
                calls[func_key] = []

            # Очищаем старые вызовы
            calls[func_key] = [call_time for call_time in calls[func_key]
                               if now - call_time < time_window]

            # Проверяем лимит
            if len(calls[func_key]) >= max_calls:
                raise RuntimeError(f"Превышен лимит вызовов для {func.__name__}: "
                                   f"{max_calls} вызовов за {time_window} секунд")

            # Записываем новый вызов
            calls[func_key].append(now)

            return func(*args, **kwargs)

        return wrapper

    return decorator


class PerformanceMonitor:
    """Класс для мониторинга производительности"""
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def start_timer(self, operation: str):
        """Начать замер времени операции"""
        self.metrics[operation] = {'start_time': time.time()}

    def end_timer(self, operation: str, additional_data: Dict = None):
        """Завершить замер времени операции"""
        if operation in self.metrics:
            duration = time.time() - self.metrics[operation]['start_time']
            self.metrics[operation]['duration'] = duration
            self.metrics[operation]['end_time'] = time.time()

            if additional_data:
                self.metrics[operation].update(additional_data)

    def get_metrics(self) -> Dict[str, Any]:
        """Получить все метрики"""
        return self.metrics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Получить сводку по метрикам"""
        summary = {
            'total_operations': len(self.metrics),
            'total_time': sum(m.get('duration', 0) for m in self.metrics.values()),
            'average_time': 0,
            'slowest_operation': None,
            'fastest_operation': None
        }

        durations = [m.get('duration', 0) for m in self.metrics.values() if m.get('duration')]

        if durations:
            summary['average_time'] = sum(durations) / len(durations)

            max_duration = max(durations)
            min_duration = min(durations)

            for op, metrics in self.metrics.items():
                if metrics.get('duration') == max_duration:
                    summary['slowest_operation'] = {'operation': op, 'duration': max_duration}
                if metrics.get('duration') == min_duration:
                    summary['fastest_operation'] = {'operation': op, 'duration': min_duration}

        return summary


# Глобальный монитор производительности
performance_monitor = PerformanceMonitor()


# Контекстный менеджер для замера производительности
class performance_timer:
    """Контекстный менеджер для замера времени выполнения"""
    def __init__(self, operation_name: str, monitor: PerformanceMonitor = None):
        self.operation_name = operation_name
        self.monitor = monitor or performance_monitor

    def __enter__(self):
        self.monitor.start_timer(self.operation_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        additional_data = {}
        if exc_type:
            additional_data['error'] = str(exc_val)
            additional_data['success'] = False
        else:
            additional_data['success'] = True

        self.monitor.end_timer(self.operation_name, additional_data)


def create_error_report(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Создание детального отчета об ошибке"""
    import traceback

    report = {
        'timestamp': get_current_time().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context or {}
    }

    # Добавляем информацию о системе
    try:
        report['system_info'] = get_system_info()
    except Exception:
        pass

    return report


# Экспорт основных функций и классов
__all__ = [
    # Валидация и проверки
    'validate_env_vars', 'validate_lead_id', 'validate_json_schema',
    'check_internet_connection', 'health_check',

    # Форматирование и преобразование
    'sanitize_text', 'format_datetime', 'format_file_size', 'format_currency',
    'truncate_text', 'clean_html_tags', 'normalize_phone_number',

    # Извлечение данных
    'extract_numbers', 'extract_integers', 'extract_urls',
    'extract_emails', 'extract_phone_numbers',

    # Утилиты времени
    'get_current_time', 'calculate_processing_time', 'is_business_hours',
    'calculate_business_days', 'parse_duration_string',

    # JSON и данные
    'safe_json_loads', 'safe_json_dumps', 'mask_sensitive_data',

    # Системные утилиты
    'get_system_info', 'get_app_version', 'generate_session_id',
    'generate_hash', 'generate_random_string',

    # Telegram утилиты
    'parse_telegram_entities', 'create_telegram_deep_link',
    'create_progress_bar', 'create_message',

    # Декораторы
    'retry_on_failure', 'rate_limiter',

    # Мониторинг производительности
    'PerformanceMonitor', 'performance_monitor', 'performance_timer',
    'benchmark_function', 'log_performance',

    # Константы и шаблоны
    'TELEGRAM_LIMITS', 'RESPONSE_TEMPLATES',

    # Обработка ошибок
    'create_error_report'
]
