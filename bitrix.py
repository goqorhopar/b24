#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import logging
from config import config

log = logging.getLogger("bitrix")

def update_lead_comprehensive(lead_id: int, meeting_summary: str, lead_score: int, action_items: list) -> bool:
    """
    Комплексное обновление лида в Bitrix24
    """
    try:
        webhook_url = config.BITRIX_WEBHOOK_URL
        if not webhook_url:
            log.error("BITRIX_WEBHOOK_URL не настроен")
            return False

        # Обновление лида
        lead_data = {
            "TITLE": f"Встреча проведена - Оценка: {lead_score}/10",
            "COMMENTS": meeting_summary,
            "UF_CRM_LEAD_SCORE": lead_score
        }

        # Отправка запроса на обновление лида
        response = requests.post(
            f"{webhook_url}/crm.lead.update",
            json={
                "id": lead_id,
                "fields": lead_data
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                log.info(f"Лид {lead_id} успешно обновлен")
                
                # Создание задач
                for item in action_items:
                    create_task(
                        title=item.get("task", ""),
                        description=f"Создано из встречи. Приоритет: {item.get('priority', 'Medium')}",
                        deadline=item.get("deadline", ""),
                        responsible_id=config.BITRIX_USER_ID or 1
                    )
                
                return True
            else:
                log.error(f"Ошибка обновления лида {lead_id}: {result}")
                return False
        else:
            log.error(f"HTTP ошибка при обновлении лида {lead_id}: {response.status_code}")
            return False

    except Exception as e:
        log.error(f"Исключение при обновлении лида {lead_id}: {e}")
        return False

def create_task(title: str, description: str, deadline: str = "", responsible_id: int = 1) -> bool:
    """
    Создание задачи в Bitrix24
    """
    try:
        webhook_url = config.BITRIX_WEBHOOK_URL
        if not webhook_url:
            log.error("BITRIX_WEBHOOK_URL не настроен")
            return False

        task_data = {
            "TITLE": title,
            "DESCRIPTION": description,
            "RESPONSIBLE_ID": responsible_id,
            "CREATED_BY": responsible_id
        }

        if deadline:
            task_data["DEADLINE"] = deadline

        response = requests.post(
            f"{webhook_url}/tasks.task.add",
            json={
                "fields": task_data
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                log.info(f"Задача '{title}' успешно создана")
                return True
            else:
                log.error(f"Ошибка создания задачи: {result}")
                return False
        else:
            log.error(f"HTTP ошибка при создании задачи: {response.status_code}")
            return False

    except Exception as e:
        log.error(f"Исключение при создании задачи: {e}")
        return False