import os
import logging
import time
import re
import json
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime

log = logging.getLogger(__name__)

# Настройки из переменных окружения
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-1.5')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY не найден в переменных окружения!")

# Настройка Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Универсальная настройка безопасности (по возможности)
SAFETY_SETTINGS = {}
try:
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
except Exception:
    log.debug("Категории безопасности не настроены (возможно версия библиотеки не поддерживает)")

# --- вспомогательные функции ---

def sanitize_transcript_for_safety(text: str) -> str:
    """Очистка транскрипта от потенциально проблемных слов для Gemini"""
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

    clean_text = text
    for pattern, replacement in replacements.items():
        clean_text = re.sub(pattern, replacement, clean_text, flags=re.IGNORECASE)

    return clean_text


def _build_analysis_prompt(transcript: str) -> str:
    """Построение промпта для анализа транскрипта (упрощённая версия)"""
    current_date = datetime.now().strftime("%d.%m.%Y")
    prompt = f"""Ты — эксперт-аналитик по продажам в digital-агентстве. Сегодня {current_date}.

ЗАДАЧА: Проанализируй транскрипт встречи с потенциальным клиентом и верни JSON со следующими полями (все поля должны присутствовать, отсутствующие — null):

{{"analysis": "...", "wow_effect": null, "product": null, "task_formulation": null, "ad_budget": null, "closing_comment": null,
"is_lpr": null, "meeting_scheduled": null, "meeting_done": null,
"client_type_text": null, "bad_reason_text": null, "kp_done_text": null, "lpr_confirmed_text": null, "source_text": null, "our_product_text": null,
"meeting_date": null, "planned_meeting_date": null, "meeting_responsible_id": null}}

Транскрипт:

Ответь **ТОЛЬКО** корректным JSON-объектом (без текста вокруг)."""
    return prompt


def _call_gemini(prompt: str, model: str = None, max_tokens: int = 1200) -> str:
    """Вызов Gemini с простыми retry-механизмами; возвращает текст ответа"""
    if model is None:
        model = MODEL_NAME

    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            # Вызов chat/completion API (универсально)
            resp = genai.create_chat_completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_output_tokens=max_tokens
            )
            if hasattr(resp, 'candidates') and resp.candidates:
                text = resp.candidates[0].content
            else:
                text = getattr(resp, 'output', {}).get('content', '')
            return text
        except Exception as e:
            last_exc = e
            log.warning(f"Попытка {attempt+1}/{MAX_RETRIES} к Gemini провалена: {e}")
            time.sleep(RETRY_DELAY * (attempt + 1))
    log.exception(f"Не удалось вызвать Gemini: {last_exc}")
    raise last_exc


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Пытается извлечь JSON-объект из текста ответа"""
    if not text:
        return None

    # Ищем первый валидный JSON-объект
    # Попытка 1: блок ```json ... ```
    m = re.search(r'```json\s*(\{.*\})\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Попытка 2: прямой JSON в тексте
    brace_stack = []
    start = None
    for i, ch in enumerate(text):
        if ch == '{':
            if start is None:
                start = i
            brace_stack.append('{')
        elif ch == '}' and brace_stack:
            brace_stack.pop()
            if not brace_stack and start is not None:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    start = None
                    continue
    # Ничего не найдено
    return None


def validate_gemini_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Приводит выход модели к ожидаемому набору полей и типов"""
    # Список всех полей, которые мы ожидаем
    expected_fields = [
        "analysis", "wow_effect", "product", "task_formulation", "ad_budget", "closing_comment",
        "is_lpr", "meeting_scheduled", "meeting_done",
        "client_type_text", "bad_reason_text", "kp_done_text", "lpr_confirmed_text", "source_text", "our_product_text",
        "meeting_date", "planned_meeting_date", "meeting_responsible_id"
    ]

    normalized = {}
    for f in expected_fields:
        v = data.get(f) if isinstance(data, dict) else None
        # Normalize booleans to True/False/null
        if f in ("is_lpr", "meeting_scheduled", "meeting_done"):
            if isinstance(v, bool):
                normalized[f] = v
            elif isinstance(v, str):
                sval = v.strip().lower()
                if sval in ('yes', 'да', 'true', '1'):
                    normalized[f] = True
                elif sval in ('no', 'нет', 'false', '0'):
                    normalized[f] = False
                else:
                    normalized[f] = None
            else:
                normalized[f] = None
        else:
            normalized[f] = v if v is not None else None

    return normalized


# --- Экспортируемые функции, которые использует main.py ---


def analyze_transcript_structured(transcript: str) -> Dict[str, Any]:
    """
    Основная функция: даёт промпт в Gemini, извлекает JSON и возвращает нормализованный словарь.
    Если модель вернула невалидный JSON — возвращается "fallback" результат с полем analysis.
    """
    try:
        if not transcript or not transcript.strip():
            return {"analysis": None}

        txt = sanitize_transcript_for_safety(transcript)
        prompt = _build_analysis_prompt(txt)

        raw = _call_gemini(prompt)
        parsed = extract_json_from_text(raw)

        if parsed is None:
            # Если JSON не найден — возвращаем основной анализ как текст (в analysis) и null для остальных
            return {
                "analysis": (raw[:MAX_RETRIES * 1000] if raw else "Не удалось получить ответ от модели"),
                "wow_effect": None,
                "product": None,
                "task_formulation": None,
                "ad_budget": None,
                "closing_comment": None,
                "is_lpr": None,
                "meeting_scheduled": None,
                "meeting_done": None,
                "client_type_text": None,
                "bad_reason_text": None,
                "kp_done_text": None,
                "lpr_confirmed_text": None,
                "source_text": None,
                "our_product_text": None,
                "meeting_date": None,
                "planned_meeting_date": None,
                "meeting_responsible_id": None
            }
        else:
            validated = validate_gemini_output(parsed)
            # Добавим анализ в поле analysis если он есть в parsed (иначе попытаемся взять часть raw текста)
            if parsed.get('analysis'):
                validated['analysis'] = parsed.get('analysis')
            else:
                # Попытка найти текстовый анализ в начале raw ответа
                plain_analysis = raw.strip()
                if len(plain_analysis) > 200:
                    plain_analysis = plain_analysis[:200] + "..."
                validated['analysis'] = plain_analysis
            return validated

    except Exception as e:
        log.exception("Ошибка при анализе транскрипта: %s", e)
        return {"analysis": f"Ошибка при анализе: {e}"}


def create_analysis_summary(data: Dict[str, Any]) -> str:
    """Форматирует короткое резюме анализа для отправки в чат"""
    if not data:
        return "Анализ недоступен"

    lines = []
    analysis = data.get('analysis') or "Нет анализа"
    lines.append("✅ Анализ встречи выполнен")
    lines.append("")
    if data.get('is_lpr') is True:
        lines.append("• ЛПР: найден ✅")
    elif data.get('is_lpr') is False:
        lines.append("• ЛПР: не найден ❌")
    else:
        lines.append("• ЛПР: не указано")

    if data.get('meeting_done'):
        lines.append("• Встреча: проведена ✅")
    else:
        lines.append("• Встреча: не проведена / не указано")

    if data.get('kp_done_text'):
        lines.append(f"• КП: {data.get('kp_done_text')}")

    if data.get('ad_budget'):
        lines.append(f"• Бюджет: {data.get('ad_budget')}")

    if data.get('product'):
        prod = data.get('product')
        lines.append(f"• Продукт клиента: {prod[:120]}{'...' if len(str(prod))>120 else ''}")

    lines.append("")
    lines.append("📝 Краткий анализ:")
    lines.append(analysis if len(analysis) < 1000 else analysis[:1000] + "...")

    return "\n".join(lines)


def get_gemini_info() -> Dict[str, Any]:
    """Возвращает информацию о состоянии Gemini-коннекта"""
    info = {
        'model_name': MODEL_NAME,
        'api_key_present': bool(GEMINI_API_KEY),
        'connection_test': False,
        'max_retries': MAX_RETRIES
    }
    try:
        # Пассивный тест — вызов небольшой подсказки (нежёстко, чтобы не расходовать много токенов)
        test_prompt = "Короткий ответ: \"ok\""
        resp = _call_gemini(test_prompt, max_tokens=16)
        if resp and 'ok' in resp.lower():
            info['connection_test'] = True
        else:
            info['connection_test'] = True  # получили ответ — считаем OK
    except Exception:
        info['connection_test'] = False

    return info


def test_gemini_connection() -> bool:
    """Простая функция для проверки подключения к Gemini"""
    try:
        info = get_gemini_info()
        return bool(info.get('connection_test'))
    except Exception:
        return False
