import os
import logging
import time
import re
import json
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

log = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY не найден в переменных окружения!")

genai.configure(api_key=GEMINI_API_KEY)

# Универсальная сборка SAFETY_SETTINGS
SAFETY_SETTINGS = {}
if hasattr(HarmCategory, "HARM_CATEGORY_HATE_SPEECH"):
    SAFETY_SETTINGS[getattr(HarmCategory, "HARM_CATEGORY_HATE_SPEECH")] = HarmBlockThreshold.BLOCK_NONE
if hasattr(HarmCategory, "HARM_CATEGORY_HARASSMENT"):
    SAFETY_SETTINGS[getattr(HarmCategory, "HARM_CATEGORY_HARASSMENT")] = HarmBlockThreshold.BLOCK_NONE
if hasattr(HarmCategory, "HARM_CATEGORY_SEXUAL"):
    SAFETY_SETTINGS[getattr(HarmCategory, "HARM_CATEGORY_SEXUAL")] = HarmBlockThreshold.BLOCK_NONE
elif hasattr(HarmCategory, "HARM_CATEGORY_SEXUALLY_EXPLICIT"):
    SAFETY_SETTINGS[getattr(HarmCategory, "HARM_CATEGORY_SEXUALLY_EXPLICIT")] = HarmBlockThreshold.BLOCK_NONE
if hasattr(HarmCategory, "HARM_CATEGORY_DANGEROUS_CONTENT"):
    SAFETY_SETTINGS[getattr(HarmCategory, "HARM_CATEGORY_DANGEROUS_CONTENT")] = HarmBlockThreshold.BLOCK_NONE


def sanitize_transcript_for_safety(text: str) -> str:
    if not text:
        return text
    replacements = {
        r"\bсекс\w*\b": "S*X",
        r"\bэрот\w*\b": "эр.",
        r"\bпорно\w*\b": "P*RN",
    }
    clean = text
    for pattern, repl in replacements.items():
        clean = re.sub(pattern, repl, clean, flags=re.IGNORECASE)
    return clean


def _prompt(transcript: str) -> str:
    return f"""
Ты — эксперт по продажам. Проанализируй транскрипт по чеклисту и верни результат в двух частях:

1) Человекочитаемый анализ (текст).
2) В конце ответа — один корректный JSON-объект (без лишнего текста после него) со следующими ключами:
analysis, wow_effect, client_type_text, bad_reason_text, product, task_formulation,
ad_budget, is_lpr, meeting_scheduled, meeting_done, kp_done_text, lpr_confirmed_text.

Транскрипт:
\"\"\"{transcript.strip()}\"\"\"
"""


def extract_json_from_text(text: str) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Извлекает JSON из текста, ищет как последний JSON, так и JSON в markdown блоках.
    Возвращает кортеж (parsed_json, start_index)
    """
    if not text:
        return None, -1
    
    # Сначала попробуем найти JSON в markdown блоке (```json ... ```)
    json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block_match:
        json_str = json_block_match.group(1).strip()
        try:
            return json.loads(json_str), json_block_match.start()
        except json.JSONDecodeError:
            log.warning("Найден JSON блок, но он содержит ошибки")
    
    # Ищем последний валидный JSON объект в тексте
    brace_stack = []
    json_start = -1
    json_end = -1
    
    for i, char in enumerate(text):
        if char == '{':
            if not brace_stack:
                json_start = i
            brace_stack.append(char)
        elif char == '}' and brace_stack:
            brace_stack.pop()
            if not brace_stack and json_start != -1:
                json_end = i
                json_str = text[json_start:json_end+1]
                try:
                    return json.loads(json_str), json_start
                except json.JSONDecodeError:
                    # Продолжаем поиск, если этот JSON невалиден
                    json_start = -1
                    json_end = -1
    
    # Если не нашли полный JSON, попробуем найти начало JSON
    last_brace_pos = text.rfind('{')
    if last_brace_pos != -1:
        # Пробуем парсить от открывающей скобки до конца
        try:
            return json.loads(text[last_brace_pos:]), last_brace_pos
        except json.JSONDecodeError:
            pass
    
    return None, -1


def analyze_transcript_structured(transcript: str) -> Tuple[str, Dict[str, Any]]:
    if not transcript or len(transcript.strip()) < 10:
        raise ValueError("Транскрипт слишком короткий или пустой")

    model = genai.GenerativeModel(MODEL_NAME)
    last_err = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = model.generate_content(
                _prompt(transcript),
                safety_settings=SAFETY_SETTINGS,
                generation_config={"temperature": 0.4, "top_p": 0.9}
            )
            text = (resp.text or "").strip()
            if not text:
                raise RuntimeError("Пустой ответ модели")

            log.debug(f"Ответ Gemini (попытка {attempt}): {text[:500]}...")

            parsed, cut_index = extract_json_from_text(text)
            if parsed and isinstance(parsed, dict):
                analysis_text = text[:cut_index].strip() if cut_index > 0 else text
                return analysis_text, parsed
            else:
                log.warning("JSON не найден в ответе, возвращаю только текст анализа")
                return text, {}

        except Exception as e:
            last_err = e
            err_str = str(e)
            log.warning(f"Ошибка Gemini (попытка {attempt}/{MAX_RETRIES}): {err_str}")

            if "HARM_CATEGORY" in err_str.upper() or "SAFETY" in err_str.upper():
                log.info("Повторная попытка с очищенным транскриптом...")
                transcript = sanitize_transcript_for_safety(transcript)
                time.sleep(RETRY_DELAY)
                continue

            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"Не удалось получить анализ от Gemini: {last_err}")


def test_gemini_connection() -> bool:
    try:
        analysis, data = analyze_transcript_structured("Мини-тест: клиент хочет увеличить лиды, бюджет 200к, ЛПР на связи.")
        return bool(analysis)
    except Exception as e:
        log.warning(f"Тест Gemini провален: {e}")
        return False
