#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import requests
from typing import Dict, List, Any, Optional
from config import config

log = logging.getLogger("bitrix")

def update_lead_comprehensive(
    lead_id: int,
    meeting_summary: str,
    lead_score: int = 8,
    action_items: List[Dict[str, Any]] = None
) -> bool:
    """
    Комплексное обновление лида в Bitrix24
    """
    if not config.BITRIX_WEBHOOK_URL:
        log.error("BITRIX_WEBHOOK_URL не настроен")
        return False
    
    try:
        # Обновление лида
        lead_data = {
            "fields": {
                "TITLE": f"Лид {lead_id} - Встреча проведена",
                "COMMENTS": meeting_summary,
                "UF_CRM_LEAD_SCORE": lead_score,
                "STATUS_ID": "IN_PROCESS"
            }
        }
        
        # Отправка обновления лида
        lead_response = requests.post(
            f"{config.BITRIX_WEBHOOK_URL}/crm.lead.update",
            json={"id": lead_id, "fields": lead_data["fields"]},
            timeout=10
        )
        
        if lead_response.status_code != 200:
            log.error(f"Ошибка обновления лида: {lead_response.status_code}")
            return False
        
        # Создание задач из action_items
        if action_items:
            for item in action_items:
                task_data = {
                    "fields": {
                        "TITLE": item.get("task", "Задача из встречи"),
                        "DESCRIPTION": f"Задача создана автоматически из встречи для лида {lead_id}",
                        "RESPONSIBLE_ID": config.BITRIX_USER_ID or "1",
                        "DEADLINE": item.get("deadline", ""),
                        "PRIORITY": _map_priority(item.get("priority", "Medium")),
                        "UF_CRM_TASK": [f"L_{lead_id}"]  # Связь с лидом
                    }
                }
                
                task_response = requests.post(
                    f"{config.BITRIX_WEBHOOK_URL}/tasks.task.add",
                    json=task_data,
                    timeout=10
                )
                
                if task_response.status_code == 200:
                    log.info(f"Создана задача: {item.get('task')}")
                else:
                    log.error(f"Ошибка создания задачи: {task_response.status_code}")
        
        log.info(f"Лид {lead_id} успешно обновлен")
        return True
        
    except Exception as e:
        log.error(f"Ошибка обновления лида {lead_id}: {e}")
        return False

def get_lead_info(lead_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение информации о лиде
    """
    if not config.BITRIX_WEBHOOK_URL:
        log.error("BITRIX_WEBHOOK_URL не настроен")
        return None
    
    try:
        response = requests.post(
            f"{config.BITRIX_WEBHOOK_URL}/crm.lead.get",
            json={"id": lead_id},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get("result")
        else:
            log.error(f"Ошибка получения лида: {response.status_code}")
            return None
            
    except Exception as e:
        log.error(f"Ошибка получения лида {lead_id}: {e}")
        return None

def create_activity(lead_id: int, activity_type: str, description: str) -> bool:
    """
    Создание активности для лида
    """
    if not config.BITRIX_WEBHOOK_URL:
        log.error("BITRIX_WEBHOOK_URL не настроен")
        return False
    
    try:
        activity_data = {
            "fields": {
                "TYPE_ID": activity_type,  # 1 - звонок, 2 - встреча, 3 - задача
                "SUBJECT": f"Встреча с лидом {lead_id}",
                "DESCRIPTION": description,
                "OWNER_TYPE_ID": 1,  # Лид
                "OWNER_ID": lead_id,
                "RESPONSIBLE_ID": config.BITRIX_USER_ID or "1"
            }
        }
        
        response = requests.post(
            f"{config.BITRIX_WEBHOOK_URL}/crm.activity.add",
            json=activity_data,
            timeout=10
        )
        
        if response.status_code == 200:
            log.info(f"Создана активность для лида {lead_id}")
            return True
        else:
            log.error(f"Ошибка создания активности: {response.status_code}")
            return False
            
    except Exception as e:
        log.error(f"Ошибка создания активности для лида {lead_id}: {e}")
        return False

def _map_priority(priority: str) -> str:
    """
    Маппинг приоритета задачи
    """
    priority_map = {
        "High": "3",
        "Medium": "2", 
        "Low": "1"
    }
    return priority_map.get(priority, "2")
