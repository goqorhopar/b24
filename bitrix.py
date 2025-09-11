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
            
            if 'error' in result:
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

def _map_bool(value: Any) -> str:
    """Преобразование boolean в строку для Bitrix"""
    if value is None:
        return '0'
    return '1' if bool(value) else '0'

def _normalize_text(s: Optional[str]) -> str:
    """Нормализация текста для поиска"""
    if not s:
        return ""
    return str(s).strip().lower()

def _enum_find_id(items: List[Dict[str, Any]], text_value: str) -> Optional[str]:
    """Поиск ID enum по тексту (VALUE), регистронезависимо"""
    if not text_value or not items:
        return None
        
    target = _normalize_text(text_value)
    
    # Точное совпадение
    for item in items:
        val = _normalize_text(item.get('VALUE', ''))
        if val and val == target:
            log.debug(f"Найдено точное совпадение для '{text_value}': ID={item.get('ID')}")
            return str(item.get('ID'))
    
    # Поиск по вхождению
    for item in items:
        val = _normalize_text(item.get('VALUE', ''))
        if val and target in val:
            log.debug(f"Найдено частичное совпадение для '{text_value}': ID={item.get('ID')}, VALUE='{item.get('VALUE')}'")
            return str(item.get('ID'))
    
    # Поиск в обратную сторону
    for item in items:
        val = _normalize_text(item.get('VALUE', ''))
        if val and val in target:
            log.debug(f"Найдено обратное совпадение для '{text_value}': ID={item.get('ID')}, VALUE='{item.get('VALUE')}'")
            return str(item.get('ID'))
    
    log.warning(f"Не найден ID для enum значения '{text_value}' среди {len(items)} вариантов")
    return None

def build_fields_from_gemini(gemini_data: Dict[str, Any], fields_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Построение полей для обновления лида на основе данных от Gemini
    """
    result = {}
    fields_result = fields_meta.get('result', {})
    
    log.info(f"Обработка данных Gemini: {json.dumps(gemini_data, ensure_ascii=False)}")
    
    # 1. Анализ встречи (COMMENTS)
    analysis = str(gemini_data.get('analysis', '')).strip()
    if analysis:
        if len(analysis) > MAX_COMMENT_LENGTH:
            analysis = analysis[:MAX_COMMENT_LENGTH] + "\n\n[Анализ обрезан]"
        result['COMMENTS'] = analysis
        log.debug("Добавлен анализ в COMMENTS")
    
    # 2. WOW-эффект (UF_CRM_1754665062)
    wow_effect = str(gemini_data.get('wow_effect', '')).strip()
    if wow_effect:
        result['UF_CRM_1754665062'] = wow_effect
        log.debug(f"Добавлен WOW-эффект: {wow_effect[:100]}")
    
    # 3. Что продает клиент (UF_CRM_1579102568584)
    product = str(gemini_data.get('product', '')).strip()
    if product:
        result['UF_CRM_1579102568584'] = product
        log.debug(f"Добавлен продукт клиента: {product}")
    
    # 4. Как сформулирована задача (UF_CRM_1592909799043)
    task_formulation = str(gemini_data.get('task_formulation', '')).strip()
    if task_formulation:
        result['UF_CRM_1592909799043'] = task_formulation
        log.debug(f"Добавлена формулировка задачи: {task_formulation}")
    
    # 5. Рекламный бюджет (UF_CRM_1592910027)
    ad_budget = str(gemini_data.get('ad_budget', '')).strip()
    if ad_budget:
        result['UF_CRM_1592910027'] = ad_budget
        log.debug(f"Добавлен рекламный бюджет: {ad_budget}")
    
    # 6. Boolean поля - точное сопоставление с документацией
    
    # Вышли на ЛПР? (UF_CRM_1754651857)
    if 'is_lpr' in gemini_data:
        result['UF_CRM_1754651857'] = _map_bool(gemini_data.get('is_lpr'))
        log.debug(f"Установлено 'Вышли на ЛПР': {result['UF_CRM_1754651857']}")
    
    # Назначили встречу? (UF_CRM_1754651891)
    if 'meeting_scheduled' in gemini_data:
        result['UF_CRM_1754651891'] = _map_bool(gemini_data.get('meeting_scheduled'))
        log.debug(f"Установлено 'Назначили встречу': {result['UF_CRM_1754651891']}")
    
    # Провели встречу? (UF_CRM_1754651937)
    if 'meeting_done' in gemini_data:
        result['UF_CRM_1754651937'] = _map_bool(gemini_data.get('meeting_done'))
        log.debug(f"Установлено 'Провели встречу': {result['UF_CRM_1754651937']}")
    
    # 7. Enum поля с поиском ID по значению
    
    # ТИП КЛИЕНТА (UF_CRM_1547738289)
    client_type_text = gemini_data.get('client_type_text')
    if client_type_text:
        items = fields_result.get('UF_CRM_1547738289', {}).get('items', [])
        enum_id = _enum_find_id(items, client_type_text)
        if enum_id:
            result['UF_CRM_1547738289'] = enum_id
            log.debug(f"Установлен тип клиента: {client_type_text} -> ID {enum_id}")
        else:
            log.warning(f"Не найден ID для типа клиента: {client_type_text}")
            log.debug(f"Доступные типы клиентов: {[item.get('VALUE') for item in items]}")
    
    # Почему некачественный (UF_CRM_1555492157080)
    bad_reason_text = gemini_data.get('bad_reason_text')
    if bad_reason_text:
        items = fields_result.get('UF_CRM_1555492157080', {}).get('items', [])
        enum_id = _enum_find_id(items, bad_reason_text)
        if enum_id:
            result['UF_CRM_1555492157080'] = enum_id
            log.debug(f"Установлена причина некачественности: {bad_reason_text} -> ID {enum_id}")
        else:
            log.warning(f"Не найден ID для причины некачественности: {bad_reason_text}")
            log.debug(f"Доступные причины: {[item.get('VALUE') for item in items]}")
    
    # Сделали КП? (UF_CRM_1754652099)
    kp_done_text = gemini_data.get('kp_done_text')
    if kp_done_text:
        items = fields_result.get('UF_CRM_1754652099', {}).get('items', [])
        enum_id = _enum_find_id(items, kp_done_text)
        if enum_id:
            result['UF_CRM_1754652099'] = enum_id
            log.debug(f"Установлено КП: {kp_done_text} -> ID {enum_id}")
        else:
            log.warning(f"Не найден ID для КП: {kp_done_text}")
            log.debug(f"Доступные варианты КП: {[item.get('VALUE') for item in items]}")
    
    # ЛПР подтвержден? (UF_CRM_1755007163632)
    lpr_confirmed_text = gemini_data.get('lpr_confirmed_text')
    if lpr_confirmed_text:
        items = fields_result.get('UF_CRM_1755007163632', {}).get('items', [])
        enum_id = _enum_find_id(items, lpr_confirmed_text)
        if enum_id:
            result['UF_CRM_1755007163632'] = enum_id
            log.debug(f"Установлено подтверждение ЛПР: {lpr_confirmed_text} -> ID {enum_id}")
        else:
            log.warning(f"Не найден ID для подтверждения ЛПР: {lpr_confirmed_text}")
            log.debug(f"Доступные варианты ЛПР: {[item.get('VALUE') for item in items]}")
    
    # Откуда узнали о нас (UF_CRM_1648714327)
    source_text = gemini_data.get('source_text')
    if source_text:
        items = fields_result.get('UF_CRM_1648714327', {}).get('items', [])
        enum_id = _enum_find_id(items, source_text)
        if enum_id:
            result['UF_CRM_1648714327'] = enum_id
            log.debug(f"Установлен источник: {source_text} -> ID {enum_id}")
    
    # Что мы продаем (UF_CRM_1741622365)
    our_product_text = gemini_data.get('our_product_text')
    if our_product_text:
        items = fields_result.get('UF_CRM_1741622365', {}).get('items', [])
        enum_id = _enum_find_id(items, our_product_text)
        if enum_id:
            result['UF_CRM_1741622365'] = enum_id
            log.debug(f"Установлен наш продукт: {our_product_text} -> ID {enum_id}")
    
    # 8. Дата встречи (UF_CRM_1755862426686)
    meeting_date = gemini_data.get('meeting_date')
    if meeting_date:
        try:
            # Пытаемся парсить дату в разных форматах
            if isinstance(meeting_date, str):
                # Пробуем разные форматы
                date_formats = ['%Y-%m-%d', '%d.%m.%Y', '%d-%m-%Y', '%Y.%m.%d']
                parsed_date = None
                
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(meeting_date, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    result['UF_CRM_1755862426686'] = parsed_date.strftime('%Y-%m-%d')
                    log.debug(f"Установлена дата встречи: {meeting_date}")
        except Exception as e:
            log.warning(f"Не удалось парсить дату встречи '{meeting_date}': {e}")
    
    # 9. Дополнительные поля
    
    # Комментарий по закрытию (UF_CRM_1592911226916)
    closing_comment = str(gemini_data.get('closing_comment', '')).strip()
    if closing_comment:
        result['UF_CRM_1592911226916'] = closing_comment
        log.debug(f"Добавлен комментарий по закрытию: {closing_comment[:100]}")
    
    # План дата встречи (UF_CRM_1757408917)
    planned_meeting_date = gemini_data.get('planned_meeting_date')
    if planned_meeting_date:
        try:
            if isinstance(planned_meeting_date, str):
                # Пробуем парсить как datetime
                datetime_formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']
                parsed_datetime = None
                
                for fmt in datetime_formats:
                    try:
                        parsed_datetime = datetime.strptime(planned_meeting_date, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_datetime:
                    result['UF_CRM_1757408917'] = parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    log.debug(f"Установлена план дата встречи: {planned_meeting_date}")
        except Exception as e:
            log.warning(f"Не удалось парсить план дату встречи '{planned_meeting_date}': {e}")
    
    # Устанавливаем ответственного за встречу (UF_CRM_1756298185)
    meeting_responsible = gemini_data.get('meeting_responsible_id')
    if meeting_responsible:
        result['UF_CRM_1756298185'] = str(meeting_responsible)
        log.debug(f"Установлен ответственный за встречу: {meeting_responsible}")
    
    log.info(f"Сформированы поля для обновления лида: {json.dumps(result, ensure_ascii=False)}")
    return result

def update_lead_with_checklist(lead_id: str, gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Обновление лида в Bitrix24 на основе данных анализа встречи
    """
    if not lead_id or not str(lead_id).strip():
        raise BitrixError("ID лида пустой или некорректный")
    
    if not gemini_data or not isinstance(gemini_data, dict):
        raise BitrixError("Данные анализа пустые или некорректные")
    
    lead_id = str(lead_id).strip()
    
    try:
        # 1. Получаем мету полей
        log.info(f"Получение мета-информации о полях лида...")
        fields_meta = get_lead_fields()
        
        # 2. Строим поля для обновления
        log.info(f"Построение полей для обновления лида {lead_id}")
        update_fields = build_fields_from_gemini(gemini_data, fields_meta)
        
        if not update_fields:
            raise BitrixError("Не удалось сформировать поля для обновления лида")
        
        # 3. Обновляем лид
        log.info(f"Обновление лида {lead_id} с полями: {list(update_fields.keys())}")
        
        data = {
            'id': lead_id,
            'fields': update_fields,
            'params': {
                'REGISTER_SONET_EVENT': 'Y'
            }
        }
        
        result = _make_bitrix_request('crm.lead.update.json', data)
        
        if result.get('result') is True:
            log.info(f"Лид {lead_id} успешно обновлен")
        else:
            log.warning(f"Неожиданный результат обновления лида {lead_id}: {result}")
        
        return result
        
    except BitrixError:
        raise
    except Exception as e:
        error_msg = f"Ошибка обновления лида {lead_id}: {e}"
        log.error(error_msg)
        raise BitrixError(error_msg)

def update_lead_and_create_task(lead_id: str, gemini_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Обновление лида и создание задачи в одной операции
    """
    lead_result = {}
    task_result = {}
    
    try:
        # 1. Обновляем лид
        log.info(f"Начинаем обновление лида {lead_id}")
        lead_result = update_lead_with_checklist(lead_id, gemini_data)
        
        # 2. Создаем задачу
        log.info(f"Создание задачи для лида {lead_id}")
        
        analysis = str(gemini_data.get('analysis', 'Анализ встречи выполнен'))
        
        # Определяем приоритет задачи на основе данных
        is_lpr = gemini_data.get('is_lpr', False)
        meeting_done = gemini_data.get('meeting_done', False)
        
        if is_lpr and meeting_done:
            task_title = "🔥 ГОРЯЧИЙ ЛИДЫ - Обработать результаты встречи с ЛПР"
        elif is_lpr:
            task_title = "⚡ Работа с ЛПР - Провести встречу"
        elif meeting_done:
            task_title = "📋 Обработать результаты встречи"
        else:
            task_title = "📞 Продолжить работу с лидом"
        
        # Формируем детальное описание задачи
        task_description = f"""Лид {lead_id} обновлен на основе анализа встречи.

🎯 АНАЛИЗ ВСТРЕЧИ:
{analysis[:1000]}

📊 КЛЮЧЕВЫЕ ДАННЫЕ:
• Вышли на ЛПР: {'✅ Да' if is_lpr else '❌ Нет'}
• Встреча проведена: {'✅ Да' if meeting_done else '❌ Нет'}
• КП сделано: {gemini_data.get('kp_done_text', 'Не указано')}
"""
        
        # Добавляем WOW-эффект если есть
        wow_effect = gemini_data.get('wow_effect')
        if wow_effect:
            task_description += f"\n💡 WOW-ЭФФЕКТ:\n{wow_effect}"
        
        # Добавляем информацию о продукте клиента
        client_product = gemini_data.get('product')
        if client_product:
            task_description += f"\n🏢 ПРОДУКТ КЛИЕНТА:\n{client_product}"
        
        # Добавляем бюджет
        budget = gemini_data.get('ad_budget')
        if budget:
            task_description += f"\n💰 РЕКЛАМНЫЙ БЮДЖЕТ:\n{budget}"
        
        task_description += f"\n\n⏰ Создано автоматически: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        try:
            task_result = create_task(lead_id, task_title, task_description)
            log.info(f"Задача создана для лида {lead_id}: ID {task_result.get('result', {}).get('task', {}).get('id', 'неизвестно')}")
        except Exception as te:
            log.error(f"Ошибка создания задачи для лида {lead_id}: {te}")
            task_result = {"error": str(te)}
        
        return lead_result, task_result
        
    except Exception as e:
        log.error(f"Ошибка в update_lead_and_create_task для лида {lead_id}: {e}")
        return lead_result, {"error": str(e)}

def get_lead_status_info(lead_id: str) -> Dict[str, Any]:
    """Получение информации о статусе лида"""
    try:
        lead_info = get_lead_info(lead_id)
        lead_data = lead_info.get('result', {})
        
        status_id = lead_data.get('STATUS_ID', '')
        status_semantic = lead_data.get('STATUS_SEMANTIC_ID', '')
        
        return {
            'status_id': status_id,
            'status_semantic': status_semantic,
            'title': lead_data.get('TITLE', ''),
            'opportunity': lead_data.get('OPPORTUNITY', ''),
            'assigned_by_id': lead_data.get('ASSIGNED_BY_ID', ''),
            'created_date': lead_data.get('DATE_CREATE', ''),
            'modified_date': lead_data.get('DATE_MODIFY', '')
        }
    except Exception as e:
        log.error(f"Ошибка получения статуса лида {lead_id}: {e}")
        return {'error': str(e)}

def add_lead_timeline_comment(lead_id: str, comment: str) -> Dict[str, Any]:
    """Добавление комментария в ленту лида"""
    try:
        data = {
            'fields': {
                'ENTITY_ID': lead_id,
                'ENTITY_TYPE': 'lead',
                'COMMENT': comment,
                'AUTHOR_ID': BITRIX_CREATED_BY_ID
            }
        }
        return _make_bitrix_request('crm.timeline.comment.add.json', data)
    except Exception as e:
        log.error(f"Ошибка добавления комментария в ленту лида {lead_id}: {e}")
        raise BitrixError(f"Не удалось добавить комментарий в ленту: {e}")

def test_bitrix_connection() -> bool:
    """Тестирование соединения с Bitrix24"""
    try:
        if not BITRIX_WEBHOOK_URL:
            log.warning("BITRIX_WEBHOOK_URL не настроен")
            return False
        
        # Пробуем получить поля лида
        fields = get_lead_fields()
        
        if 'result' in fields and isinstance(fields['result'], dict):
            log.info("✅ Соединение с Bitrix24 работает")
            return True
        else:
            log.warning("❌ Неожиданный ответ от Bitrix24")
            return False
            
    except Exception as e:
        log.warning(f"❌ Тест соединения с Bitrix24 провален: {e}")
        return False

def get_bitrix_info() -> Dict[str, Any]:
    """Получение информации о конфигурации Bitrix24"""
    info = {
        'webhook_configured': bool(BITRIX_WEBHOOK_URL),
        'webhook_url_preview': BITRIX_WEBHOOK_URL[:50] + '...' if BITRIX_WEBHOOK_URL else None,
        'responsible_id': BITRIX_RESPONSIBLE_ID,
        'created_by_id': BITRIX_CREATED_BY_ID,
        'task_deadline_days': BITRIX_TASK_DEADLINE_DAYS,
        'connection_test': test_bitrix_connection()
    }
    
    try:
        if info['connection_test']:
            # Получаем дополнительную информацию
            fields = get_lead_fields()
            info['available_fields'] = len(fields.get('result', {}))
            info['custom_fields'] = len([k for k in fields.get('result', {}).keys() if k.startswith('UF_')])
    except:
        pass
    
    return info

def validate_lead_data(gemini_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Валидация данных для обновления лида"""
    errors = []
    
    if not isinstance(gemini_data, dict):
        errors.append("Данные должны быть словарем")
        return False, errors
    
    # Проверяем наличие анализа
    if not gemini_data.get('analysis'):
        errors.append("Отсутствует анализ встречи")
    
    # Проверяем корректность boolean полей
    bool_fields = ['is_lpr', 'meeting_scheduled', 'meeting_done']
    for field in bool_fields:
        if field in gemini_data:
            value = gemini_data[field]
            if value is not None and not isinstance(value, bool):
                errors.append(f"Поле {field} должно быть boolean")
    
    # Проверяем строковые поля
    string_fields = ['wow_effect', 'product', 'task_formulation', 'ad_budget']
    for field in string_fields:
        if field in gemini_data:
            value = gemini_data[field]
            if value is not None and not isinstance(value, str):
                errors.append(f"Поле {field} должно быть строкой")
    
    return len(errors) == 0, errors

def backup_lead_data(lead_id: str) -> Dict[str, Any]:
    """Создание резервной копии данных лида перед изменением"""
    try:
        lead_info = get_lead_info(lead_id)
        backup = {
            'lead_id': lead_id,
            'backup_date': datetime.now().isoformat(),
            'original_data': lead_info.get('result', {})
        }
        
        # Сохраняем важные поля
        important_fields = [
            'TITLE', 'COMMENTS', 'STATUS_ID', 'OPPORTUNITY',
            'UF_CRM_1754665062', 'UF_CRM_1579102568584', 'UF_CRM_1592909799043',
            'UF_CRM_1592910027', 'UF_CRM_1754651857', 'UF_CRM_1754651891', 
            'UF_CRM_1754651937', 'UF_CRM_1547738289', 'UF_CRM_1555492157080',
            'UF_CRM_1754652099', 'UF_CRM_1755007163632'
        ]
        
        backup['important_fields'] = {
            field: backup['original_data'].get(field) 
            for field in important_fields 
            if field in backup['original_data']
        }
        
        return backup
    except Exception as e:
        log.error(f"Ошибка создания резервной копии лида {lead_id}: {e}")
        return {'error': str(e)}

def get_enum_values(field_name: str) -> List[Dict[str, Any]]:
    """Получение всех возможных значений для enum поля"""
    try:
        fields_meta = get_lead_fields()
        field_info = fields_meta.get('result', {}).get(field_name, {})
        return field_info.get('items', [])
    except Exception as e:
        log.error(f"Ошибка получения enum значений для поля {field_name}: {e}")
        return []

def create_advanced_task(lead_id: str, gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """Создание расширенной задачи с учетом всех данных анализа"""
    try:
        # Определяем тип и приоритет задачи
        is_lpr = gemini_data.get('is_lpr', False)
        meeting_done = gemini_data.get('meeting_done', False)
        kp_done = gemini_data.get('kp_done_text', '').lower() in ['да', 'yes', 'готово']
        
        # Базовые параметры
        priority = '2'  # Обычный
        title_prefix = "📋"
        
        # Определяем приоритет и префикс
        if is_lpr and meeting_done and kp_done:
            priority = '1'  # Высокий
            title_prefix = "🔥🔥🔥"
            base_title = "ГОРЯЧИЙ ЛИД - Финализировать сделку"
        elif is_lpr and meeting_done:
            priority = '1'  # Высокий  
            title_prefix = "🔥🔥"
            base_title = "ГОРЯЧИЙ ЛИД - Подготовить КП"
        elif is_lpr:
            priority = '1'  # Высокий
            title_prefix = "🔥"
            base_title = "ЛПР найден - Назначить встречу"
        elif meeting_done:
            priority = '2'  # Обычный
            title_prefix = "📞"
            base_title = "Обработать результаты встречи"
        else:
            priority = '2'  # Обычный
            title_prefix = "📋"
            base_title = "Продолжить работу с лидом"
        
        # Формируем заголовок
        task_title = f"{title_prefix} {base_title}"
        
        # Детальное описание
        description_parts = []
        
        # Основная информация
        description_parts.append(f"🎯 ЛИДА: {lead_id}")
        description_parts.append(f"📊 СТАТУС ОБРАБОТКИ: Анализ встречи завершен")
        description_parts.append("")
        
        # Анализ
        analysis = gemini_data.get('analysis', '')
        if analysis:
            description_parts.append("📝 АНАЛИЗ ВСТРЕЧИ:")
            description_parts.append(analysis[:800] + ("..." if len(analysis) > 800 else ""))
            description_parts.append("")
        
        # Ключевые индикаторы
        description_parts.append("🎯 КЛЮЧЕВЫЕ ИНДИКАТОРЫ:")
        description_parts.append(f"• Вышли на ЛПР: {'✅ ДА' if is_lpr else '❌ НЕТ'}")
        description_parts.append(f"• Встреча проведена: {'✅ ДА' if meeting_done else '❌ НЕТ'}")
        
        kp_status = gemini_data.get('kp_done_text', 'Не указано')
        description_parts.append(f"• КП подготовлено: {kp_status}")
        
        lpr_confirmed = gemini_data.get('lpr_confirmed_text', 'Не указано')
        description_parts.append(f"• ЛПР подтвержден: {lpr_confirmed}")
        description_parts.append("")
        
        # Информация о клиенте
        client_type = gemini_data.get('client_type_text')
        if client_type:
            description_parts.append(f"👤 ТИП КЛИЕНТА: {client_type}")
        
        product = gemini_data.get('product')
        if product:
            description_parts.append(f"🏢 ПРОДУКТ КЛИЕНТА: {product}")
        
        task_formulation = gemini_data.get('task_formulation')
        if task_formulation:
            description_parts.append(f"📋 ЗАДАЧА КЛИЕНТА: {task_formulation}")
        
        budget = gemini_data.get('ad_budget')
        if budget:
            description_parts.append(f"💰 РЕКЛАМНЫЙ БЮДЖЕТ: {budget}")
        
        # WOW-эффект
        wow_effect = gemini_data.get('wow_effect')
        if wow_effect:
            description_parts.append("")
            description_parts.append("💡 WOW-ЭФФЕКТ:")
            description_parts.append(wow_effect)
        
        # Рекомендуемые действия
        description_parts.append("")
        description_parts.append("🎯 РЕКОМЕНДУЕМЫЕ ДЕЙСТВИЯ:")
        
        if is_lpr and meeting_done and kp_done:
            description_parts.append("• Связаться с клиентом для обсуждения деталей сделки")
            description_parts.append("• Подготовить договор")
            description_parts.append("• Согласовать сроки и условия")
        elif is_lpr and meeting_done:
            description_parts.append("• Подготовить и отправить коммерческое предложение")
            description_parts.append("• Назначить следующую встречу для обсуждения КП")
        elif is_lpr:
            description_parts.append("• Назначить встречу с ЛПР")
            description_parts.append("• Подготовить презентацию")
        elif meeting_done:
            description_parts.append("• Проанализировать результаты встречи")
            description_parts.append("• Определить следующие шаги")
        else:
            description_parts.append("• Связаться с клиентом")
            description_parts.append("• Выяснить потребности и бюджет")
        
        description_parts.append("")
        description_parts.append(f"⏰ Задача создана: {datetime.now().strftime('%d.%m.%Y в %H:%M')}")
        description_parts.append("🤖 Создано автоматически системой анализа встреч")
        
        full_description = "\n".join(description_parts)
        
        # Расчет дедлайна в зависимости от приоритета
        deadline_days = 1 if priority == '1' else BITRIX_TASK_DEADLINE_DAYS
        deadline = (datetime.now() + timedelta(days=deadline_days)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Создание задачи
        task_data = {
            'fields': {
                'TITLE': f"[Лид {lead_id}] {task_title}",
                'DESCRIPTION': full_description,
                'RESPONSIBLE_ID': BITRIX_RESPONSIBLE_ID,
                'CREATED_BY': BITRIX_CREATED_BY_ID,
                'DEADLINE': deadline,
                'PRIORITY': priority,
                'UF_CRM_TASK': [f'L_{lead_id}'],
                'GROUP_ID': '0',
                'ALLOW_CHANGE_DEADLINE': 'Y',
                'MATCH_WORK_TIME': 'N'
            }
        }
        
        # Добавляем наблюдателей если есть
        if gemini_data.get('meeting_responsible_id'):
            task_data['fields']['AUDITORS'] = [str(gemini_data['meeting_responsible_id'])]
        
        result = _make_bitrix_request('tasks.task.add.json', task_data)
        
        if result.get('result'):
            task_id = result['result'].get('task', {}).get('id')
            log.info(f"Создана расширенная задача {task_id} для лида {lead_id}")
        
        return result
        
    except Exception as e:
        log.error(f"Ошибка создания расширенной задачи для лида {lead_id}: {e}")
        raise BitrixError(f"Не удалось создать задачу: {e}")

def update_lead_comprehensive(lead_id: str, gemini_data: Dict[str, Any], create_task: bool = True, backup: bool = True) -> Dict[str, Any]:
    """
    Полное обновление лида с расширенными возможностями
    """
    operation_result = {
        'lead_update': {},
        'task_creation': {},
        'backup': {},
        'validation': {},
        'errors': [],
        'warnings': []
    }
    
    try:
        # 1. Валидация данных
        is_valid, validation_errors = validate_lead_data(gemini_data)
        operation_result['validation'] = {
            'is_valid': is_valid,
            'errors': validation_errors
        }
        
        if not is_valid:
            operation_result['errors'].extend(validation_errors)
            return operation_result
        
        # 2. Создание резервной копии
        if backup:
            try:
                backup_data = backup_lead_data(lead_id)
                operation_result['backup'] = backup_data
                if 'error' not in backup_data:
                    log.info(f"Создана резервная копия лида {lead_id}")
            except Exception as e:
                operation_result['warnings'].append(f"Не удалось создать резервную копию: {e}")
        
        # 3. Обновление лида
        try:
            lead_result = update_lead_with_checklist(lead_id, gemini_data)
            operation_result['lead_update'] = lead_result
            
            if lead_result.get('result') is True:
                log.info(f"Лид {lead_id} успешно обновлен")
                
                # 4. Добавление комментария в ленту
                try:
                    timeline_comment = f"🤖 Автоматический анализ встречи завершен\n\n{gemini_data.get('analysis', '')[:500]}"
                    add_lead_timeline_comment(lead_id, timeline_comment)
                except Exception as e:
                    operation_result['warnings'].append(f"Не удалось добавить комментарий в ленту: {e}")
                
            else:
                operation_result['warnings'].append("Неожиданный результат обновления лида")
                
        except Exception as e:
            operation_result['errors'].append(f"Ошибка обновления лида: {e}")
            return operation_result
        
        # 5. Создание задачи
        if create_task:
            try:
                task_result = create_advanced_task(lead_id, gemini_data)
                operation_result['task_creation'] = task_result
                
                if task_result.get('result'):
                    task_id = task_result['result'].get('task', {}).get('id')
                    log.info(f"Создана задача {task_id} для лида {lead_id}")
                else:
                    operation_result['warnings'].append("Неожиданный результат создания задачи")
                    
            except Exception as e:
                operation_result['errors'].append(f"Ошибка создания задачи: {e}")
        
        return operation_result
        
    except Exception as e:
        operation_result['errors'].append(f"Общая ошибка операции: {e}")
        return operation_result

# Дополнительные утилиты для отладки и мониторинга

def debug_field_mapping(gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """Отладочная функция для проверки маппинга полей"""
    try:
        fields_meta = get_lead_fields()
        debug_info = {
            'gemini_data_keys': list(gemini_data.keys()),
            'field_mappings': {},
            'enum_fields': {},
            'boolean_fields': {},
            'string_fields': {}
        }
        
        # Проверяем маппинг enum полей
        enum_mappings = {
            'client_type_text': 'UF_CRM_1547738289',
            'bad_reason_text': 'UF_CRM_1555492157080', 
            'kp_done_text': 'UF_CRM_1754652099',
            'lpr_confirmed_text': 'UF_CRM_1755007163632'
        }
        
        for gemini_key, bitrix_field in enum_mappings.items():
            if gemini_key in gemini_data:
                value = gemini_data[gemini_key]
                items = fields_meta.get('result', {}).get(bitrix_field, {}).get('items', [])
                found_id = _enum_find_id(items, value)
                
                debug_info['enum_fields'][gemini_key] = {
                    'value': value,
                    'bitrix_field': bitrix_field,
                    'found_id': found_id,
                    'available_values': [item.get('VALUE') for item in items]
                }
        
        # Проверяем boolean поля
        bool_mappings = {
            'is_lpr': 'UF_CRM_1754651857',
            'meeting_scheduled': 'UF_CRM_1754651891',
            'meeting_done': 'UF_CRM_1754651937'
        }
        
        for gemini_key, bitrix_field in bool_mappings.items():
            if gemini_key in gemini_data:
                value = gemini_data[gemini_key]
                debug_info['boolean_fields'][gemini_key] = {
                    'value': value,
                    'bitrix_field': bitrix_field,
                    'mapped_value': _map_bool(value)
                }
        
        # Проверяем строковые поля
        string_mappings = {
            'wow_effect': 'UF_CRM_1754665062',
            'product': 'UF_CRM_1579102568584',
            'task_formulation': 'UF_CRM_1592909799043',
            'ad_budget': 'UF_CRM_1592910027'
        }
        
        for gemini_key, bitrix_field in string_mappings.items():
            if gemini_key in gemini_data:
                value = gemini_data[gemini_key]
                debug_info['string_fields'][gemini_key] = {
                    'value': value,
                    'bitrix_field': bitrix_field,
                    'length': len(str(value))
                }
        
        return debug_info
        
    except Exception as e:
        return {'error': str(e)}

# Экспорт основных функций для использования в других модулях
__all__ = [
    'update_lead_with_checklist',
    'update_lead_and_create_task', 
    'update_lead_comprehensive',
    'create_advanced_task',
    'get_lead_info',
    'get_lead_fields',
    'test_bitrix_connection',
    'get_bitrix_info',
    'BitrixError'
]
