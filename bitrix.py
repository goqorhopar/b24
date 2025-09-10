import os
import requests
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urljoin

log = logging.getLogger(__name__)

BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
BITRIX_RESPONSIBLE_ID = os.getenv('BITRIX_RESPONSIBLE_ID', '1')
BITRIX_CREATED_BY_ID = os.getenv('BITRIX_CREATED_BY_ID', '1')
BITRIX_TASK_DEADLINE_DAYS = int(os.getenv('BITRIX_TASK_DEADLINE_DAYS', '3'))

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))
MAX_COMMENT_LENGTH = int(os.getenv('MAX_COMMENT_LENGTH', '8000'))

class BitrixError(Exception):
    pass

def _make_bitrix_request(method: str, data: Dict[str, Any], retries: int = MAX_RETRIES) -> Dict[str, Any]:
    if not BITRIX_WEBHOOK_URL:
        raise BitrixError("BITRIX_WEBHOOK_URL не настроен")
    url = urljoin(BITRIX_WEBHOOK_URL.rstrip('/') + '/', method)

    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.post(
                url, json=data, timeout=REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()
            if 'error' in result:
                raise BitrixError(result.get('error_description', result.get('error', 'Ошибка Bitrix API')))
            return result
        except requests.exceptions.RequestException as e:
            last_exc = e
            log.warning(f"HTTP ошибка Bitrix (попытка {attempt+1}/{retries}): {e}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            last_exc = e
            log.error(f"Неожиданная ошибка Bitrix: {e}")
            time.sleep(RETRY_DELAY)
    raise BitrixError(f"Не удалось выполнить запрос к Bitrix: {last_exc}")

def update_lead_comment(lead_id: str, comment: str) -> Dict[str, Any]:
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")
    if not comment or not comment.strip():
        raise BitrixError("Комментарий пустой")

    if len(comment) > MAX_COMMENT_LENGTH:
        comment = comment[:MAX_COMMENT_LENGTH] + "\n\n[Комментарий обрезан из-за ограничений длины]"
        log.warning(f"COMMENTS для лида {lead_id} обрезан до {MAX_COMMENT_LENGTH}")

    data = {
        'id': lead_id.strip(),
        'fields': {'COMMENTS': comment.strip()},
        'params': {'REGISTER_SONET_EVENT': 'Y'}
    }
    return _make_bitrix_request('crm.lead.update.json', data)

def get_lead_info(lead_id: str) -> Dict[str, Any]:
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")

    data = {
        'id': lead_id.strip()
    }
    return _make_bitrix_request('crm.lead.get.json', data)

def get_lead_fields() -> Dict[str, Any]:
    """
    Возвращает описание полей лида (для enum/boolean маппинга).
    """
    return _make_bitrix_request('crm.lead.fields.json', {})

def _map_bool(value: Any) -> str:
    return '1' if bool(value) else '0'

def _normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return str(s).strip().lower()

def _enum_find_id(items: List[Dict[str, Any]], text_value: str) -> Optional[str]:
    """
    Находит ID enum по тексту (VALUE или VALUE_LOCALIZED), регистронезависимо.
    """
    target = _normalize_text(text_value)
    for it in items:
        val = _normalize_text(it.get('VALUE')) or _normalize_text(it.get('VALUE_LOCALIZED'))
        if val == target:
            return str(it.get('ID'))
    # Попробуем contains, если точного совпадения нет
    for it in items:
        val = _normalize_text(it.get('VALUE')) or _normalize_text(it.get('VALUE_LOCALIZED'))
        if target and target in val:
            return str(it.get('ID'))
    return None

def build_fields_from_gemini(gemini: Dict[str, Any], fields_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Собирает словарь fields для crm.lead.update на основе структурированных данных Gemini
    и меты полей Bitrix (динамический поиск enum ID).
    Предполагаемые поля в Bitrix:
      - COMMENTS (string)
      - UF_CRM_1754665062 WOW-эффект (string)
      - UF_CRM_1547738289 ТИП КЛИЕНТА (enum)
      - UF_CRM_1555492157080 Почему некачественный (enum)
      - UF_CRM_1579102568584 Что продает (string)
      - UF_CRM_1592909799043 Как сформулирована задача (string)
      - UF_CRM_1592910027 Рекламный бюджет (string)
      - UF_CRM_1754651857 Вышли на ЛПР? (boolean)
      - UF_CRM_1754651891 Назначили встречу? (boolean)
      - UF_CRM_1754651937 Провели встречу? (boolean)
      - UF_CRM_1754652099 Сделали КП? (enum)
      - UF_CRM_1755007163632 ЛПР подтвержден? (enum)
    """
    result = {}

    # 1) Comments
    analysis = str(gemini.get('analysis') or '').strip()
    if analysis:
        result['COMMENTS'] = analysis[:MAX_COMMENT_LENGTH]

    # 2) Простые строки
    result['UF_CRM_1754665062'] = str(gemini.get('wow_effect') or '').strip()                        # WOW
    result['UF_CRM_1579102568584'] = str(gemini.get('product') or '').strip()                        # Что продает
    result['UF_CRM_1592909799043'] = str(gemini.get('task_formulation') or '').strip()               # Как сформулирована задача
    result['UF_CRM_1592910027'] = str(gemini.get('ad_budget') or '').strip()                         # Рекламный бюджет

    # 3) Boolean
    result['UF_CRM_1754651857'] = _map_bool(gemini.get('is_lpr'))                                    # Вышли на ЛПР
    result['UF_CRM_1754651891'] = _map_bool(gemini.get('meeting_scheduled'))                         # Назначили встречу
    result['UF_CRM_1754651937'] = _map_bool(gemini.get('meeting_done'))                              # Провели встречу

    # 4) Enums — ищем ID по тексту
    # ТИП КЛИЕНТА
    client_type_text = gemini.get('client_type_text')
    if client_type_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1547738289', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, client_type_text)
        if enum_id:
            result['UF_CRM_1547738289'] = enum_id

    # Почему некачественный
    bad_reason_text = gemini.get('bad_reason_text')
    if bad_reason_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1555492157080', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, bad_reason_text)
        if enum_id:
            result['UF_CRM_1555492157080'] = enum_id

    # Сделали КП?
    kp_done_text = gemini.get('kp_done_text')
    if kp_done_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1754652099', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, kp_done_text)
        if enum_id:
            result['UF_CRM_1754652099'] = enum_id

    # ЛПР подтвержден?
    lpr_confirmed_text = gemini.get('lpr_confirmed_text')
    if lpr_confirmed_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1755007163632', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, lpr_confirmed_text)
        if enum_id:
            result['UF_CRM_1755007163632'] = enum_id

    return result

def update_lead_with_checklist(lead_id: str, gemini_struct: Dict[str, Any]) -> Dict[str, Any]:
    """
    Забирает мету полей, строит fields, обновляет лид.
    """
    # 1) Мета полей (для enum)
    fields_meta = get_lead_fields()
    # 2) Сборка полей
    fields = build_fields_from_gemini(gemini_struct, fields_meta)
    if not fields:
        raise BitrixError("Нет данных для обновления полей лида")

    data = {
        'id': str(lead_id).strip(),
        'fields': fields,
        'params': {'REGISTER_SONET_EVENT': 'Y'}
    }
    return _make_bitrix_request('crm.lead.update.json', data)

def test_bitrix_connection() -> bool:
    try:
        if not BITRIX_WEBHOOK_URL:
            return False
        _ = get_lead_fields()
        return True
    except Exception as e:
        log.warning(f"Bitrix тест провален: {e}")
        return False
