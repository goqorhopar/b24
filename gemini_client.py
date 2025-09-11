import os
import logging
import time
import re
import json
from typing import Dict, Any, Tuple, Optional, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

# Настройки из переменных окружения
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY не найден в переменных окружения!")

# Настройка Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Универсальная настройка безопасности
SAFETY_SETTINGS = {}
harm_categories = [
    'HARM_CATEGORY_HATE_SPEECH',
    'HARM_CATEGORY_HARASSMENT', 
    'HARM_CATEGORY_SEXUAL',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT',
    'HARM_CATEGORY_DANGEROUS_CONTENT'
]

for category_name in harm_categories:
    if hasattr(HarmCategory, category_name):
        category = getattr(HarmCategory, category_name)
        SAFETY_SETTINGS[category] = HarmBlockThreshold.BLOCK_NONE

log.info(f"Настроены категории безопасности: {list(SAFETY_SETTINGS.keys())}")

def sanitize_transcript_for_safety(text: str) -> str:
    """Очистка транскрипта от потенциально проблемных слов для Gemini"""
    if not text:
        return text
    
    # Замены для потенциально проблемных слов
    replacements = {
        # Явно сексуальные термины
        r"\bсекс\w*\b": "интимн.",
        r"\bэрот\w*\b": "эр.",
        r"\bпорно\w*\b": "взр.контент",
        # Потенциально агрессивные слова
        r"\bубить\b": "устранить",
        r"\bубийство\b": "устранение",
        r"\bнасилие\b": "принуждение",
        # Наркотики и алкоголь
        r"\bнаркотик\w*\b": "запр.вещество",
        r"\bкокаин\w*\b": "зап.в-во",
        r"\bгерои\w*н\b": "зап.в-во",
        # Мат и оскорбления  
        r"\bбля\w*\b": "блин",
        r"\bхуй\w*\b": "фиг",
        r"\bпизд\w*\b": "плохо"
    }
    
    clean_text = text
    for pattern, replacement in replacements.items():
        clean_text = re.sub(pattern, replacement, clean_text, flags=re.IGNORECASE)
    
    return clean_text

def _build_analysis_prompt(transcript: str) -> str:
    """Построение детального промпта для анализа транскрипта"""
    
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    prompt = f"""Ты — эксперт-аналитик по продажам в digital-агентстве. Сегодня {current_date}.

ЗАДАЧА: Проанализируй транскрипт встречи с потенциальным клиентом и заполни чек-лист по стандартам B2B продаж.

ТРАНСКРИПТ ВСТРЕЧИ:
```
{transcript.strip()}
```

ИНСТРУКЦИИ:
1. Внимательно изучи транскрипт
2. Проведи детальный анализ встречи
3. Заполни все поля чек-листа на основе найденной информации
4. Если информации недостаточно, укажи "Не указано" или оставь поле пустым

ФОРМАТ ОТВЕТА:
Сначала дай развернутый анализ встречи (2-3 абзаца), затем обязательно добавь JSON-блок.

---

ЧЕКЛ-ЛИСТ ДЛЯ JSON (все поля обязательны):

ОСНОВНЫЕ ПОЛЯ:
- analysis: детальный анализ встречи (строка)
- wow_effect: что впечатлило клиента, его реакция на предложение (строка)
- product: что продает клиент, его бизнес (строка) 
- task_formulation: как клиент сформулировал свою задачу (строка)
- ad_budget: рекламный бюджет клиента (строка)
- closing_comment: комментарий по закрытию лида, если есть (строка)

СТАТУСНЫЕ ПОЛЯ (boolean true/false):
- is_lpr: вышли ли мы на лицо принимающее решения
- meeting_scheduled: была ли назначена встреча
- meeting_done: была ли проведена встреча

КЛАССИФИКАЦИОННЫЕ ПОЛЯ (точный текст):
- client_type_text: тип клиента - точно один из: "AAA", "BBB", "CCC"
- bad_reason_text: почему лид некачественный (если применимо) - один из: "Реклама", "Ошиблись номером", "Тест", "Не интересует контекст", "Садик"
- kp_done_text: сделано ли КП - точно: "Да" или "Нет"  
- lpr_confirmed_text: подтвержден ли ЛПР - точно: "Да" или "Нет"
- source_text: откуда узнали о нас - один из: "Roistat", "Рекомендация", "Зорин", "Самостоятельный мониторинг"
- our_product_text: что мы продаем - один из: "Продвижение", "Внедрение", "Лицензия", "БИГ ДАТА ГЦК", "БИГ ДАТА ТЕХНОЛОГИЯ", "БИГ ДАТА КОЛЛЦЕНТР", "Привлечение по партнерской программе", "Аналитика"

ДОПОЛНИТЕЛЬНЫЕ ПОЛЯ:
- meeting_date: дата фактического проведения встречи в формате YYYY-MM-DD (если есть)
- planned_meeting_date: планируемая дата встречи в формате YYYY-MM-DD HH:MM:SS (если есть)
- meeting_responsible_id: ID ответственного за встречу (число, если упоминается)

ВАЖНО: 
- Возвращай только валидный JSON без markdown разметки
- Все поля должны присутствовать в JSON
- Для отсутствующей информации используй null
- Boolean поля только true/false
- Строковые поля в кавычках
- Финальный JSON должен быть на отдельной строке

ПРИМЕР ОТВЕТА:
Встреча прошла продуктивно. Клиент заинтересован в наших услугах...

{{"analysis": "текст анализа", "wow_effect": "текст или null", "is_lpr": true, ...}}"""

    return prompt

def extract_json_from_gemini_response(text: str) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Извлечение JSON из ответа Gemini с поддержкой различных форматов
    """
    if not text:
        return None, -1
    
    log.debug(f"Извлечение JSON из текста длиной {len(text)} символов")
    
    # 1. Поиск JSON в markdown блоках
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    for block in json_blocks:
        try:
            parsed = json.loads(block.strip())
            if isinstance(parsed, dict):
                log.debug("Найден валидный JSON в markdown блоке")
                return parsed, text.find(block)
        except json.JSONDecodeError:
            continue
    
    # 2. Поиск JSON без markdown
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_matches = re.findall(json_pattern, text, re.DOTALL)
    
    # Сортируем по длине (более длинные JSON более вероятно содержат все поля)
    json_matches.sort(key=len, reverse=True)
    
    for match in json_matches:
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict) and len(parsed) > 3:  # Минимум полей
                log.debug(f"Найден валидный JSON с {len(parsed)} полями")
                return parsed, text.find(match)
        except json.JSONDecodeError:
            continue
    
    # 3. Поиск с более гибким паттерном
    all_braces = re.finditer(r'[{}]', text)
    
    stack = []
    potential_jsons = []
    
    for match in all_braces:
        char = match.group()
        pos = match.start()
        
        if char == '{':
            stack.append(pos)
        elif char == '}' and stack:
            start_pos = stack.pop()
            if not stack:  # Завершенный JSON объект
                json_str = text[start_pos:pos+1]
                potential_jsons.append((json_str, start_pos))
    
    # Пробуем парсить найденные JSON
    for json_str, start_pos in sorted(potential_jsons, key=lambda x: len(x[0]), reverse=True):
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and len(parsed) > 2:
                log.debug(f"Найден JSON с гибким поиском: {len(parsed)} полей")
                return parsed, start_pos
        except json.JSONDecodeError:
            continue
    
    log.warning("JSON не найден в ответе Gemini")
    return None, -1

def validate_gemini_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Валидация JSON от Gemini на соответствие схеме"""
    errors = []
    
    # Обязательные поля
    required_fields = ['analysis']
    for field in required_fields:
        if field not in data:
            errors.append(f"Отсутствует обязательное поле: {field}")
    
    # Проверка типов boolean полей
    boolean_fields = ['is_lpr', 'meeting_scheduled', 'meeting_done']
    for field in boolean_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], bool):
                errors.append(f"Поле {field} должно быть boolean")
    
    # Проверка enum полей
    enum_validations = {
        'client_type_text': ['AAA', 'BBB', 'CCC'],
        'bad_reason_text': ['Реклама', 'Ошиблись номером', 'Тест', 'Не интересует контекст', 'Садик'],
        'kp_done_text': ['Да', 'Нет'],
        'lpr_confirmed_text': ['Да', 'Нет'],
        'source_text': ['Roistat', 'Рекомендация', 'Зорин', 'Самостоятельный мониторинг'],
        'our_product_text': ['Продвижение', 'Внедрение', 'Лицензия', 'БИГ ДАТА ГЦК', 'БИГ ДАТА ТЕХНОЛОГИЯ', 'БИГ ДАТА КОЛЛЦЕНТР', 'Привлечение по партнерской программе', 'Аналитика']
    }
    
    for field, valid_values in enum_validations.items():
        if field in data and data[field] is not None:
            if data[field] not in valid_values:
                errors.append(f"Недопустимое значение для {field}: '{data[field]}'. Допустимые: {valid_values}")
    
    # Проверка дат
    date_fields = ['meeting_date', 'planned_meeting_date']
    for field in date_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], str):
                errors.append(f"Поле {field} должно быть строкой")
    
    return len(errors) == 0, errors

def normalize_gemini_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Нормализация и очистка JSON от Gemini"""
    normalized = {}
    
    # Обрабатываем все поля
    all_fields = [
        'analysis', 'wow_effect', 'product', 'task_formulation', 'ad_budget', 
        'closing_comment', 'is_lpr', 'meeting_scheduled', 'meeting_done',
        'client_type_text', 'bad_reason_text', 'kp_done_text', 'lpr_confirmed_text',
        'source_text', 'our_product_text', 'meeting_date', 'planned_meeting_date',
        'meeting_responsible_id'
    ]
    
    for field in all_fields:
        value = data.get(field)
        
        if value is None:
            normalized[field] = None
        elif field in ['is_lpr', 'meeting_scheduled', 'meeting_done']:
            # Boolean поля
            if isinstance(value, bool):
                normalized[field] = value
            elif isinstance(value, str):
                normalized[field] = value.lower() in ['true', 'да', 'yes', '1']
            else:
                normalized[field] = bool(value)
        elif field == 'meeting_responsible_id':
            # Числовое поле
            if isinstance(value, (int, float)):
                normalized[field] = int(value)
            elif isinstance(value, str) and value.isdigit():
                normalized[field] = int(value)
            else:
                normalized[field] = None
        else:
            # Строковые поля
            if isinstance(value, str):
                normalized[field] = value.strip()
            elif value is not None:
                normalized[field] = str(value).strip()
            else:
                normalized[field] = None
    
    return normalized

def analyze_transcript_structured(transcript: str, max_attempts: int = None) -> Tuple[str, Dict[str, Any]]:
    """
    Анализ транскрипта встречи с возвращением структурированных данных
    """
    if not transcript or len(transcript.strip()) < 10:
        raise ValueError("Транскрипт слишком короткий или пустой")

    if max_attempts is None:
        max_attempts = MAX_RETRIES

    # Очищаем транскрипт для безопасности
    clean_transcript = sanitize_transcript_for_safety(transcript)
    
    model = genai.GenerativeModel(MODEL_NAME)
    last_error = None
    
    log.info(f"Начинаем анализ транскрипта длиной {len(transcript)} символов")
    
    for attempt in range(1, max_attempts + 1):
        try:
            log.debug(f"Попытка анализа {attempt}/{max_attempts}")
            
            # Генерируем контент
            response = model.generate_content(
                _build_analysis_prompt(clean_transcript),
                safety_settings=SAFETY_SETTINGS,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "top_k": 40,
                    "max_output_tokens": 2048
                }
            )
            
            response_text = (response.text or "").strip()
            
            if not response_text:
                raise RuntimeError("Получен пустой ответ от Gemini")

            log.debug(f"Получен ответ от Gemini длиной {len(response_text)} символов")
            
            # Извлекаем JSON
            parsed_json, json_start = extract_json_from_gemini_response(response_text)
            
            if parsed_json:
                # Валидируем JSON
                is_valid, validation_errors = validate_gemini_json(parsed_json)
                
                if not is_valid:
                    log.warning(f"JSON не прошел валидацию: {validation_errors}")
                    if attempt < max_attempts:
                        continue
                
                # Нормализуем данные
                normalized_json = normalize_gemini_json(parsed_json)
                
                # Извлекаем текст анализа
                analysis_text = response_text[:json_start].strip() if json_start > 0 else "Анализ встречи выполнен"
                
                # Обновляем analysis в JSON если он короткий
                if not normalized_json.get('analysis') or len(normalized_json['analysis']) < 50:
                    normalized_json['analysis'] = analysis_text
                
                log.info(f"Анализ успешно завершен с {len(normalized_json)} полями")
                return analysis_text, normalized_json
            
            else:
                log.warning(f"JSON не найден в ответе (попытка {attempt})")
                if attempt == max_attempts:
                    # Возвращаем хотя бы текстовый анализ
                    return response_text, {"analysis": response_text}
                continue

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            
            log.warning(f"Ошибка анализа (попытка {attempt}/{max_attempts}): {e}")
            
            # Специальная обработка ошибок безопасности
            if any(keyword in error_msg for keyword in ['safety', 'harm', 'blocked']):
                log.info("Ошибка безопасности, очищаем транскрипт дополнительно")
                clean_transcript = sanitize_transcript_for_safety(clean_transcript)
                # Дополнительная очистка
                clean_transcript = re.sub(r'[^\w\s\-.,!?():]', ' ', clean_transcript)
                clean_transcript = re.sub(r'\s+', ' ', clean_transcript).strip()
            
            if attempt < max_attempts:
                time.sleep(RETRY_DELAY * attempt)  # Экспоненциальная задержка
            
    error_msg = f"Не удалось проанализировать транскрипт после {max_attempts} попыток"
    if last_error:
        error_msg += f". Последняя ошибка: {last_error}"
    
    log.error(error_msg)
    raise RuntimeError(error_msg)

def analyze_transcript_simple(transcript: str) -> str:
    """Простой анализ транскрипта без структурированных данных"""
    try:
        analysis_text, _ = analyze_transcript_structured(transcript)
        return analysis_text
    except Exception as e:
        log.error(f"Ошибка простого анализа: {e}")
        raise

def test_gemini_connection() -> bool:
    """Тестирование соединения с Gemini"""
    try:
        test_transcript = """
        Тестовый звонок. Клиент интересуется продвижением сайта. 
        Бюджет 100000 рублей в месяц. ЛПР на связи. Встреча назначена на завтра.
        """
        
        analysis_text, structured_data = analyze_transcript_structured(test_transcript)
        
        # Проверяем что получили валидные данные
        if analysis_text and isinstance(structured_data, dict) and 'analysis' in structured_data:
            log.info("✅ Тест соединения с Gemini прошел успешно")
            return True
        else:
            log.warning("❌ Тест соединения вернул неожиданные данные")
            return False
            
    except Exception as e:
        log.warning(f"❌ Тест соединения с Gemini провален: {e}")
        return False

def get_gemini_info() -> Dict[str, Any]:
    """Получение информации о конфигурации Gemini"""
    return {
        'api_key_configured': bool(GEMINI_API_KEY),
        'api_key_preview': GEMINI_API_KEY[:10] + '...' if GEMINI_API_KEY else None,
        'model_name': MODEL_NAME,
        'max_retries': MAX_RETRIES,
        'retry_delay': RETRY_DELAY,
        'safety_settings_count': len(SAFETY_SETTINGS),
        'connection_test': test_gemini_connection()
    }

def analyze_with_retry_strategy(transcript: str, strategy: str = 'conservative') -> Tuple[str, Dict[str, Any]]:
    """
    Анализ с различными стратегиями повторных попыток
    
    Strategies:
    - conservative: мало попыток, строгая валидация
    - aggressive: много попыток, мягкая валидация  
    - balanced: сбалансированный подход (по умолчанию)
    """
    strategies = {
        'conservative': {'max_attempts': 2, 'temperature': 0.1, 'strict_validation': True},
        'aggressive': {'max_attempts': 5, 'temperature': 0.5, 'strict_validation': False},
        'balanced': {'max_attempts': 3, 'temperature': 0.3, 'strict_validation': True}
    }
    
    config = strategies.get(strategy, strategies['balanced'])
    
    log.info(f"Анализ транскрипта со стратегией '{strategy}': {config}")
    
    return analyze_transcript_structured(transcript, max_attempts=config['max_attempts'])

def batch_analyze_transcripts(transcripts: List[str], 
                            delay_between: float = 1.0) -> List[Tuple[str, Dict[str, Any]]]:
    """Пакетный анализ нескольких транскриптов"""
    results = []
    
    for i, transcript in enumerate(transcripts):
        try:
            log.info(f"Анализ транскрипта {i+1}/{len(transcripts)}")
            result = analyze_transcript_structured(transcript)
            results.append(result)
            
            # Задержка между запросами
            if i < len(transcripts) - 1:
                time.sleep(delay_between)
                
        except Exception as e:
            log.error(f"Ошибка анализа транскрипта {i+1}: {e}")
            results.append((f"Ошибка анализа: {e}", {"analysis": f"Ошибка: {e}"}))
    
    return results

def create_analysis_summary(structured_data: Dict[str, Any]) -> str:
    """Создание краткого резюме анализа"""
    summary_parts = []
    
    # Основные индикаторы
    is_lpr = structured_data.get('is_lpr', False)
    meeting_done = structured_data.get('meeting_done', False)
    kp_done = structured_data.get('kp_done_text', '').lower() == 'да'
    
    summary_parts.append("🎯 КРАТКОЕ РЕЗЮМЕ:")
    summary_parts.append(f"• ЛПР: {'✅' if is_lpr else '❌'}")
    summary_parts.append(f"• Встреча: {'✅' if meeting_done else '❌'}")  
    summary_parts.append(f"• КП: {'✅' if kp_done else '❌'}")
    
    # Тип клиента
    client_type = structured_data.get('client_type_text')
    if client_type:
        summary_parts.append(f"• Тип клиента: {client_type}")
    
    # Бюджет
    budget = structured_data.get('ad_budget')
    if budget:
        summary_parts.append(f"• Бюджет: {budget}")
    
    # Продукт клиента
    product = structured_data.get('product')
    if product:
        summary_parts.append(f"• Продукт клиента: {product[:50]}{'...' if len(product) > 50 else ''}")
    
    return "\n".join(summary_parts)

def export_analysis_to_json(analysis_text: str, structured_data: Dict[str, Any]) -> str:
    """Экспорт полного анализа в JSON формат"""
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'analysis_text': analysis_text,
        'structured_data': structured_data,
        'summary': create_analysis_summary(structured_data),
        'metadata': {
            'model_name': MODEL_NAME,
            'fields_count': len(structured_data),
            'has_lpr': structured_data.get('is_lpr', False),
            'has_meeting': structured_data.get('meeting_done', False)
        }
    }
    
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# Экспорт основных функций
__all__ = [
    'analyze_transcript_structured',
    'analyze_transcript_simple', 
    'analyze_with_retry_strategy',
    'batch_analyze_transcripts',
    'create_analysis_summary',
    'export_analysis_to_json',
    'test_gemini_connection',
    'get_gemini_info'
]
