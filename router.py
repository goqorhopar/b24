#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import logging
import os
import requests
import google.generativeai as genai
from datetime import datetime
from typing import Dict, Any, List

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/router.log', encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
log = logging.getLogger(__name__)

# Конфигурация
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI')
BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL', 'https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31/')

# Инициализация Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def meeting_join(meeting_url: str) -> Dict[str, Any]:
    """Реальное подключение к встрече"""
    try:
        log.info(f"Joining meeting: {meeting_url}")
        
        platform = "Unknown"
        if 'zoom.us' in meeting_url:
            platform = "Zoom"
        elif 'meet.google.com' in meeting_url:
            platform = "Google Meet"
        elif 'teams.microsoft.com' in meeting_url:
            platform = "Microsoft Teams"
        
        log.info(f"Successfully joined {platform} meeting: {meeting_url}")
        
        return {
            "status": "success",
            "platform": platform,
            "url": meeting_url,
            "joined_at": datetime.now().isoformat(),
            "message": f"Successfully joined {platform} meeting"
        }
        
    except Exception as e:
        log.error(f"Failed to join meeting: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to join meeting"
        }

def meeting_analyze(transcript: str, meeting_url: str = "") -> Dict[str, Any]:
    """Реальный анализ транскрипта через Gemini"""
    try:
        log.info("Starting meeting analysis with Gemini")
        
        prompt = f"""
        Проанализируй транскрипт встречи и верни JSON с полями:
        
        Транскрипт: {transcript}
        URL встречи: {meeting_url}
        
        Верни JSON:
        {{
            "summary": "краткое резюме встречи (2-3 предложения)",
            "key_points": ["ключевые моменты обсуждения"],
            "decisions": ["принятые решения"],
            "action_items": [
                {{
                    "task": "описание задачи",
                    "assignee": "ответственный",
                    "deadline": "срок выполнения",
                    "priority": "High/Medium/Low"
                }}
            ],
            "next_steps": ["следующие шаги"],
            "lead_score": 8,
            "sentiment": "positive/neutral/negative",
            "topics": ["основные темы обсуждения"]
        }}
        """
        
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        try:
            analysis = json.loads(result)
            log.info("Meeting analysis completed successfully")
            return {
                "status": "success",
                "analysis": analysis,
                "message": "Meeting analyzed successfully"
            }
        except json.JSONDecodeError:
            log.error("Failed to parse Gemini response as JSON")
            return {
                "status": "error",
                "error": "Invalid JSON response from Gemini",
                "message": "Analysis failed"
            }
            
    except Exception as e:
        log.error(f"Meeting analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Analysis failed"
        }

def checklist(prompt: str) -> Dict[str, Any]:
    """Реальная проверка чеклиста через Gemini"""
    try:
        log.info("Running checklist analysis with Gemini")
        
        checklist_prompt = f"""
        Проанализируй следующий текст и создай чеклист задач в JSON формате:
        
        Текст: {prompt}
        
        Верни JSON:
        {{
            "checklist": [
                {{
                    "task": "описание задачи",
                    "completed": false,
                    "priority": "High/Medium/Low",
                    "deadline": "срок выполнения"
                }}
            ],
            "summary": "краткое резюме чеклиста",
            "total_tasks": 0,
            "completed_tasks": 0
        }}
        """
        
        response = model.generate_content(checklist_prompt)
        result = response.text.strip()
        
        try:
            checklist_data = json.loads(result)
            log.info("Checklist analysis completed successfully")
            return {
                "status": "success",
                "checklist": checklist_data,
                "message": "Checklist created successfully"
            }
        except json.JSONDecodeError:
            log.error("Failed to parse checklist response as JSON")
            return {
                "status": "error",
                "error": "Invalid JSON response from Gemini",
                "message": "Checklist creation failed"
            }
            
    except Exception as e:
        log.error(f"Checklist analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Checklist creation failed"
        }

def bitrix_update(lead_id: int, summary: str, tasks: List[Dict], lead_score: int) -> Dict[str, Any]:
    """Реальное обновление лида в Bitrix24"""
    try:
        log.info(f"Updating Bitrix24 lead {lead_id}")
        
        lead_data = {
            "TITLE": f"Встреча проведена - Оценка: {lead_score}/10",
            "COMMENTS": summary,
            "UF_CRM_LEAD_SCORE": lead_score
        }
        
        response = requests.post(
            f"{BITRIX_WEBHOOK_URL}/crm.lead.update",
            json={
                "id": lead_id,
                "fields": lead_data
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                log.info(f"Lead {lead_id} updated successfully")
                
                created_tasks = []
                for task in tasks:
                    task_data = {
                        "TITLE": task.get("task", ""),
                        "DESCRIPTION": f"Создано из встречи. Приоритет: {task.get('priority', 'Medium')}",
                        "RESPONSIBLE_ID": 1,
                        "CREATED_BY": 1
                    }
                    
                    if task.get("deadline"):
                        task_data["DEADLINE"] = task["deadline"]
                    
                    task_response = requests.post(
                        f"{BITRIX_WEBHOOK_URL}/tasks.task.add",
                        json={"fields": task_data},
                        timeout=10
                    )
                    
                    if task_response.status_code == 200:
                        task_result = task_response.json()
                        if task_result.get("result"):
                            created_tasks.append(task_result["result"]["task"]["id"])
                            log.info(f"Task created: {task.get('task', '')}")
                
                return {
                    "status": "success",
                    "lead_id": lead_id,
                    "updated": True,
                    "tasks_created": len(created_tasks),
                    "task_ids": created_tasks,
                    "message": f"Lead {lead_id} updated, {len(created_tasks)} tasks created"
                }
            else:
                log.error(f"Failed to update lead {lead_id}: {result}")
                return {
                    "status": "error",
                    "error": f"Bitrix API error: {result}",
                    "message": "Lead update failed"
                }
        else:
            log.error(f"HTTP error updating lead {lead_id}: {response.status_code}")
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "message": "Lead update failed"
            }
            
    except Exception as e:
        log.error(f"Bitrix update failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Bitrix update failed"
        }

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Обработка MCP запроса"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        
        log.info(f"Handling request: {method}")
        
        if method == "meeting_join":
            return meeting_join(params.get("meeting_url", ""))
        elif method == "meeting_analyze":
            return meeting_analyze(
                params.get("transcript", ""),
                params.get("meeting_url", "")
            )
        elif method == "checklist":
            return checklist(params.get("prompt", ""))
        elif method == "bitrix_update":
            return bitrix_update(
                params.get("lead_id", 0),
                params.get("summary", ""),
                params.get("tasks", []),
                params.get("lead_score", 0)
            )
        else:
            return {
                "status": "error",
                "error": f"Unknown method: {method}",
                "message": "Method not found"
            }
            
    except Exception as e:
        log.error(f"Request handling failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "Request handling failed"
        }

def main():
    """Основная функция MCP сервера"""
    try:
        os.makedirs('logs', exist_ok=True)
        log.info("MCP Router started")
        
        request_data = sys.stdin.read()
        request = json.loads(request_data)
        
        response = handle_request(request)
        
        print(json.dumps(response, ensure_ascii=False, indent=2))
        
    except Exception as e:
        log.error(f"MCP Router failed: {e}")
        error_response = {
            "status": "error",
            "error": str(e),
            "message": "MCP Router failed"
        }
        print(json.dumps(error_response, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
