import os
import requests
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import urljoin
from datetime import datetime, timedelta
import json

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
    """Универсальный метод для запросов к Bitrix24"""
    if not BITRIX_WEBHOOK_URL:
        raise BitrixError("BITRIX_WEBHOOK_URL не настроен")

    url = urljoin(BITRIX_WEBHOOK_URL.rstrip('/') + '/', method)
    log.info(f"Bitrix request to {method}: {json.dumps(data, ensure_ascii=False)[:500]}")

    last_exc = None
    for attempt in range(retries):
        try:
            response = requests.post(
                url,
                json=data,
                timeout=REQUEST_TIMEOUT,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
            response.raise_for_status()
            result = response.json()

            log.info(f"Bitrix response for {method}: {json.dumps(result, ensure_ascii=False)[:1000]}")

            # Bitrix may return 'result' or 'error'
            if isinstance(result, dict) and result.get('error'):
                error_msg = result.get('error_description', result.get('error', 'Неизвестная ошибка Bitrix API'))
                log.error(f"Bitrix API error in {method}: {error_msg}")
                raise BitrixError(f"{method}: {error_msg}")

            return result
        except requests.exceptions.Timeout:
            last_exc = BitrixError(f"Таймаут запроса к Bitrix ({method})")
            log.warning(f"Timeout для {method} (попытка {attempt+1}/{retries})")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.ConnectionError:
            last_exc = BitrixError(f"Ошибка соединения с Bitrix ({method})")
            log.warning(f"Connection error для {method} (попытка {attempt+1}/{retries})")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            last_exc = BitrixError(f"HTTP ошибка Bitrix ({method}): {e}")
            log.warning(f"HTTP ошибка для {method} (попытка {attempt+1}/{retries}): {e}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            last_exc = BitrixError(f"Неожиданная ошибка Bitrix ({method}): {e}")
            log.error(f"Неожиданная ошибка для {method}: {e}")
            time.sleep(RETRY_DELAY)

    raise last_exc


def get_lead_fields() -> Dict[str, Any]:
    """Получение описания полей лида"""
    return _make_bitrix_request('crm.lead.fields.json', {})


def get_lead_info(lead_id: str) -> Dict[str, Any]:
    """Получение информации о лиде"""
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")

    data = {
        'id': str(lead_id).strip()
    }
    return _make_bitrix_request('crm.lead.get.json', data)


def update_lead_comment(lead_id: str, comment: str) -> Dict[str, Any]:
    """Обновление комментария лида"""
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")
    if not comment or not comment.strip():
        raise BitrixError("Комментарий пустой")

    # Обрезаем комментарий если слишком длинный
    if len(comment) > MAX_COMMENT_LENGTH:
        comment = comment[:MAX_COMMENT_LENGTH] + "\n\n[Комментарий обрезан из-за ограничений длины]"
        log.warning(f"Комментарий для лида {lead_id} обрезан до {MAX_COMMENT_LENGTH} символов")

    data = {
        'id': str(lead_id).strip(),
        'fields': {
            'COMMENTS': comment.strip()
        },
        'params': {
            'REGISTER_SONET_EVENT': 'Y'
        }
    }
    return _make_bitrix_request('crm.lead.update.json', data)


def create_task(lead_id: str, title: str, description: str, responsible_id: str = None) -> Dict[str, Any]:
    """Создание задачи в Bitrix24, связанной с лидом"""
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")

    if not title or not title.strip():
        raise BitrixError("Заголовок задачи пустой")

    if not responsible_id:
        responsible_id = BITRIX_RESPONSIBLE_ID

    # Рассчитываем дедлайн
    deadline_date = (datetime.now() + timedelta(days=BITRIX_TASK_DEADLINE_DAYS)).strftime('%Y-%m-%d %H:%M:%S')

    # Обрезаем описание если слишком длинное
    max_desc_length = 5000
    if len(description) > max_desc_length:
        description = description[:max_desc_length] + "\n\n[Описание обрезано]"

    data = {
        'fields': {
            'TITLE': f"[Лид {lead_id}] {title}",
            'DESCRIPTION': description,
            'RESPONSIBLE_ID': responsible_id,
            'CREATED_BY': BITRIX_CREATED_BY_ID,
            'DEADLINE': deadline_date,
            'UF_CRM_TASK': [f'L_{lead_id.strip()}'],  # Связываем с лидом
            'PRIORITY': '1',  # Высокий приоритет
            'GROUP_ID': '0'   # Общая группа
        }
    }

    log.info(f"Создание задачи для лида {lead_id}: {title}")
    return _make_bitrix_request('tasks.task.add.json', data)


# ---- Дополнительные функции-обёртки, ожидаемые main.py ----

def test_bitrix_connection() -> bool:
    """Пассивный тест подключения: пытается получить описание полей лида"""
    try:
        if not BITRIX_WEBHOOK_URL:
            log.warning("BITRIX_WEBHOOK_URL не задан — тест подключения пропущен")
            return False
        resp = get_lead_fields()
        # Если ответ содержит 'result' или структуру полей — считаем OK
        if isinstance(resp, dict):
            return True
        return False
    except Exception as e:
        log.exception(f"Ошибка теста Bitrix: {e}")
        return False


def get_bitrix_info() -> Dict[str, Any]:
    """Возвращает информацию о конфигурации Bitrix"""
    info = {
        'webhook_configured': bool(BITRIX_WEBHOOK_URL),
        'connection_test': False,
        'available_fields': 0,
        'custom_fields': 0
    }
    try:
        if not BITRIX_WEBHOOK_URL:
            return info
        fields = get_lead_fields()
        if isinstance(fields, dict) and 'result' in fields:
            items = fields.get('result', {})
            info['available_fields'] = len(items)
            # custom fields — простой подсчёт по UF_CRM_ ключам
            info['custom_fields'] = len([k for k in items.keys() if k.startswith('UF_')])
            info['connection_test'] = True
        else:
            info['connection_test'] = True  # получили ответ — пусть будет true
    except Exception:
        log.exception("Не удалось получить поля лида из Bitrix")
        info['connection_test'] = False

    return info


def update_lead_comprehensive(lead_id: str, gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Удобная обёртка для обновления лида: добавляет комментарий с анализом и обновляет кастомные поля.
    gemini_data — структура, возвращаемая из gemini_client.analyze_transcript_structured (словарь).
    """
    if not lead_id:
        raise BitrixError("lead_id обязателен")

    result = {'updated': False, 'detail': None}

    try:
        # 1) Обновим COMMENTS (если есть analysis)
        analysis = gemini_data.get('analysis')
        if analysis:
            try:
                update_resp = update_lead_comment(lead_id, analysis)
                log.debug(f"Обновлен комментарий лида {lead_id}")
            except Exception as e:
                log.exception(f"Не удалось обновить комментарий лид {lead_id}: {e}")

        # 2) Попробуем собрать fields для обновления (простое поведение — маппинг известных ключей)
        fields_payload = {}
        # Перечисляем возможные поля, которые могут присутствовать и соответствуют UF_*
        mapping = {
            'wow_effect': 'UF_CRM_1754665062',
            'product': 'UF_CRM_1579102568584',
            'task_formulation': 'UF_CRM_1592909799043',
            'ad_budget': 'UF_CRM_1592910027',
            'is_lpr': 'UF_CRM_1754651857',
            'meeting_scheduled': 'UF_CRM_1754651891',
            'meeting_done': 'UF_CRM_1754651937',
            'client_type_text': 'UF_CRM_1547738289',
            'bad_reason_text': 'UF_CRM_1555492157080',
            'kp_done_text': 'UF_CRM_1754652099',
            'lpr_confirmed_text': 'UF_CRM_1755007163632',
            'source_text': 'UF_CRM_1648714327',
            'our_product_text': 'UF_CRM_1741622365',
        }

        for k, uf in mapping.items():
            if k in gemini_data and gemini_data.get(k) is not None:
                val = gemini_data.get(k)
                # Bool -> '1'/'0' if necessary for Bitrix
                if isinstance(val, bool):
                    fields_payload[uf] = '1' if val else '0'
                else:
                    fields_payload[uf] = str(val)

        if fields_payload:
            data = {
                'id': str(lead_id).strip(),
                'fields': fields_payload,
                'params': {
                    'REGISTER_SONET_EVENT': 'Y'
                }
            }
            try:
                resp = _make_bitrix_request('crm.lead.update.json', data)
                result['updated'] = True
                result['detail'] = resp
                log.info(f"Lead {lead_id} updated with fields: {list(fields_payload.keys())}")
            except Exception as e:
                log.exception(f"Ошибка при обновлении полей лида {lead_id}: {e}")

    except Exception as e:
        log.exception(f"Ошибка в update_lead_comprehensive: {e}")
        raise

    return result
