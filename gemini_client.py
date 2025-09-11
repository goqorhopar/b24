# gemini_client.py
import os
import logging
import time
import re
import json
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Попытка импортировать google.generativeai (работает с разными версиями)
try:
    import google.generativeai as genai  # type: ignore
except Exception as exc:
    raise RuntimeError(f"Невозможно импортировать google.generativeai: {exc}")

# Попытка импортировать типы безопасности (в некоторых версиях их может не быть)
try:
    from google.generativeai.types import HarmCategory, HarmBlockThreshold  # type: ignore
except Exception:
    HarmCategory = None
    HarmBlockThreshold = None  # type: ignore

log = logging.getLogger(__name__)

# Конфигурация из окружения
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("RETRY_DELAY", "2"))
TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
TOP_P = float(os.getenv("GEMINI_TOP_P", "0.2"))
MAX_OUTPUT_TOKENS_DEFAULT = int(os.getenv("GEMINI_MAX_TOKENS", "1200"))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY не найден в переменных окружения!")

# Настройка ключа
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    # Не фатальная ошибка — дальше в вызовах мы обработаем возможные ошибки
    log.debug(f"genai.configure вызвало исключение: {e}")

# Безопасностные настройки (если поддерживаются)
SAFETY_SETTINGS = {}
if HarmCategory is not None and HarmBlockThreshold is not None:
    try:
        categories = [
            'HARM_CATEGORY_HATE_SPEECH',
            'HARM_CATEGORY_HARASSMENT',
            'HARM_CATEGORY_SEXUAL',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT',
            'HARM_CATEGORY_DANGEROUS_CONTENT',
        ]
        for name in categories:
            if hasattr(HarmCategory, name):
                cat = getattr(HarmCategory, name)
                SAFETY_SETTINGS[cat] = HarmBlockThreshold.BLOCK_NONE
        log.debug("SAFETY_SETTINGS установлены")
    except Exception:
        SAFETY_SETTINGS = {}

# ---- Вспомогательные функции ----

def sanitize_transcript_for_safety(text: str) -> str:
    """
    Подменяет потенциально проблемные слова, чтобы снизить вероятность триггеров фильтров
    и убрать грубую лексику перед отправкой в модель.
    """
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
        # мат
        r"\bбля\w*\b": "блин",
        r"\bхуй\w*\b": "фиг",
        r"\bпизд\w*\b": "плохо"
    }

    cleaned = text
    for pattern, repl in replacements.items():
        cleaned = re.sub(pattern, repl, cleaned, flags=re.IGNORECASE)
    return cleaned


def _build_analysis_prompt(transcript: str) -> str:
    """
    Формирует подробный промпт для модели.
    Возвращаемый текст ориентирован на получение JSON-структуры с определёнными полями.
    """
    current_date = datetime.now().strftime("%d.%m.%Y")
    prompt = (
        f"ИНСТРУКЦИЯ ДЛЯ GEMINI (Промпт)\n"
        f"Роль: Ты — эксперт-аналитик по продажам и переговорам. Сегодня {current_date}.\n"
        "Твоя задача — проанализировать транскрипт встречи менеджера с клиентом, дать развернутую оценку по 12 пунктам чек-листа и, что важнее всего, сгенерировать структурированный JSON-объект с данными для автоматического обновления карточки лида и создания задач в CRM Bitrix24.\n\n"
        "ИНСТРУКЦИЯ:\n"
        "1) Внимательно проанализируй предоставленную транскрипцию.\n"
        "2) Сформируй один JSON-объект, содержащий два блока: analysis_report (текстовый отчёт) и bitrix24_update (структурированные данные для CRM).\n"
        "3) Верни строго валидный JSON без какого-либо дополнительного текста.\n\n"
        "ФОРМАТ ОТВЕТА:\n"
        "{\n"
        "  \"analysis_report\": \"...подробный отчёт по 12 пунктам...\",\n"
        "  \"bitrix24_update\": {\n"
        "    \"fields_to_update\": {\n"
        "      \"COMMENTS\": \"строка\",\n"
        "      \"TITLE\": \"строка или null\",\n"
        "      \"NAME\": \"строка или null\",\n"
        "      \"LAST_NAME\": \"строка или null\",\n"
        "      \"COMPANY_TITLE\": \"строка или null\",\n"
        "      \"ASSIGNED_BY_ID\": number или null,\n"
        "      \"UF_*\": \"значения пользовательских полей, если применимо\"\n"
        "    },\n"
        "    \"tasks_to_create\": [\n"
        "      { \"title\": \"строка\", \"description\": \"строка\", \"deadline\": \"YYYY-MM-DD или YYYY-MM-DD HH:MM:SS\", \"responsible_id\": number }\n"
        "    ],\n"
        "    \"lead_category\": \"A|B|C\"\n"
        "  }\n"
        "}\n\n"
        "ЧЕК-ЛИСТ (включить разбор в analysis_report): 1) Бизнес клиента 2) Боли/потребности 3) Возражения 4) Реакция на модель генерации 5) Особый интерес 6) Возможности 7) Ошибки менеджера 8) Путь к закрытию 9) Тон беседы 10) Контроль диалога 11) Рекомендации 12) Категория клиента.\n\n"
        "Строгие требования: Всегда возвращай один корректный JSON с указанной структурой.\n\n"
        "ТРАНСКРИПТ:\n```\n" + transcript.strip() + "\n```\n"
    )
    return prompt


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Ищет JSON-объект в текстовом ответе модели.
    Поддерживает блоки ```json``` и "сырой" JSON.
    """
    if not text:
        return None

    # 1) JSON в ```json ... ```
    m = re.search(r'```json\s*(\{.*\})\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 2) Ищем наиболее длинный корректный JSON-объект методом скобочного стека
    brace_stack = []
    start = None
    candidates = []
    for i, ch in enumerate(text):
        if ch == '{':
            if start is None:
                start = i
            brace_stack.append('{')
        elif ch == '}' and brace_stack:
            brace_stack.pop()
            if not brace_stack and start is not None:
                candidate = text[start:i+1]
                candidates.append(candidate)
                start = None

    # Сортируем кандидаты по длине (большие предпочтительнее)
    candidates.sort(key=len, reverse=True)
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # 3) Попытка найти простой JSON по regex (последняя инстанция)
    json_matches = re.findall(r'\{(?:[^{}]|\{[^{}]*\})*\}', text, re.DOTALL)
    for match in sorted(json_matches, key=len, reverse=True):
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    return None


def validate_gemini_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Приводит выход модели к ожидаемому набору полей и типов.
    Нормализует булевы поля, оставляет все ожидаемые ключи.
    """
    expected_fields = [
        "analysis", "key_request", "pains_text", "budget_value", "budget_currency", "timeline_text", "goal_text",
        "client_name", "client_last_name", "position", "company_title",
        "product", "task_formulation", "ad_budget", "closing_comment",
        "is_lpr", "meeting_scheduled", "meeting_done",
        "client_type_text", "bad_reason_text", "kp_done_text", "lpr_confirmed_text",
        "source_id_code", "source_id_text", "source_text", "our_product_text",
        "meeting_date", "planned_meeting_date", "meeting_responsible_id",
        "sentiment", "next_action", "next_action_comment"
    ]

    normalized: Dict[str, Any] = {}
    for f in expected_fields:
        v = data.get(f) if isinstance(data, dict) else None

        # булевые поля
        if f in ("is_lpr", "meeting_scheduled", "meeting_done"):
            if isinstance(v, bool):
                normalized[f] = v
            elif isinstance(v, (int, float)):
                normalized[f] = bool(v)
            elif isinstance(v, str):
                vs = v.strip().lower()
                if vs in ("yes", "true", "да", "1"):
                    normalized[f] = True
                elif vs in ("no", "false", "нет", "0"):
                    normalized[f] = False
                else:
                    normalized[f] = None
            else:
                normalized[f] = None
        else:
            # числа
            if f in ("budget_value", "meeting_responsible_id"):
                try:
                    normalized[f] = float(v) if v is not None else None
                except Exception:
                    normalized[f] = None
            else:
                # сохраняем значение или None
                normalized[f] = v if v is not None else None

    return normalized


# ---- Вызов модели: универсальный и надёжный ----

def _call_gemini(prompt: str, model: Optional[str] = None, max_tokens: int = MAX_OUTPUT_TOKENS_DEFAULT) -> str:
    """
    Умный обёртывающий вызов Gemini с ретраями.
    Попробует несколько возможных путей вызова в зависимости от версии библиотеки:
      1) genai.GenerativeModel(...).generate_content(...)
      2) genai.generate_text(...) (если доступно)
      3) genai.create_chat_completion(...) (старые интерфейсы)
    Возвращает сырой текст-ответ модели.
    """
    if model is None:
        model = MODEL_NAME

    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 1) Попытка через GenerativeModel (современные версии)
            if hasattr(genai, "GenerativeModel"):
                try:
                    ModelClass = getattr(genai, "GenerativeModel")
                    model_obj = ModelClass(model)
                    # Попытка вызвать generate_content
                    if hasattr(model_obj, "generate_content"):
                        resp = model_obj.generate_content(
                            prompt,
                            generation_config={
                                "max_output_tokens": max_tokens,
                                "temperature": TEMPERATURE,
                                "top_p": TOP_P,
                                "response_mime_type": "application/json"
                            },
                            safety_settings=SAFETY_SETTINGS or None
                        )
                        # возращаем текст — в разных версиях может быть .text или .output
                        if hasattr(resp, "text"):
                            return resp.text
                        if isinstance(resp, dict) and "output" in resp:
                            out = resp.get("output")
                            if isinstance(out, dict):
                                # возможна структура {'content': '...'} или candidates
                                if "content" in out:
                                    return str(out["content"])
                                # кандидаты
                                candidates = out.get("candidates")
                                if candidates and isinstance(candidates, list) and len(candidates) > 0:
                                    cand = candidates[0]
                                    if isinstance(cand, dict):
                                        return cand.get("content", "") or str(cand)
                                    return str(cand)
                            return str(resp)
                        # как fallback
                        return str(resp)
                    # если нет generate_content — попробовать generate_text
                    if hasattr(model_obj, "generate_text"):
                        resp = model_obj.generate_text(prompt, max_output_tokens=max_tokens)
                        if hasattr(resp, "text"):
                            return resp.text
                        return str(resp)
                except Exception as e:
                    log.debug(f"Попытка вызова через GenerativeModel провалилась: {e}")
                    # если упало здесь — пробуем другие варианты
                    last_exc = e

            # 2) genai.generate_text (возможно в модуле)
            if hasattr(genai, "generate_text"):
                try:
                    func = getattr(genai, "generate_text")
                    resp = func(model=model, prompt=prompt, max_output_tokens=max_tokens, temperature=TEMPERATURE, top_p=TOP_P)
                    # обработка возможных структур
                    if isinstance(resp, dict):
                        if "candidates" in resp and resp["candidates"]:
                            cand = resp["candidates"][0]
                            if isinstance(cand, dict) and "content" in cand:
                                return cand["content"]
                            return str(cand)
                        if "output" in resp:
                            out = resp["output"]
                            if isinstance(out, dict) and "content" in out:
                                return out["content"]
                            return str(out)
                    # если объект имеет .text
                    if hasattr(resp, "text"):
                        return resp.text
                    return str(resp)
                except Exception as e:
                    log.debug(f"genai.generate_text провалился: {e}")
                    last_exc = e

            # 3) Старые интерфейсы: create_chat_completion (редко в новых версиях)
            if hasattr(genai, "create_chat_completion"):
                try:
                    resp = genai.create_chat_completion(model=model, messages=[{"role": "user", "content": prompt}], max_output_tokens=max_tokens)
                    # обычно resp.candidates[0].content
                    if hasattr(resp, "candidates") and resp.candidates:
                        return resp.candidates[0].content
                    if isinstance(resp, dict):
                        # попробовать получить глубже
                        cand = resp.get("candidates")
                        if cand and isinstance(cand, list):
                            c0 = cand[0]
                            if isinstance(c0, dict) and "content" in c0:
                                return c0["content"]
                    return str(resp)
                except Exception as e:
                    log.debug(f"create_chat_completion провалился: {e}")
                    last_exc = e

            # Если ни один интерфейс не найден — попробуем REST API как надёжный фолбэк
            try:
                api_key = GEMINI_API_KEY
                if not api_key:
                    raise RuntimeError("GEMINI_API_KEY не задан")
                rest_model = model
                # Попробуем привести названия к REST-идиомам, если указана укороченная форма
                # Например: "gemini-1.5" -> "gemini-1.5-flash" (более доступная модель)
                if rest_model in (None, "gemini-1.5"):
                    rest_model = MODEL_NAME
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{rest_model}:generateContent?key={api_key}"
                payload: Dict[str, Any] = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        }
                    ],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": TEMPERATURE,
                        "topP": TOP_P,
                        "responseMimeType": "application/json"
                    }
                }
                headers = {"Content-Type": "application/json"}
                r = requests.post(url, headers=headers, json=payload, timeout=30)
                if r.status_code == 429:
                    # Рейт-лимит — подождём и повторим попытку
                    wait_s = RETRY_DELAY * attempt
                    log.warning(f"Gemini REST 429 Too Many Requests — ожидание {wait_s}s перед повтором")
                    time.sleep(wait_s)
                    raise requests.exceptions.HTTPError("429 Too Many Requests", response=r)
                r.raise_for_status()
                data = r.json()
                # В v1beta ответ обычно: candidates[0].content.parts[*].text
                if isinstance(data, dict):
                    candidates = data.get("candidates") or []
                    if candidates:
                        c0 = candidates[0]
                        if isinstance(c0, dict):
                            content = c0.get("content") or {}
                            if isinstance(content, dict):
                                parts = content.get("parts") or []
                                texts = []
                                for p in parts:
                                    if isinstance(p, dict) and "text" in p:
                                        texts.append(str(p["text"]))
                                if texts:
                                    return "\n".join(texts)
                # Фолбэк — вернуть сырой JSON как строку
                return r.text
            except Exception as e:
                last_exc = e
                raise RuntimeError("Ошибка вызова Gemini REST API")

        except Exception as e:
            last_exc = e
            log.warning(f"Попытка {attempt}/{MAX_RETRIES} к Gemini провалена: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
            else:
                log.exception(f"Не удалось вызвать Gemini: {last_exc}")
                raise last_exc

    # На всякий случай
    raise last_exc or RuntimeError("Неизвестная ошибка при вызове Gemini")


# ---- Основные публичные функции API ----

def analyze_transcript_structured(transcript: str) -> Dict[str, Any]:
    """
    Основная функция для анализа транскрипта.
    Возвращает нормализованный словарь с ожидаемыми полями.
    """
    try:
        if not transcript or not transcript.strip():
            return {"analysis": None}

        safe_txt = sanitize_transcript_for_safety(transcript)
        prompt = _build_analysis_prompt(safe_txt)

        raw = _call_gemini(prompt, model=MODEL_NAME, max_tokens=MAX_OUTPUT_TOKENS_DEFAULT)
        if not raw:
            log.warning("Gemini вернул пустой ответ")
            return {"analysis": "Пустой ответ от модели"}

        parsed = extract_json_from_text(raw)
        if parsed is None:
            # Попробуем сделать повторный краткий вызов строго под JSON
            try:
                strict_prompt = "Верни строго JSON по ранее заданной схеме без пояснений. Если данных нет — верни ключи со значением null.\n\nТЕКСТ:\n" + transcript.strip()
                raw2 = _call_gemini(strict_prompt, model=MODEL_NAME, max_tokens=512)
                parsed = extract_json_from_text(raw2)
            except Exception:
                parsed = None
            # Если JSON не найден — попытка взять начало ответа как анализ
            fallback_analysis = raw.strip()
            if len(fallback_analysis) > 4000:
                fallback_analysis = fallback_analysis[:4000] + "..."
            result = {
                "analysis": fallback_analysis,
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
            return result

        validated = validate_gemini_output(parsed)

        # Если модель вернула почти всё null — применим эвристику для базового заполнения
        non_null = sum(1 for k, v in validated.items() if v not in (None, "", [], {}))
        if non_null <= 2:
            # Сформируем хотя бы базовый анализ из первых 700 символов транскрипта
            base = transcript.strip()
            if len(base) > 700:
                base = base[:700] + "..."
            validated["analysis"] = validated.get("analysis") or base

        # Если analysis не заполнён в parsed — попытка извлечь текстовую часть из raw
        if not validated.get("analysis"):
            # Найти всё до JSON (если JSON найден внутри) — это может быть текстовый анализ
            json_pos = None
            try:
                json_pos = raw.find(json.dumps(parsed))
            except Exception:
                json_pos = None

            if json_pos and json_pos > 0:
                possible_analysis = raw[:json_pos].strip()
            else:
                possible_analysis = raw.strip()

            validated["analysis"] = possible_analysis if possible_analysis else None

        return validated

    except Exception as e:
        log.exception("Ошибка при анализе транскрипта: %s", e)
        return {"analysis": f"Ошибка при анализе: {e}"}


def create_analysis_summary(data: Dict[str, Any]) -> str:
    """
    Форматирует короткое резюме анализа для отправки в чат.
    """
    if not data:
        return "Анализ недоступен"

    lines = []
    analysis = data.get("analysis") or "Нет анализа"

    lines.append("✅ Анализ встречи выполнен")
    if data.get("is_lpr") is True:
        lines.append("• ЛПР: найден ✅")
    elif data.get("is_lpr") is False:
        lines.append("• ЛПР: не найден ❌")
    else:
        lines.append("• ЛПР: не указано")

    if data.get("meeting_done") is True:
        lines.append("• Встреча: проведена ✅")
    elif data.get("meeting_scheduled") is True:
        lines.append("• Встреча: запланирована ⏳")
    else:
        lines.append("• Встреча: не указано")

    kp = data.get("kp_done_text")
    if kp:
        lines.append(f"• КП: {kp}")

    budget = data.get("ad_budget")
    if budget:
        lines.append(f"• Бюджет: {budget}")

    product = data.get("product")
    if product:
        prod_short = str(product)[:200] + ("..." if len(str(product)) > 200 else "")
        lines.append(f"• Продукт клиента: {prod_short}")

    lines.append("")
    lines.append("📝 Краткий анализ:")
    lines.append(str(analysis)[:2000])

    return "\n".join(lines)


def get_gemini_info() -> Dict[str, Any]:
    """
    Возвращает информацию о настройках и тестовом ответе Gemini.
    """
    info = {
        "model_name": MODEL_NAME,
        "api_key_present": bool(GEMINI_API_KEY),
        "connection_test": False,
        "max_retries": MAX_RETRIES
    }
    try:
        # Пассивный тест: короткий вызов
        test_prompt = "Короткий ответ: ok"
        resp = _call_gemini(test_prompt, model=MODEL_NAME, max_tokens=16)
        if resp and "ok" in resp.lower():
            info["connection_test"] = True
        else:
            # если получили хоть какой-то ответ, тоже считаем соединение рабочим
            info["connection_test"] = bool(resp)
    except Exception as e:
        log.debug(f"get_gemini_info test failed: {e}")
        info["connection_test"] = False
    return info


def test_gemini_connection() -> bool:
    """
    Утилита для быстрого теста доступности Gemini.
    """
    try:
        return bool(get_gemini_info().get("connection_test"))
    except Exception:
        return False
