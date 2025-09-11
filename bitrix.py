import os
import requests
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urljoin
from datetime import datetime, timedelta

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
    log.info(f"Bitrix request to {method}: {data}")

    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.post(
                url, json=data, timeout=REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            result = response.json()
            
            log.info(f"Bitrix response: {result}")
            
            if 'error' in result:
                error_msg = result.get('error_description', result.get('error', 'Ошибка Bitrix API'))
                log.error(f"Bitrix API error: {error_msg}")
                raise BitrixError(error_msg)
                
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

def create_task(lead_id: str, title: str, description: str, responsible_id: str = None) -> Dict[str, Any]:
    """
    Создает задачу в Bitrix24, связанную с лидом
    """
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")
    
    if not responsible_id:
        responsible_id = BITRIX_RESPONSIBLE_ID
    
    # Рассчитываем дедлайн
    deadline_date = (datetime.now() + timedelta(days=BITRIX_TASK_DEADLINE_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
    
    data = {
        'fields': {
            'TITLE': f"[Лид {lead_id}] {title}",
            'DESCRIPTION': description,
            'RESPONSIBLE_ID': responsible_id,
            'CREATED_BY': BITRIX_CREATED_BY_ID,
            'DEADLINE': deadline_date,
            'UF_CRM_TASK': ['L_' + lead_id.strip()]  # Связываем с лидом
        }
    }
    
    return _make_bitrix_request('tasks.task.add.json', data)

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
    """
    result = {}

    # 1) Comments
    analysis = str(gemini.get('analysis') or '').strip()
    if analysis:
        result['COMMENTS'] = analysis[:MAX_COMMENT_LENGTH]

    # 2) Простые строки
    if 'wow_effect' in gemini:
        result['UF_CRM_1754665062'] = str(gemini.get('wow_effect') or '').strip()  # WOW
    if 'product' in gemini:
        result['UF_CRM_1579102568584'] = str(gemini.get('product') or '').strip()  # Что продает
    if 'task_formulation' in gemini:
        result['UF_CRM_1592909799043'] = str(gemini.get('task_formulation') or '').strip()  # Как сформулирована задача
    if 'ad_budget' in gemini:
        result['UF_CRM_1592910027'] = str(gemini.get('ad_budget') or '').strip()  # Рекламный бюджет

    # 3) Boolean
    if 'is_lpr' in gemini:
        result['UF_CRM_1754651857'] = _map_bool(gemini.get('is_lpr'))  # Вышли на ЛПР
    if 'meeting_scheduled' in gemini:
        result['UF_CRM_1754651891'] = _map_bool(gemini.get('meeting_scheduled'))  # Назначили встречу
    if 'meeting_done' in gemini:
        result['UF_CRM_1754651937'] = _map_bool(gemini.get('meeting_done'))  # Провели встречу

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
        else:
            log.warning(f"Не найден ID для client_type_text: {client_type_text}")

    # Почему некачественный
    bad_reason_text = gemini.get('bad_reason_text')
    if bad_reason_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1555492157080', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, bad_reason_text)
        if enum_id:
            result['UF_CRM_1555492157080'] = enum_id
        else:
            log.warning(f"Не найден ID для bad_reason_text: {bad_reason_text}")

    # Сделали КП?
    kp_done_text = gemini.get('kp_done_text')
    if kp_done_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1754652099', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, kp_done_text)
        if enum_id:
            result['UF_CRM_1754652099'] = enum_id
        else:
            log.warning(f"Не найден ID для kp_done_text: {kp_done_text}")

    # ЛПР подтвержден?
    lpr_confirmed_text = gemini.get('lpr_confirmed_text')
    if lpr_confirmed_text:
        items = (fields_meta.get('result', {})
                 .get('UF_CRM_1755007163632', {})
                 .get('items') or [])
        enum_id = _enum_find_id(items, lpr_confirmed_text)
        if enum_id:
            result['UF_CRM_1755007163632'] = enum_id
        else:
            log.warning(f"Не найден ID для lpr_confirmed_text: {lpr_confirmed_text}")

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

def update_lead_and_create_task(lead_id: str, gemini_struct: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Обновляет лид и создает задачу в одном вызове
    """
    # Обновляем лид
    lead_result = update_lead_with_checklist(lead_id, gemini_struct)
    
    # Создаем задачу
    analysis = gemini_struct.get('analysis', '')
    task_title = "Обработать результаты анализа встречи"
    task_description = f"Лид {lead_id} был обновлен на основе анализа встречи.\n\nКлючевые выводы:\n{analysis[:500]}..."
    
    try:
        task_result = create_task(lead_id, task_title, task_description)
        return lead_result, task_result
    except Exception as e:
        log.error(f"Ошибка создания задачи: {e}")
        return lead_result, {"error": str(e)}

def test_bitrix_connection() -> bool:
    try:
        if not BITRIX_WEBHOOK_URL:
            return False
        _ = get_lead_fields()
        return True
    except Exception as e:
        log.warning(f"Bitrix тест провален: {e}")
        return False
