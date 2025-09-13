"""
Модуль интеграции анализа встреч с Bitrix24
Автоматическое обновление полей лида на основе анализа онлайн-встреч
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from bitrix import (
    BitrixError, 
    update_lead_comment, 
    create_task, 
    _make_bitrix_request,
    _get_fields_meta,
    _enum_id_by_label,
    _format_date,
    _format_datetime,
    BITRIX_RESPONSIBLE_ID,
    BITRIX_CREATED_BY_ID,
    MAX_COMMENT_LENGTH
)

log = logging.getLogger(__name__)


def update_lead_from_meeting_analysis(lead_id: str, meeting_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Автоматическое обновление лида на основе анализа встречи
    meeting_analysis - структура из meeting_analyzer.py
    """
    if not lead_id:
        raise BitrixError("lead_id обязателен")
    
    if not meeting_analysis:
        raise BitrixError("meeting_analysis не может быть пустым")
    
    result = {
        'updated': False,
        'detail': None,
        'task_created': False,
        'task_id': None,
        'tasks': [],
        'fields_updated': [],
        'comment_updated': False,
        'meeting_data_processed': False
    }
    
    try:
        log.info(f"Начинаем обновление лида {lead_id} на основе анализа встречи")
        
        # 1. Извлечение данных из анализа встречи
        gemini_data = _convert_meeting_analysis_to_gemini_format(meeting_analysis)
        
        # 2. Обновление комментария с анализом встречи
        if meeting_analysis.get('transcription') or meeting_analysis.get('summary'):
            try:
                meeting_comment = _format_meeting_analysis_comment(meeting_analysis)
                update_resp = update_lead_comment(str(lead_id), meeting_comment)
                result['comment_updated'] = True
                log.info(f"Обновлен комментарий лида {lead_id} с анализом встречи")
            except Exception as e:
                log.exception(f"Не удалось обновить комментарий лида {lead_id}: {e}")
        
        # 3. Обновление полей лида
        fields_payload = _build_lead_fields_from_meeting_analysis(meeting_analysis, gemini_data)
        
        if fields_payload:
            data = {
                'id': str(lead_id).strip(),
                'fields': fields_payload,
                'params': {
                    'REGISTER_SONET_EVENT': 'Y'
                }
            }
            try:
                log.info(f"Обновляем поля лида {lead_id}: {list(fields_payload.keys())}")
                resp = _make_bitrix_request('crm.lead.update.json', data)
                result['updated'] = True
                result['detail'] = resp
                result['fields_updated'] = list(fields_payload.keys())
                log.info(f"Lead {lead_id} updated with fields: {list(fields_payload.keys())}")
            except Exception as e:
                log.exception(f"Ошибка при обновлении полей лида {lead_id}: {e}")
        
        # 4. Создание задач на основе анализа встречи
        task_result = _create_tasks_from_meeting_analysis(lead_id, meeting_analysis, gemini_data)
        if task_result:
            result.update(task_result)
        
        result['meeting_data_processed'] = True
        
    except Exception as e:
        log.exception(f"Ошибка в update_lead_from_meeting_analysis: {e}")
        raise
    
    log.info(f"Завершено обновление лида {lead_id} на основе анализа встречи. Результат: {result}")
    return result


def _convert_meeting_analysis_to_gemini_format(meeting_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Конвертация формата анализа встречи в формат gemini_data
    для совместимости с существующими функциями
    """
    gemini_data = {}
    
    try:
        # Извлечение данных из анализа
        transcript = meeting_analysis.get('transcription', {}).get('text', '')
        summary = meeting_analysis.get('summary', '')
        extracted_entities = meeting_analysis.get('extracted_entities', {})
        action_items = meeting_analysis.get('action_items', [])
        checklist_score = meeting_analysis.get('checklist_score', {})
        
        # Базовые поля
        gemini_data['analysis'] = transcript
        gemini_data['summary'] = summary
        
        # Извлеченные сущности
        gemini_data['client_name'] = extracted_entities.get('contact_person')
        gemini_data['company_title'] = extracted_entities.get('company')
        gemini_data['budget_value'] = extracted_entities.get('budget')
        gemini_data['timeline_text'] = extracted_entities.get('timeline')
        gemini_data['priority'] = extracted_entities.get('priority')
        
        # Анализ на основе чеклиста
        checklist_responses = meeting_analysis.get('checklist_responses', {})
        
        # Преобразование ответов чеклиста в поля лида
        gemini_data['is_lpr'] = checklist_responses.get('decision_maker_present', False)
        gemini_data['meeting_scheduled'] = True  # Встреча состоялась
        gemini_data['meeting_done'] = True  # Встреча проведена
        
        # Оценка эффективности встречи
        overall_score = checklist_score.get('overall_score', 0)
        if overall_score >= 80:
            gemini_data['wow_effect'] = 'Высокий'
        elif overall_score >= 60:
            gemini_data['wow_effect'] = 'Средний'
        else:
            gemini_data['wow_effect'] = 'Низкий'
        
        # Извлечение ключевой информации из транскрипта
        if transcript:
            key_info = _extract_key_info_from_transcript(transcript)
            gemini_data.update(key_info)
        
        # Обработка пунктов действий
        if action_items:
            gemini_data['key_request'] = action_items[0].get('task', '')
            
            # Поиск задач, связанных с КП
            kp_tasks = [item for item in action_items if 'кп' in item.get('task', '').lower() or 'коммерческое' in item.get('task', '').lower()]
            if kp_tasks:
                gemini_data['kp_done_text'] = 'Да'
            else:
                gemini_data['kp_done_text'] = 'Нет'
        
        # Настроение клиента
        sentiment = meeting_analysis.get('gemini_analysis', {}).get('sentiment', 'neutral')
        gemini_data['sentiment'] = sentiment
        
        # Риск
        risk_level = meeting_analysis.get('gemini_analysis', {}).get('risk_level', 'medium')
        if risk_level == 'high':
            gemini_data['pains_text'] = 'Высокий риск, требуется внимание'
        elif risk_level == 'low':
            gemini_data['pains_text'] = 'Низкий риск, позитивный прогноз'
        else:
            gemini_data['pains_text'] = 'Средний риск, стандартная ситуация'
        
        # Продукт/услуга
        key_topics = meeting_analysis.get('gemini_analysis', {}).get('key_topics', [])
        if key_topics:
            gemini_data['product'] = ', '.join(key_topics[:3])  # Первые 3 темы
        
        # Дата встречи
        meeting_info = meeting_analysis.get('meeting_info', {})
        if meeting_info.get('start_time'):
            gemini_data['meeting_date'] = meeting_info['start_time']
        
        # Закрывающий комментарий
        recommendations = meeting_analysis.get('recommendations', [])
        if recommendations:
            gemini_data['closing_comment'] = '\n'.join(recommendations)
        
        log.info(f"Данные анализа встречи сконвертированы в формат Gemini: {list(gemini_data.keys())}")
        
    except Exception as e:
        log.error(f"Ошибка при конвертации анализа встречи: {e}")
    
    return gemini_data


def _format_meeting_analysis_comment(meeting_analysis: Dict[str, Any]) -> str:
    """
    Форматирование комментария с анализом встречи
    """
    try:
        meeting_info = meeting_analysis.get('meeting_info', {})
        transcript = meeting_analysis.get('transcription', {})
        checklist_score = meeting_analysis.get('checklist_score', {})
        gemini_analysis = meeting_analysis.get('gemini_analysis', {})
        extracted_entities = meeting_analysis.get('extracted_entities', {})
        action_items = meeting_analysis.get('action_items', [])
        recommendations = meeting_analysis.get('recommendations', [])
        
        comment_lines = []
        
        # Заголовок
        comment_lines.append("📊 **Анализ онлайн-встречи**")
        comment_lines.append("=" * 50)
        comment_lines.append("")
        
        # Информация о встрече
        if meeting_info:
            comment_lines.append("📅 **Информация о встрече:**")
            platform = meeting_info.get('platform', 'Unknown')
            meeting_id = meeting_info.get('meeting_id', 'N/A')
            start_time = meeting_info.get('start_time', 'N/A')
            
            comment_lines.append(f"• Платформа: {platform}")
            comment_lines.append(f"• ID встречи: {meeting_id}")
            comment_lines.append(f"• Время начала: {start_time}")
            comment_lines.append("")
        
        # Оценка встречи
        if checklist_score:
            comment_lines.append("📈 **Оценка встречи:**")
            overall_score = checklist_score.get('overall_score', 0)
            checklist_name = checklist_score.get('checklist_name', 'Unknown')
            
            comment_lines.append(f"• Тип встречи: {checklist_name}")
            comment_lines.append(f"• Общая оценка: {overall_score}%")
            
            if overall_score >= 80:
                comment_lines.append(f"• Результат: 🟢 Отлично")
            elif overall_score >= 60:
                comment_lines.append(f"• Результат: 🟡 Хорошо")
            else:
                comment_lines.append(f"• Результат: 🔔 Требует внимания")
            
            comment_lines.append("")
        
        # Извлеченные данные
        if extracted_entities:
            comment_lines.append("🔍 **Извлеченные данные:**")
            for key, value in extracted_entities.items():
                if value:
                    comment_lines.append(f"• {key.replace('_', ' ').title()}: {value}")
            comment_lines.append("")
        
        # Ключевые темы
        key_topics = gemini_analysis.get('key_topics', [])
        if key_topics:
            comment_lines.append("🎯 **Ключевые темы:**")
            for topic in key_topics:
                comment_lines.append(f"• {topic}")
            comment_lines.append("")
        
        # Решения
        decisions = gemini_analysis.get('decisions_made', [])
        if decisions:
            comment_lines.append("✅ **Решения:**")
            for decision in decisions:
                comment_lines.append(f"• {decision}")
            comment_lines.append("")
        
        # Пункты действий
        if action_items:
            comment_lines.append("📝 **Пункты действий:**")
            for item in action_items:
                task = item.get('task', '')
                responsible = item.get('responsible', 'Не указан')
                deadline = item.get('deadline', 'Не указан')
                comment_lines.append(f"• {task}")
                comment_lines.append(f"  - Ответственный: {responsible}")
                comment_lines.append(f"  - Срок: {deadline}")
            comment_lines.append("")
        
        # Настроение и риск
        sentiment = gemini_analysis.get('sentiment', 'neutral')
        risk_level = gemini_analysis.get('risk_level', 'medium')
        
        comment_lines.append("🎭 **Анализ тональности:**")
        comment_lines.append(f"• Настроение: {sentiment}")
        comment_lines.append(f"• Уровень риска: {risk_level}")
        comment_lines.append("")
        
        # Рекомендации
        if recommendations:
            comment_lines.append("💡 **Рекомендации:**")
            for rec in recommendations:
                comment_lines.append(f"• {rec}")
            comment_lines.append("")
        
        # Транскрипт (сокращенный)
        full_transcript = transcript.get('text', '')
        if full_transcript:
            comment_lines.append("📄 **Транскрипт встречи:**")
            comment_lines.append("-" * 30)
            # Ограничиваем длину транскрипта
            if len(full_transcript) > 2000:
                comment_lines.append(full_transcript[:2000] + "...\n[транскрипт сокращен]")
            else:
                comment_lines.append(full_transcript)
        
        return "\n".join(comment_lines)
        
    except Exception as e:
        log.error(f"Ошибка при форматировании комментария: {e}")
        return f"Ошибка при форматировании анализа встречи: {e}"


def _build_lead_fields_from_meeting_analysis(meeting_analysis: Dict[str, Any], gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Построение полей лида на основе анализа встречи
    """
    fields_payload = {}
    
    try:
        # Получение метаданных полей
        fields_meta = _get_fields_meta()
        
        # Маппинг полей анализа на поля Bitrix
        meeting_mapping = {
            'meeting_date': 'UF_CRM_1755862426686',           # date - Дата факт. проведения встречи
            'meeting_responsible_id': 'UF_CRM_1756298185',   # employee - Кто проводит встречу?
            'wow_effect': 'UF_CRM_1754665062',              # string - WOW-эффект
            'product': 'UF_CRM_1579102568584',               # string - Что продает
            'task_formulation': 'UF_CRM_1592909799043',      # string - Как сформулирована задача
            'ad_budget': 'UF_CRM_1592910027',                # string - Рекламный бюджет
            'is_lpr': 'UF_CRM_1754651857',                   # boolean - Вышли на ЛПР?
            'meeting_scheduled': 'UF_CRM_1754651891',        # boolean - Назначили встречу?
            'meeting_done': 'UF_CRM_1754651937',             # boolean - Провели встречу?
            'kp_done_text': 'UF_CRM_1754652099',             # enumeration - Сделали КП? (Да/Нет)
            'lpr_confirmed_text': 'UF_CRM_1755007163632',    # enumeration - ЛПР подтвержден? (Да/Нет)
            'closing_comment': 'UF_CRM_1592911226916',       # string - Комментарий по закрытию
        }
        
        # Обработка полей из gemini_data
        for k, uf in meeting_mapping.items():
            if k in gemini_data and gemini_data.get(k) is not None:
                val = gemini_data.get(k)
                fmeta = fields_meta.get(uf) or {}
                ftype = fmeta.get('type')
                
                log.debug(f"Обрабатываем поле {k} -> {uf}, тип: {ftype}, значение: {val}")
                
                try:
                    if ftype == 'boolean':
                        if isinstance(val, bool):
                            fields_payload[uf] = '1' if val else '0'
                        elif isinstance(val, str):
                            v = val.strip().lower()
                            if v in ('1', 'true', 'yes', 'да'):
                                fields_payload[uf] = '1'
                            elif v in ('0', 'false', 'no', 'нет'):
                                fields_payload[uf] = '0'
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
                        # string и другие типы
                        fields_payload[uf] = str(val)
                        
                except Exception as e:
                    log.warning(f"Пропущено поле {uf} ({k}) из-за ошибки преобразования: {e}")
        
        # Стандартные поля CRM
        # TITLE
        lead_title = gemini_data.get('lead_title')
        if not lead_title:
            # Автогенерация на основе данных встречи
            company = gemini_data.get('company_title') or extracted_entities.get('company')
            product = gemini_data.get('product')
            if company and product:
                lead_title = f"{company} - {product}"
            elif product:
                lead_title = f"Встреча по {product}"
            else:
                lead_title = "Онлайн-встреча"
        
        if lead_title:
            fields_payload['TITLE'] = str(lead_title)[:100]
        
        # NAME, LAST_NAME, COMPANY_TITLE
        if gemini_data.get('client_name'):
            fields_payload['NAME'] = str(gemini_data['client_name'])[:100]
        
        if gemini_data.get('company_title'):
            fields_payload['COMPANY_TITLE'] = str(gemini_data['company_title'])[:255]
        
        # COMMENTS (если есть транскрипт)
        transcript = meeting_analysis.get('transcription', {}).get('text', '')
        if transcript and len(transcript) > 100:
            fields_payload['COMMENTS'] = transcript[:4000]  # Ограничение длины
        
        log.info(f"Построены поля лида из анализа встречи: {list(fields_payload.keys())}")
        
    except Exception as e:
        log.error(f"Ошибка при построении полей лида: {e}")
    
    return fields_payload


def _create_tasks_from_meeting_analysis(lead_id: str, meeting_analysis: Dict[str, Any], gemini_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Создание задач на основе анализа встречи
    """
    result = {
        'task_created': False,
        'task_id': None,
        'tasks': []
    }
    
    try:
        # Получение ответственного
        task_responsible = gemini_data.get('meeting_responsible_id') or BITRIX_RESPONSIBLE_ID
        
        action_items = meeting_analysis.get('action_items', [])
        checklist_score = meeting_analysis.get('checklist_score', {})
        recommendations = meeting_analysis.get('recommendations', [])
        
        # Задача 1: Обработка результатов встречи
        task1_deadline = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        task1_title = 'Обработать результаты онлайн-встречи'
        task1_descr = f"Проанализировать результаты встречи, оценить эффективность ({checklist_score.get('overall_score', 0)}%). Обновить данные лида на основе транскрипта."
        
        try:
            task1_resp = create_task(
                lead_id=str(lead_id),
                title=task1_title,
                description=task1_descr,
                responsible_id=task_responsible,
                deadline=task1_deadline
            )
            result['task_created'] = True
            task1_id = _extract_task_id_from_response(task1_resp)
            if task1_id:
                result['tasks'].append({'step': 1, 'title': task1_title, 'id': str(task1_id)})
        except Exception as e:
            log.exception(f"Ошибка создания задачи 1 для лида {lead_id}: {e}")
        
        # Задача 2: Выполнение пунктов действий
        if action_items:
            task2_deadline = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
            task2_title = 'Выполнить пункты действий по встрече'
            
            action_text = "\n".join([f"• {item.get('task', '')} (Ответственный: {item.get('responsible', 'N/A')})" for item in action_items[:5]])
            task2_descr = f"Выполнить следующие пункты действий, выявленные в ходе встречи:\n{action_text}"
            
            try:
                task2_resp = create_task(
                    lead_id=str(lead_id),
                    title=task2_title,
                    description=task2_descr,
                    responsible_id=task_responsible,
                    deadline=task2_deadline
                )
                result['task_created'] = True
                task2_id = _extract_task_id_from_response(task2_resp)
                if task2_id:
                    result['tasks'].append({'step': 2, 'title': task2_title, 'id': str(task2_id)})
            except Exception as e:
                log.exception(f"Ошибка создания задачи 2 для лида {lead_id}: {e}")
        
        # Задача 3: Реализация рекомендаций
        if recommendations:
            task3_deadline = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
            task3_title = 'Реализовать рекомендации по встрече'
            
            rec_text = "\n".join([f"• {rec}" for rec in recommendations[:5]])
            task3_descr = f"Реализовать следующие рекомендации для улучшения процесса:\n{rec_text}"
            
            try:
                task3_resp = create_task(
                    lead_id=str(lead_id),
                    title=task3_title,
                    description=task3_descr,
                    responsible_id=task_responsible,
                    deadline=task3_deadline
                )
                result['task_created'] = True
                task3_id = _extract_task_id_from_response(task3_resp)
                if task3_id:
                    result['tasks'].append({'step': 3, 'title': task3_title, 'id': str(task3_id)})
            except Exception as e:
                log.exception(f"Ошибка создания задачи 3 для лида {lead_id}: {e}")
        
        # Дополнительные задачи на основе оценки встречи
        overall_score = checklist_score.get('overall_score', 0)
        
        # Если оценка низкая, создать задачу на анализ проблем
        if overall_score < 60:
            task4_deadline = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
            task4_title = 'Проанализировать проблемы встречи'
            task4_descr = f"Встреча получила низкую оценку ({overall_score}%). Проанализировать причины и разработать план улучшений."
            
            try:
                task4_resp = create_task(
                    lead_id=str(lead_id),
                    title=task4_title,
                    description=task4_descr,
                    responsible_id=task_responsible,
                    deadline=task4_deadline
                )
                result['task_created'] = True
                task4_id = _extract_task_id_from_response(task4_resp)
                if task4_id:
                    result['tasks'].append({'step': 4, 'title': task4_title, 'id': str(task4_id)})
            except Exception as e:
                log.exception(f"Ошибка создания задачи 4 для лида {lead_id}: {e}")
        
        # Публикация сводного комментария
        if result['tasks']:
            try:
                summary_lines = [
                    '📋 Созданы задачи по итогам онлайн-встречи:',
                ]
                for t in sorted(result['tasks'], key=lambda x: x.get('step') or 99):
                    summary_lines.append(f"{t.get('step')}. {t.get('title')} — задача ID {t.get('id')}")
                
                feed_text = "\n".join(summary_lines)
                post_lead_timeline_comment(str(lead_id), feed_text)
            except Exception as e:
                log.warning(f"Не удалось опубликовать комментарий в ленту лида {lead_id}: {e}")
        
    except Exception as e:
        log.exception(f"Ошибка при создании задач из анализа встречи: {e}")
    
    return result


def _extract_task_id_from_response(task_response: Dict[str, Any]) -> Optional[str]:
    """
    Извлечение ID задачи из ответа API
    """
    try:
        if isinstance(task_response, dict) and task_response.get('result'):
            task_result = task_response['result']
            if isinstance(task_result, dict):
                task_id = task_result.get('id') or task_result.get('task', {}).get('id')
                return str(task_id) if task_id else None
    except Exception as e:
        log.warning(f"Ошибка при извлечении ID задачи: {e}")
    return None


def _extract_key_info_from_transcript(transcript: str) -> Dict[str, Any]:
    """
    Извлечение ключевой информации из транскрипта
    """
    key_info = {}
    
    try:
        # Поиск упоминаний бюджета
        budget_patterns = [
            r'бюджет[:\s]*(\d+[\s\d]*[\s]?[руб\$€])',
            r'(\d+[\s\d]*[\s]?[руб\$€]).*бюджет',
            r'стоимость[:\s]*(\d+[\s\d]*[\s]?[руб\$€])',
            r'цена[:\s]*(\d+[\s\d]*[\s]?[руб\$€])',
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                key_info['ad_budget'] = match.group(1)
                break
        
        # Поиск упоминаний сроков
        timeline_patterns = [
            r'срок[:\s]*(\d+\s*(дней|недель|месяцев))',
            r'(\d+\s*(дней|недель|месяцев)).*срок',
            r'к\s*(\d+\s*(дню|неделе|месяцу))',
            r'в\s*(течение\s*\d+\s*(дней|недель|месяцев))',
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                key_info['timeline_text'] = match.group(1)
                break
        
        # Поиск ключевого запроса/потребности
        need_patterns = [
            r'нужен[:\s]*([^\.\n]+)',
            r'требуется[:\s]*([^\.\n]+)',
            r'ищем[:\s]*([^\.\n]+)',
            r'интересуемся[:\s]*([^\.\n]+)',
        ]
        
        for pattern in need_patterns:
            match = re.search(pattern, transcript, re.IGNORECASE)
            if match:
                key_info['key_request'] = match.group(1).strip()
                break
        
    except Exception as e:
        log.error(f"Ошибка при извлечении ключевой информации: {e}")
    
    return key_info


def create_meeting_follow_up_tasks(lead_id: str, meeting_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Создание follow-up задач после встречи
    """
    if not lead_id:
        raise BitrixError("lead_id обязателен")
    
    result = {
        'tasks_created': False,
        'tasks': [],
        'follow_up_strategy': None
    }
    
    try:
        # Анализ результатов встречи для определения стратегии follow-up
        checklist_score = meeting_analysis.get('checklist_score', {})
        overall_score = checklist_score.get('overall_score', 0)
        sentiment = meeting_analysis.get('gemini_analysis', {}).get('sentiment', 'neutral')
        action_items = meeting_analysis.get('action_items', [])
        
        # Определение стратегии follow-up
        if overall_score >= 80 and sentiment == 'positive':
            follow_up_strategy = 'aggressive'
            strategy_desc = 'Агрессивный follow-up (высокий интерес)'
        elif overall_score >= 60:
            follow_up_strategy = 'standard'
            strategy_desc = 'Стандартный follow-up (средний интерес)'
        else:
            follow_up_strategy = 'careful'
            strategy_desc = 'Осторожный follow-up (низкий интерес)'
        
        result['follow_up_strategy'] = {
            'type': follow_up_strategy,
            'description': strategy_desc
        }
        
        # Создание задач в зависимости от стратегии
        if follow_up_strategy == 'aggressive':
            # Агрессивная стратегия - частые контакты
            tasks = [
                {
                    'title': 'Первичный follow-up звонок',
                    'description': 'Позвонить клиенту в течение 24 часов после встречи для закрепления контакта',
                    'deadline_days': 1
                },
                {
                    'title': 'Отправка КП/предложения',
                    'description': 'Подготовить и отправить коммерческое предложение в течение 2 дней',
                    'deadline_days': 2
                },
                {
                    'title': 'Уточнение деталей',
                    'description': 'Связаться для уточнения деталей и ответа на вопросы',
                    'deadline_days': 4
                }
            ]
        elif follow_up_strategy == 'standard':
            # Стандартная стратегия
            tasks = [
                {
                    'title': 'Follow-up контакт',
                    'description': 'Связаться с клиентом в течение 3 дней после встречи',
                    'deadline_days': 3
                },
                {
                    'title': 'Подготовка предложения',
                    'description': 'Подготовить и отправить предложение в течение 5 дней',
                    'deadline_days': 5
                }
            ]
        else:
            # Осторожная стратегия
            tasks = [
                {
                    'title': 'Оценка потенциала',
                    'description': 'Проанализировать потенциал лида и определить целесообразность дальнейшей работы',
                    'deadline_days': 7
                },
                {
                    'title': 'Ненавязчивый контакт',
                    'description': 'Отправить полезную информацию или статью по теме встречи',
                    'deadline_days': 10
                }
            ]
        
        # Создание задач
        task_responsible = BITRIX_RESPONSIBLE_ID
        
        for i, task_info in enumerate(tasks, 1):
            deadline = (datetime.now() + timedelta(days=task_info['deadline_days'])).strftime('%Y-%m-%d %H:%M:%S')
            
            try:
                task_resp = create_task(
                    lead_id=str(lead_id),
                    title=task_info['title'],
                    description=task_info['description'],
                    responsible_id=task_responsible,
                    deadline=deadline
                )
                
                task_id = _extract_task_id_from_response(task_resp)
                if task_id:
                    result['tasks'].append({
                        'step': i,
                        'title': task_info['title'],
                        'id': str(task_id),
                        'deadline_days': task_info['deadline_days']
                    })
                    
            except Exception as e:
                log.exception(f"Ошибка создания follow-up задачи {i} для лида {lead_id}: {e}")
        
        result['tasks_created'] = len(result['tasks']) > 0
        
        # Публикация информации о follow-up стратегии
        if result['tasks']:
            try:
                followup_lines = [
                    f'🎯 **Follow-up стратегия:** {strategy_desc}',
                    '',
                    '📋 Созданы задачи:',
                ]
                for t in result['tasks']:
                    followup_lines.append(f"{t.get('step')}. {t.get('title')} (через {t.get('deadline_days')} дн.) — ID {t.get('id')}")
                
                feed_text = "\n".join(followup_lines)
                post_lead_timeline_comment(str(lead_id), feed_text)
            except Exception as e:
                log.warning(f"Не удалось опубликовать follow-up информацию для лида {lead_id}: {e}")
        
    except Exception as e:
        log.exception(f"Ошибка при создании follow-up задач: {e}")
    
    return result


def post_lead_timeline_comment(lead_id: str, comment: str) -> Dict[str, Any]:
    """
    Публикует комментарий в таймлайн/ленту лида.
    """
    lead_id_str = str(lead_id).strip()
    if not lead_id_str:
        raise BitrixError("ID лида пустой")
    if not comment or not comment.strip():
        raise BitrixError("Комментарий пустой")

    data = {
        'fields': {
            'ENTITY_ID': int(lead_id_str),
            'ENTITY_TYPE': 'lead',
            'COMMENT': str(comment)
        }
    }
    log.info(f"Публикуем комментарий в ленту лида {lead_id}")
    return _make_bitrix_request('crm.timeline.comment.add', data)
