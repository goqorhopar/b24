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
