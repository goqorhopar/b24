import os
import logging
import time
from typing import Optional, Dict, Any, Tuple
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

STRUCTURED_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "analysis": {"type": "string"},
        "wow_effect": {"type": "string"},
        "client_type_text": {"type": "string"},         # текст enum, например: A/B/C/Некачественный
        "bad_reason_text": {"type": "string"},          # текст enum при некачественном
        "product": {"type": "string"},
        "task_formulation": {"type": "string"},
        "ad_budget": {"type": "string"},
        "is_lpr": {"type": "boolean"},
        "meeting_scheduled": {"type": "boolean"},
        "meeting_done": {"type": "boolean"},
        "kp_done_text": {"type": "string"},             # текст enum, например: Да/Нет/В процессе
        "lpr_confirmed_text": {"type": "string"}        # текст enum
    },
    "required": ["analysis"]
}

def _prompt(transcript: str) -> str:
    return f"""
Ты — эксперт по продажам. Проанализируй транскрипт по чеклисту, а также верни структурированные данные в JSON.

1) Сформируй "analysis" — качественный разбор по 12 критериям (как в твоём шаблоне).
2) Для полей CRM верни аккуратные значения:
   - wow_effect: строка (кратко, по сути)
   - client_type_text: один из — A, B, C, Некачественный (если модель считает лид некачественным, так и укажи)
   - bad_reason_text: если client_type_text = "Некачественный", укажи причину (краткая фраза)
   - product: что клиент продаёт (строка)
   - task_formulation: как сформулирована задача (строка)
   - ad_budget: бюджет/возможности (строка)
   - is_lpr: true/false (вышли ли на ЛПР)
   - meeting_scheduled: true/false (назначили встречу)
   - meeting_done: true/false (провели встречу)
   - kp_done_text: одно из — Да, Нет, В процессе
   - lpr_confirmed_text: одно из — Да, Нет, Неясно

Вначале дай короткий человекочитаемый анализ, затем верни JSON (только один JSON-объект, без лишнего текста вокруг).
Транскрипт:
\"\"\"{transcript.strip()}\"\"\"
""".strip()

def analyze_transcript_structured(transcript: str) -> Tuple[str, Dict[str, Any]]:
    """
    Возвращает (analysis_text, data_dict) — человекочитаемый анализ и структурированные поля.
    """
    if not transcript or len(transcript.strip()) < 10:
        raise ValueError("Транскрипт слишком короткий или пустой")

    model = genai.GenerativeModel(MODEL_NAME)

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = model.generate_content(
                _prompt(transcript),
                safety_settings=safety_settings,
                generation_config={"temperature": 0.4, "top_p": 0.9}
            )
            text = (resp.text or "").strip()
            if not text:
                raise RuntimeError("Пустой ответ модели")

            # Находим последний JSON в ответе (модель может выдать анализ + JSON)
            import json, re
            # Попробуем извлечь JSON-объект фигурными скобками
            json_candidates = re.findall(r'\{(?:[^{}]|(?R))*\}', text, flags=re.DOTALL)
            parsed = None
            for candidate in reversed(json_candidates):
                try:
                    parsed = json.loads(candidate)
                    break
                except Exception:
                    continue

            if not parsed or not isinstance(parsed, dict):
                raise RuntimeError("Не удалось извлечь JSON из ответа модели")

            # Анализ (чел.текст) — это весь ответ без последнего JSON
            analysis_text = text
            if json_candidates:
                last = json_candidates[-1]
                cut_index = analysis_text.rfind(last)
                if cut_index > 0:
                    analysis_text = analysis_text[:cut_index].strip()

            return analysis_text, parsed
        except Exception as e:
            last_err = e
            log.warning(f"Ошибка Gemini (попытка {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)

    raise RuntimeError(f"Не удалось получить анализ от Gemini: {last_err}")

def test_gemini_connection() -> bool:
    try:
        _ = analyze_transcript_structured("Мини-тест: клиент хочет увеличить лиды, бюджет 200к, ЛПР на связи.")
        return True
    except Exception as e:
        log.warning(f"Тест Gemini провален: {e}")
        return False
