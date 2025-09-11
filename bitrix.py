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

_BITRIX_FIELDS_CACHE: Optional[Dict[str, Any]] = None


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


def _get_fields_meta(force_refresh: bool = False) -> Dict[str, Any]:
    global _BITRIX_FIELDS_CACHE
    if force_refresh or _BITRIX_FIELDS_CACHE is None:
        try:
            fields_resp = get_lead_fields()
            if isinstance(fields_resp, dict) and 'result' in fields_resp:
                _BITRIX_FIELDS_CACHE = fields_resp['result']
            else:
                _BITRIX_FIELDS_CACHE = {}
        except Exception as e:
            log.exception(f"Не удалось получить описание полей лида: {e}")
            _BITRIX_FIELDS_CACHE = {}
    return _BITRIX_FIELDS_CACHE or {}


def _enum_id_by_label(field_code: str, label_value: Any) -> Optional[str]:
    """Преобразует текстовую метку перечисления в ID для поля field_code."""
    if label_value is None:
        return None
    try:
        if isinstance(label_value, (int, float)):
            return str(int(label_value))
        if isinstance(label_value, str) and label_value.strip().isdigit():
            return label_value.strip()
    except Exception:
        pass

    fields = _get_fields_meta()
    meta = fields.get(field_code)
    if not isinstance(meta, dict):
        return None
    items = meta.get('items') or []
    if not isinstance(items, list):
        return None

    val_norm = str(label_value).strip().lower()
    for it in items:
        if isinstance(it, dict) and str(it.get('VALUE', '')).strip().lower() == val_norm:
            return str(it.get('ID')) if it.get('ID') is not None else None
    for it in items:
        if isinstance(it, dict) and val_norm in str(it.get('VALUE', '')).strip().lower():
            return str(it.get('ID')) if it.get('ID') is not None else None
    return None


def _format_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    try:
        s = str(date_str).strip()
        if len(s) >= 19:
            dt = datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d')
        if len(s) == 10:
            dt = datetime.strptime(s, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
    except Exception:
        return None
    return None


def _format_datetime(dt_str: Optional[str], default_hour: int = 18) -> Optional[str]:
    if not dt_str:
        return None
    try:
        s = str(dt_str).strip()
        if len(s) >= 19:
            dt = datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        if len(s) == 10:
            d = datetime.strptime(s, '%Y-%m-%d')
            d = d.replace(hour=default_hour, minute=0, second=0)
            return d.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None
    return None


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


def create_task(lead_id: str, title: str, description: str, responsible_id: str = None, deadline: Optional[str] = None) -> Dict[str, Any]:
    """Создание задачи в Bitrix24, связанной с лидом"""
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида пустой")

    if not title or not title.strip():
        raise BitrixError("Заголовок задачи пустой")

    # Ответственный и создатель — целые числа
    if not responsible_id:
        responsible_id = BITRIX_RESPONSIBLE_ID
    try:
        responsible_id_int = int(str(responsible_id).strip())
    except Exception:
        raise BitrixError(f"RESPONSIBLE_ID некорректен: {responsible_id}")
    try:
        created_by_int = int(str(BITRIX_CREATED_BY_ID).strip())
    except Exception:
        created_by_int = responsible_id_int

    # Рассчитываем дедлайн
    deadline_date = deadline or (datetime.now() + timedelta(days=BITRIX_TASK_DEADLINE_DAYS)).strftime('%Y-%m-%d %H:%M:%S')

    # Обрезаем описание если слишком длинное
    max_desc_length = 5000
    if len(description) > max_desc_length:
        description = description[:max_desc_length] + "\n\n[Описание обрезано]"

    fields: Dict[str, Any] = {
        'TITLE': f"[Лид {lead_id}] {title}",
        'DESCRIPTION': description,
        'RESPONSIBLE_ID': responsible_id_int,
        'CREATED_BY': created_by_int,
        'DEADLINE': deadline_date,
        'UF_CRM_TASK': [f"L_{str(lead_id).strip()}"]
    }
    # Приоритет: 2 — высокий
    fields['PRIORITY'] = 2
    # GROUP_ID указывать только если валидное положительное число
    try:
        group_id = int('0')
        if group_id > 0:
            fields['GROUP_ID'] = group_id
    except Exception:
        pass

    data = {'fields': fields}

    log.info(f"Создание задачи для лида {lead_id}: {title}")
    resp = _make_bitrix_request('tasks.task.add.json', data)
    log.info(f"Результат создания задачи для лида {lead_id}: {json.dumps(resp, ensure_ascii=False)[:1000]}")
    return resp


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

    result = {'updated': False, 'detail': None, 'task_created': False, 'task_id': None}

    try:
        # 1) Обновим COMMENTS (если есть analysis)
        analysis = gemini_data.get('analysis')
        closing_comment = gemini_data.get('closing_comment')
        if analysis or closing_comment:
            try:
                # Дополняем основной анализ завершающим комментарием, если он есть
                comment_parts: List[str] = []
                if analysis:
                    comment_parts.append(str(analysis))
                if closing_comment:
                    comment_parts.append("\n\nИтог/закрывающий комментарий:\n" + str(closing_comment))

                update_resp = update_lead_comment(lead_id, "\n".join(comment_parts).strip())
                log.debug(f"Обновлен комментарий лида {lead_id}")
            except Exception as e:
                log.exception(f"Не удалось обновить комментарий лид {lead_id}: {e}")

        # 2) Попробуем собрать fields для обновления (простое поведение — маппинг известных ключей)
        fields_payload = {}
        # Перечисляем возможные поля
        mapping = {
            'wow_effect': 'UF_CRM_1754665062',               # string
            'product': 'UF_CRM_1579102568584',                # string
            'task_formulation': 'UF_CRM_1592909799043',       # string
            'ad_budget': 'UF_CRM_1592910027',                 # string
            'is_lpr': 'UF_CRM_1754651857',                    # boolean
            'meeting_scheduled': 'UF_CRM_1754651891',         # boolean
            'meeting_done': 'UF_CRM_1754651937',              # boolean
            'client_type_text': 'UF_CRM_1547738289',          # enumeration
            'bad_reason_text': 'UF_CRM_1555492157080',        # enumeration
            'kp_done_text': 'UF_CRM_1754652099',              # enumeration (Да/Нет)
            'lpr_confirmed_text': 'UF_CRM_1755007163632',     # enumeration (Да/Нет)
            'source_text': 'UF_CRM_1648714327',               # enumeration
            'our_product_text': 'UF_CRM_1741622365',          # enumeration
            'closing_comment': 'UF_CRM_1592911226916',        # string
            'meeting_responsible_id': 'UF_CRM_1756298185',    # employee (user id)
            'meeting_date': 'UF_CRM_1755862426686',           # date
            'planned_meeting_date': 'UF_CRM_1757408917',      # datetime
        }

        fields_meta = _get_fields_meta()
        for k, uf in mapping.items():
            if k in gemini_data and gemini_data.get(k) is not None:
                val = gemini_data.get(k)
                fmeta = fields_meta.get(uf) or {}
                ftype = fmeta.get('type')
                try:
                    if ftype == 'boolean':
                        if isinstance(val, bool):
                            fields_payload[uf] = '1' if val else '0'
                        elif isinstance(val, str):
                            v = val.strip().lower()
                            fields_payload[uf] = '1' if v in ('1', 'true', 'yes', 'да') else '0' if v in ('0', 'false', 'no', 'нет') else None
                    elif ftype == 'enumeration':
                        enum_id = _enum_id_by_label(uf, val)
                        if enum_id:
                            fields_payload[uf] = enum_id
                    elif ftype == 'date':
                        fmt = _format_date(val)
                        if fmt:
                            fields_payload[uf] = fmt
                    elif ftype == 'datetime':
                        fmt = _format_datetime(val)
                        if fmt:
                            fields_payload[uf] = fmt
                    elif ftype == 'employee':
                        if isinstance(val, (int, float)):
                            fields_payload[uf] = int(val)
                        elif isinstance(val, str) and val.strip().isdigit():
                            fields_payload[uf] = int(val.strip())
                    else:
                        fields_payload[uf] = str(val)
                except Exception as e:
                    log.debug(f"Пропущено поле {uf} из-за ошибки преобразования: {e}")

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

        # 3) Логика создания задач по результатам анализа
        try:
            task_responsible = str(gemini_data.get('meeting_responsible_id') or '').strip() or None

            def _format_deadline(dt_str: Optional[str]) -> Optional[str]:
                if not dt_str:
                    return None
                try:
                    # Поддержка форматов YYYY-MM-DD и YYYY-MM-DD HH:MM:SS
                    if len(dt_str.strip()) == 10:
                        parsed = datetime.strptime(dt_str.strip(), '%Y-%m-%d')
                        return parsed.strftime('%Y-%m-%d 18:00:00')
                    parsed = datetime.strptime(dt_str.strip(), '%Y-%m-%d %H:%M:%S')
                    return parsed.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    return None

            meeting_scheduled = gemini_data.get('meeting_scheduled') is True
            meeting_done = gemini_data.get('meeting_done') is True
            is_lpr = gemini_data.get('is_lpr') is True
            planned_meeting_date = gemini_data.get('planned_meeting_date')

            # Если встреча запланирована и есть дата — создаём задачу с соответствующим дедлайном
            if meeting_scheduled and not meeting_done:
                deadline = _format_deadline(planned_meeting_date)
                title = 'Провести запланированную встречу'
                descr_parts: List[str] = [
                    'Автосоздано ботом по итогам анализа встречи.',
                ]
                if planned_meeting_date:
                    descr_parts.append(f"Плановая дата: {planned_meeting_date}")
                if closing_comment:
                    descr_parts.append(f"Комментарий: {closing_comment}")
                description = "\n".join(descr_parts)

                try:
                    task_resp = create_task(
                        lead_id=str(lead_id),
                        title=title,
                        description=description,
                        responsible_id=task_responsible or None,
                        deadline=deadline
                    )
                    result['task_created'] = True
                    if isinstance(task_resp, dict):
                        task_obj = task_resp.get('result') or {}
                        if isinstance(task_obj, dict):
                            task_entity = task_obj.get('task') or task_obj
                            if isinstance(task_entity, dict):
                                task_id = task_entity.get('id') or task_entity.get('task', {}).get('id')
                                result['task_id'] = str(task_id) if task_id else None
                except Exception as e:
                    log.exception(f"Не удалось создать задачу для лида {lead_id}: {e}")

            # Если ЛПР найден, но встреча не назначена — создаём задачу назначить встречу
            elif is_lpr and not meeting_scheduled and not meeting_done:
                title = 'Назначить встречу с ЛПР'
                description = 'Автозадача: назначить встречу с ЛПР по итогам анализа. '
                if closing_comment:
                    description += f"\nКомментарий: {closing_comment}"
                try:
                    task_resp = create_task(
                        lead_id=str(lead_id),
                        title=title,
                        description=description,
                        responsible_id=task_responsible or None
                    )
                    result['task_created'] = True
                    if isinstance(task_resp, dict):
                        task_obj = task_resp.get('result') or {}
                        if isinstance(task_obj, dict):
                            task_entity = task_obj.get('task') or task_obj
                            if isinstance(task_entity, dict):
                                task_id = task_entity.get('id') or task_entity.get('task', {}).get('id')
                                result['task_id'] = str(task_id) if task_id else None
                except Exception as e:
                    log.exception(f"Не удалось создать задачу 'Назначить встречу' для лида {lead_id}: {e}")
        except Exception as e:
            log.exception(f"Ошибка логики создания задач для лида {lead_id}: {e}")

    except Exception as e:
        log.exception(f"Ошибка в update_lead_comprehensive: {e}")
        raise

    return result
