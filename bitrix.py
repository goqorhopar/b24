import os
import requests
import logging
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin

# Настройка логирования
log = logging.getLogger(__name__)

# Конфигурация Bitrix24
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
BITRIX_RESPONSIBLE_ID = os.getenv('BITRIX_RESPONSIBLE_ID', '1')
BITRIX_CREATED_BY_ID = os.getenv('BITRIX_CREATED_BY_ID', '1')
BITRIX_TASK_DEADLINE_DAYS = int(os.getenv('BITRIX_TASK_DEADLINE_DAYS', '3'))

# Настройки запросов
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_COMMENT_LENGTH = 8000  # Ограничение длины комментария

class BitrixError(Exception):
    """Исключение для ошибок Bitrix API"""
    pass

def _make_bitrix_request(method: str, data: Dict[str, Any], retries: int = MAX_RETRIES) -> Dict[str, Any]:
    """Базовый метод для выполнения запросов к Bitrix API"""
    
    if not BITRIX_WEBHOOK_URL:
        raise BitrixError("BITRIX_WEBHOOK_URL не настроен")
    
    url = urljoin(BITRIX_WEBHOOK_URL.rstrip('/') + '/', method)
    
    for attempt in range(retries):
        try:
            log.debug(f"Bitrix API запрос (попытка {attempt + 1}): {method}")
            
            response = requests.post(
                url,
                json=data,
                timeout=REQUEST_TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            
            result = response.json()
            
            # Проверяем наличие ошибок в ответе Bitrix
            if 'error' in result:
                error_msg = result.get('error_description', result.get('error', 'Неизвестная ошибка'))
                raise BitrixError(f"Ошибка Bitrix API: {error_msg}")
            
            log.debug(f"Bitrix API успешный ответ: {method}")
            return result
            
        except requests.exceptions.RequestException as e:
            log.warning(f"Ошибка HTTP запроса к Bitrix (попытка {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise BitrixError(f"Не удалось выполнить запрос к Bitrix после {retries} попыток: {str(e)}")
        
        except BitrixError:
            raise  # Пробрасываем ошибки Bitrix API
        
        except Exception as e:
            log.error(f"Неожиданная ошибка при запросе к Bitrix: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
                continue
            raise BitrixError(f"Неожиданная ошибка Bitrix API: {str(e)}")
    
    raise BitrixError("Все попытки запроса к Bitrix исчерпаны")

def update_lead_comment(lead_id: str, comment: str) -> Dict[str, Any]:
    """Обновление комментария лида"""
    
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида не может быть пустым")
    
    if not comment or not comment.strip():
        raise BitrixError("Комментарий не может быть пустым")
    
    # Обрезаем комментарий если он слишком длинный
    if len(comment) > MAX_COMMENT_LENGTH:
        comment = comment[:MAX_COMMENT_LENGTH] + "\n\n[Комментарий обрезан из-за ограничений длины]"
        log.warning(f"Комментарий для лида {lead_id} обрезан до {MAX_COMMENT_LENGTH} символов")
    
    try:
        log.info(f"Обновление комментария лида {lead_id}")
        
        data = {
            'id': lead_id.strip(),
            'fields': {
                'COMMENTS': comment.strip()
            },
            'params': {
                'REGISTER_SONET_EVENT': 'Y'  # Регистрируем событие в ленте активности
            }
        }
        
        result = _make_bitrix_request('crm.lead.update.json', data)
        
        if result.get('result'):
            log.info(f"Лид {lead_id} успешно обновлён")
            return {
                'success': True,
                'lead_id': lead_id,
                'updated': True,
                'result': result
            }
        else:
            log.warning(f"Неожиданный ответ при обновлении лида {lead_id}: {result}")
            return {
                'success': False,
                'lead_id': lead_id,
                'error': 'Неожиданный формат ответа',
                'result': result
            }
            
    except Exception as e:
        log.error(f"Ошибка обновления лида {lead_id}: {e}")
        raise

def get_lead_info(lead_id: str) -> Dict[str, Any]:
    """Получение информации о лиде"""
    
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида не может быть пустым")
    
    try:
        log.info(f"Получение информации о лиде {lead_id}")
        
        data = {
            'id': lead_id.strip(),
            'select': [
                'ID', 'TITLE', 'STATUS_ID', 'STAGE_ID', 
                'NAME', 'LAST_NAME', 'COMPANY_TITLE',
                'PHONE', 'EMAIL', 'COMMENTS',
                'OPPORTUNITY', 'CURRENCY_ID',
                'ASSIGNED_BY_ID', 'CREATED_BY_ID',
                'DATE_CREATE', 'DATE_MODIFY'
            ]
        }
        
        result = _make_bitrix_request('crm.lead.get.json', data)
        
        if result.get('result'):
            lead_data = result['result']
            log.info(f"Информация о лиде {lead_id} получена успешно")
            return {
                'success': True,
                'lead_id': lead_id,
                'data': lead_data
            }
        else:
            log.warning(f"Лид {lead_id} не найден")
            return {
                'success': False,
                'lead_id': lead_id,
                'error': 'Лид не найден'
            }
            
    except Exception as e:
        log.error(f"Ошибка получения информации о лиде {lead_id}: {e}")
        raise

def add_lead_activity(lead_id: str, subject: str, description: str, activity_type: str = 'CALL') -> Dict[str, Any]:
    """Добавление активности к лиду"""
    
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида не может быть пустым")
    
    try:
        log.info(f"Добавление активности к лиду {lead_id}")
        
        data = {
            'fields': {
                'OWNER_TYPE_ID': 1,  # Лид
                'OWNER_ID': lead_id.strip(),
                'TYPE_ID': activity_type,
                'SUBJECT': subject[:255],  # Ограничиваем длину заголовка
                'DESCRIPTION': description[:8000],  # Ограничиваем длину описания
                'RESPONSIBLE_ID': BITRIX_RESPONSIBLE_ID,
                'CREATED_BY_ID': BITRIX_CREATED_BY_ID,
                'COMPLETED': 'Y'  # Отмечаем как выполненную
            }
        }
        
        result = _make_bitrix_request('crm.activity.add.json', data)
        
        if result.get('result'):
            activity_id = result['result']
            log.info(f"Активность {activity_id} добавлена к лиду {lead_id}")
            return {
                'success': True,
                'lead_id': lead_id,
                'activity_id': activity_id
            }
        else:
            log.warning(f"Не удалось добавить активность к лиду {lead_id}")
            return {
                'success': False,
                'lead_id': lead_id,
                'error': 'Не удалось создать активность'
            }
            
    except Exception as e:
        log.error(f"Ошибка добавления активности к лиду {lead_id}: {e}")
        raise

def create_task_for_lead(lead_id: str, title: str, description: str, responsible_id: Optional[str] = None) -> Dict[str, Any]:
    """Создание задачи по лиду"""
    
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида не может быть пустым")
    
    try:
        from datetime import datetime, timedelta
        
        deadline = (datetime.now() + timedelta(days=BITRIX_TASK_DEADLINE_DAYS)).strftime('%Y-%m-%d %H:%M:%S')
        
        log.info(f"Создание задачи для лида {lead_id}")
        
        data = {
            'fields': {
                'TITLE': title[:255],
                'DESCRIPTION': description[:8000],
                'RESPONSIBLE_ID': responsible_id or BITRIX_RESPONSIBLE_ID,
                'CREATED_BY': BITRIX_CREATED_BY_ID,
                'DEADLINE': deadline,
                'UF_CRM_TASK': [f'L_{lead_id}']  # Привязка к лиду
            }
        }
        
        result = _make_bitrix_request('tasks.task.add.json', data)
        
        if result.get('result'):
            task_id = result['result']['task']['id']
            log.info(f"Задача {task_id} создана для лида {lead_id}")
            return {
                'success': True,
                'lead_id': lead_id,
                'task_id': task_id,
                'deadline': deadline
            }
        else:
            log.warning(f"Не удалось создать задачу для лида {lead_id}")
            return {
                'success': False,
                'lead_id': lead_id,
                'error': 'Не удалось создать задачу'
            }
            
    except Exception as e:
        log.error(f"Ошибка создания задачи для лида {lead_id}: {e}")
        raise

def update_lead_stage(lead_id: str, stage_id: str) -> Dict[str, Any]:
    """Изменение стадии лида"""
    
    if not lead_id or not lead_id.strip():
        raise BitrixError("ID лида не может быть пустым")
    
    if not stage_id or not stage_id.strip():
        raise BitrixError("ID стадии не может быть пустым")
    
    try:
        log.info(f"Изменение стадии лида {lead_id} на {stage_id}")
        
        data = {
            'id': lead_id.strip(),
            'fields': {
                'STAGE_ID': stage_id.strip()
            },
            'params': {
                'REGISTER_SONET_EVENT': 'Y'
            }
        }
        
        result = _make_bitrix_request('crm.lead.update.json', data)
        
        if result.get('result'):
            log.info(f"Стадия лида {lead_id} изменена на {stage_id}")
            return {
                'success': True,
                'lead_id': lead_id,
                'stage_id': stage_id
            }
        else:
            log.warning(f"Не удалось изменить стадию лида {lead_id}")
            return {
                'success': False,
                'lead_id': lead_id,
                'error': 'Не удалось изменить стадию'
            }
            
    except Exception as e:
        log.error(f"Ошибка изменения стадии лида {lead_id}: {e}")
        raise

def test_bitrix_connection() -> bool:
    """Тестирование соединения с Bitrix24"""
    
    if not BITRIX_WEBHOOK_URL:
        log.warning("BITRIX_WEBHOOK_URL не настроен")
        return False
    
    try:
        log.info("Тестирование соединения с Bitrix24...")
        
        # Простой запрос для проверки соединения
        result = _make_bitrix_request('crm.lead.list.json', {
            'select': ['ID'],
            'filter': {'ID': '999999999'},  # Несуществующий ID
            'start': 0
        })
        
        if 'result' in result:
            log.info("✅ Соединение с Bitrix24 работает")
            return True
        else:
            log.warning("⚠️ Неожиданный ответ от Bitrix24")
            return False
            
    except Exception as e:
        log.error(f"❌ Ошибка соединения с Bitrix24: {e}")
        return False

def get_bitrix_info() -> Dict[str, Any]:
    """Получение информации о настройках Bitrix"""
    return {
        'webhook_url_set': bool(BITRIX_WEBHOOK_URL),
        'webhook_url': BITRIX_WEBHOOK_URL[:50] + '...' if BITRIX_WEBHOOK_URL else None,
        'responsible_id': BITRIX_RESPONSIBLE_ID,
        'created_by_id': BITRIX_CREATED_BY_ID,
        'task_deadline_days': BITRIX_TASK_DEADLINE_DAYS,
        'max_comment_length': MAX_COMMENT_LENGTH,
        'request_timeout': REQUEST_TIMEOUT,
        'max_retries': MAX_RETRIES
    }

# Комплексная функция для полного обновления лида
def update_lead_full(lead_id: str, analysis: str, create_activity: bool = True, create_task: bool = False) -> Dict[str, Any]:
    """Полное обновление лида с анализом"""
    
    results = {
        'lead_id': lead_id,
        'comment_updated': False,
        'activity_created': False,
        'task_created': False,
        'errors': []
    }
    
    try:
        # 1. Обновляем комментарий
        comment_result = update_lead_comment(lead_id, analysis)
        results['comment_updated'] = comment_result.get('success', False)
        
        if not results['comment_updated']:
            results['errors'].append('Не удалось обновить комментарий')
        
        # 2. Создаём активность если нужно
        if create_activity:
            try:
                activity_result = add_lead_activity(
                    lead_id,
                    'Анализ встречи с клиентом',
                    f"Проведён автоматический анализ встречи:\n\n{analysis[:1000]}..."
                )
                results['activity_created'] = activity_result.get('success', False)
                
                if not results['activity_created']:
                    results['errors'].append('Не удалось создать активность')
                    
            except Exception as e:
                results['errors'].append(f'Ошибка создания активности: {str(e)}')
        
        # 3. Создаём задачу если нужно
        if create_task:
            try:
                task_result = create_task_for_lead(
                    lead_id,
                    f'Отработка лида {lead_id} после анализа',
                    f"На основе анализа встречи выполнить действия:\n\n{analysis[:500]}..."
                )
                results['task_created'] = task_result.get('success', False)
                
                if not results['task_created']:
                    results['errors'].append('Не удалось создать задачу')
                    
            except Exception as e:
                results['errors'].append(f'Ошибка создания задачи: {str(e)}')
        
        # Определяем общий успех
        results['success'] = results['comment_updated'] and len(results['errors']) == 0
        
        return results
        
    except Exception as e:
        results['errors'].append(f'Критическая ошибка: {str(e)}')
        results['success'] = False
        return results
