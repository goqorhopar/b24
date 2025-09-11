# gemini_client.py
import os
import logging
import time
import re
import json
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime, timedelta

# Настройка логирования
log = logging.getLogger(__name__)

# Конфигурация из окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "5"))  # Увеличиваем задержку
TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
TOP_P = float(os.getenv("GEMINI_TOP_P", "0.2"))
MAX_OUTPUT_TOKENS_DEFAULT = int(os.getenv("GEMINI_MAX_TOKENS", "2000"))  # Увеличиваем лимит токенов

# Глобальные переменные для управления лимитами
_last_request_time = 0
_request_counter = 0
_rate_limit_delay = 2.0  # Минимальная задержка между запросами в секундах

if not GEMINI_API_KEY:
    log.warning("GEMINI_API_KEY не найден в переменных окружения!")

def _rate_limit():
    """Обеспечивает соблюдение лимитов запросов к API"""
    global _last_request_time, _request_counter
    
    current_time = time.time()
    elapsed = current_time - _last_request_time
    
    if elapsed < _rate_limit_delay:
        sleep_time = _rate_limit_delay - elapsed
        log.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()
    _request_counter += 1

def sanitize_transcript_for_safety(text: str) -> str:
    """Очистка транскрипта от потенциально проблемного контента"""
    if not text:
        return text

    replacements = {
        r"\bсекс\w*\b": "интимн.",
        r"\bэрот\w*\b": "эр.",
        r"\bпорно\w*\b": "взр.контент",
        r"\bубить\b": "устранить",
        r"\bубийство\b": "устранение",
        r"\bнасилие\b": "принуждение",
        r"\bнаркотик\w*\b": "запр.вещество",
        r"\bбля\w*\b": "блин",
        r"\bхуй\w*\b": "фиг",
        r"\bпизд\w*\b": "плохо"
    }

    cleaned = text
    for pattern, repl in replacements.items():
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned

def _build_analysis_prompt(transcript: str) -> str:
    """Создание промпта для анализа транскрипта"""
    current_date = datetime.now().strftime("%d.%m.%Y")
    
    prompt = f"""Ты - эксперт по продажам и переговорам. Проанализируй транскрипт встречи и верни ответ в строгом JSON формате.

ТРЕБОВАНИЯ К ФОРМАТУ:
{{
  "analysis_report": "Подробный анализ по 12 пунктам...",
  "bitrix24_update": {{
    "fields_to_update": {{
      "COMMENTS": "Сводка встречи",
      "TITLE": "Название лида",
      "UF_CRM_LEAD_QUALITY": "Высокий/Средний/Низкий"
    }},
    "tasks_to_create": [
      {{
        "title": "Название задачи",
        "description": "Описание задачи", 
        "deadline": "2024-05-24",
        "responsible_id": 123
      }}
    ],
    "lead_category": "A/B/C"
  }}
}}

ЧЕК-ЛИСТ ДЛЯ АНАЛИЗА:
1. Анализ бизнеса клиента
2. Выявление болей и потребностей  
3. Возражения по лидогенерации
4. Реакция на модель генерации
5. Особый интерес к сервису
6. Найденные возможности
7. Ошибки менеджера
8. Путь к закрытию
9. Тон беседы
10. Контроль диалога
11. Рекомендации
12. Категория клиента (A/B/C)

ТРАНСКРИПТ ВСТРЕЧИ:
{transcript.strip()}

Верни ТОЛЬКО JSON без дополнительного текста."""
    
    return prompt

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Извлечение JSON из текстового ответа"""
    if not text:
        return None

    # Поиск JSON в блоке ```json
    json_match = re.search(r'```json\s*(\{.*\})\s*```', text, re.DOTALL | re.IGNORECASE)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Поиск JSON объекта
    brace_count = 0
    start_index = -1
    json_candidates = []
    
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_index = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_index != -1:
                json_candidates.append(text[start_index:i+1])
                start_index = -1
    
    # Проверка кандидатов от самого длинного
    for candidate in sorted(json_candidates, key=len, reverse=True):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    
    return None

def _call_gemini_api(prompt: str, max_tokens: int = MAX_OUTPUT_TOKENS_DEFAULT) -> str:
    """Вызов Gemini через REST API с обработкой ошибок"""
    global _request_counter
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY не настроен")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": TEMPERATURE,
            "topP": TOP_P,
            "responseMimeType": "application/json"
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT", 
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            _rate_limit()  # Соблюдаем лимиты запросов
            
            log.debug(f"Attempt {attempt + 1}/{MAX_RETRIES} to call Gemini API")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 429:
                wait_time = RETRY_DELAY * (2 ** attempt)  # Экспоненциальная backoff
                log.warning(f"Rate limit exceeded. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # Извлечение текста из ответа
            if "candidates" in data and data["candidates"]:
                candidate = data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        return parts[0]["text"]
            
            return json.dumps(data)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = RETRY_DELAY * (2 ** attempt)
                log.warning(f"HTTP 429 - Rate limit. Waiting {wait_time}s...")
                time.sleep(wait_time)
                last_exception = e
            else:
                log.error(f"HTTP error: {e}")
                last_exception = e
        except requests.exceptions.RequestException as e:
            log.error(f"Request error: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY * (attempt + 1))
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            last_exception = e
            time.sleep(RETRY_DELAY * (attempt + 1))
    
    raise last_exception or Exception("Failed to call Gemini API after retries")

def analyze_transcript_structured(transcript: str) -> Dict[str, Any]:
    """Основная функция анализа транскрипта"""
    try:
        if not transcript or not transcript.strip():
            return {"error": "Empty transcript", "analysis": None}
        
        # Очистка и подготовка транскрипта
        safe_text = sanitize_transcript_for_safety(transcript)
        prompt = _build_analysis_prompt(safe_text)
        
        # Вызов API
        raw_response = _call_gemini_api(prompt)
        
        if not raw_response:
            return {"error": "Empty response from Gemini", "analysis": None}
        
        # Извлечение JSON
        parsed_data = extract_json_from_text(raw_response)
        
        if not parsed_data:
            log.warning("Failed to extract JSON from response. Trying fallback...")
            # Попытка прямого парсинга ответа как JSON
            try:
                parsed_data = json.loads(raw_response)
            except json.JSONDecodeError:
                return {
                    "error": "Invalid JSON response",
                    "raw_response": raw_response[:1000] + "..." if len(raw_response) > 1000 else raw_response,
                    "analysis": None
                }
        
        # Валидация структуры ответа
        if not isinstance(parsed_data, dict):
            return {
                "error": "Response is not a JSON object",
                "raw_response": raw_response[:1000] + "..." if len(raw_response) > 1000 else raw_response,
                "analysis": None
            }
        
        # Нормализация структуры ответа
        result = {
            "analysis_report": parsed_data.get("analysis_report", ""),
            "bitrix24_update": parsed_data.get("bitrix24_update", {})
        }
        
        # Заполнение обязательных полей
        if "fields_to_update" not in result["bitrix24_update"]:
            result["bitrix24_update"]["fields_to_update"] = {}
        
        if "tasks_to_create" not in result["bitrix24_update"]:
            result["bitrix24_update"]["tasks_to_create"] = []
        
        if "lead_category" not in result["bitrix24_update"]:
            result["bitrix24_update"]["lead_category"] = "B"  # По умолчанию теплый лид
        
        return result
        
    except Exception as e:
        log.error(f"Error in analyze_transcript_structured: {e}")
        return {
            "error": str(e),
            "analysis": None,
            "bitrix24_update": {
                "fields_to_update": {
                    "COMMENTS": f"Ошибка анализа: {str(e)[:200]}"
                },
                "tasks_to_create": [],
                "lead_category": "C"
            }
        }

def create_analysis_summary(data: Dict[str, Any]) -> str:
    """Создание краткого summary для отправки в чат"""
    if not data or "error" in data:
        return "❌ Анализ не удался. Ошибка при обработке транскрипта."
    
    lines = ["✅ Анализ встречи выполнен успешно"]
    
    if "analysis_report" in data and data["analysis_report"]:
        report = data["analysis_report"]
        if len(report) > 500:
            report = report[:500] + "..."
        lines.append(f"📊 Отчет: {report}")
    
    if "bitrix24_update" in data:
        bitrix_data = data["bitrix24_update"]
        
        if "lead_category" in bitrix_data:
            category_map = {"A": "🔥 Горячий", "B": "🌤️ Теплый", "C": "❄️ Холодный"}
            lines.append(f"• Категория: {category_map.get(bitrix_data['lead_category'], 'Не определена')}")
        
        if "tasks_to_create" in bitrix_data and bitrix_data["tasks_to_create"]:
            lines.append(f"• Задач создано: {len(bitrix_data['tasks_to_create'])}")
    
    return "\n".join(lines)

def get_gemini_info() -> Dict[str, Any]:
    """Информация о настройках Gemini"""
    return {
        "model_name": MODEL_NAME,
        "api_key_configured": bool(GEMINI_API_KEY),
        "max_retries": MAX_RETRIES,
        "rate_limit_delay": _rate_limit_delay
    }

def test_gemini_connection() -> bool:
    """Тест соединения с Gemini"""
    try:
        test_prompt = "Ответь одно слово: OK"
        response = _call_gemini_api(test_prompt, max_tokens=10)
        return "OK" in response.upper()
    except Exception as e:
        log.error(f"Connection test failed: {e}")
        return False

# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Тест соединения
    print("Testing Gemini connection...")
    if test_gemini_connection():
        print("✅ Connection successful")
    else:
        print("❌ Connection failed")
    
    print("Gemini info:", get_gemini_info())
