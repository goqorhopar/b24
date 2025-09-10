import os
import logging
import time
import re
import json
from typing import Dict, Any, Tuple
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
    """
    Убирает или заменяет слова, которые могут триггерить фильтры Gemini,
    но не важны для бизнес-анализа.
    """
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
Ты — эксперт по продажам. Проанализируй транскрипт по чеклисту и верни JSON с полями:
analysis, wow_effect, client_type_text, bad_reason_text, product, task_formulation,
ad_budget, is_lpr, meeting_scheduled, meeting_done, kp_done_text, lpr_confirmed_text.

Транскрипт:
\"\"\"{transcript.strip()}\"\"\"
"""


def extract_last_json(text: str) -> Tuple[Dict[str, Any], int]:
    """
    Ищет последний корректный JSON-объект в тексте.
    Возвращает (dict, позиция_начала) или (None, -1).
    """
    last_json = None
    last_pos = -1
    # Ищем с конца текста
    for start in range(len(text)):
        if text[start] == '{':
            try:
                obj = json.loads(text[start:])
                last_json = obj
                last_pos = start
                break
            except Exception:
                continue
    return last_json, last_pos


def analyze_transcript_structured(transcript: str) -> Tuple[str, Dict[str, Any]]:
    """
    Возвращает (analysis_text, data_dict) — человекочитаемый анализ и структурированные поля.
    """
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

            parsed, cut_index = extract_last_json(text)
            if not parsed or not isinstance(parsed, dict):
                raise RuntimeError("Не удалось извлечь JSON из ответа модели")

            analysis_text = text
            if cut_index > 0:
                analysis_text = analysis_text[:cut_index].strip()

            return analysis_text, parsed

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
        _ = analyze_transcript_structured("Мини-тест: клиент хочет увеличить лиды, бюджет 200к, ЛПР на связи.")
        return True
    except Exception as e:
        log.warning(f"Тест Gemini провален: {e}")
        return False
