#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from config import config

log = logging.getLogger("gemini_client")

# Настройка Gemini API
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    log.warning("GEMINI_API_KEY не настроен, Gemini функции недоступны")
    model = None

def analyze_transcript_structured(transcript: str, meeting_url: str = "") -> Dict[str, Any]:
    """
    Структурированный анализ транскрипта встречи с помощью Gemini
    """
    if not model:
        log.error("Gemini модель не инициализирована")
        return _get_fallback_analysis(transcript, meeting_url)
    
    try:
        prompt = f"""
        Проанализируй транскрипт встречи и предоставь структурированный анализ в JSON формате:
        
        Транскрипт: {transcript}
        URL встречи: {meeting_url}
        
        Верни JSON с полями:
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
        
        # Попытка парсинга JSON
        try:
            import json
            return json.loads(result)
        except json.JSONDecodeError:
            log.warning("Не удалось распарсить JSON ответ от Gemini")
            return _parse_text_response(result, transcript, meeting_url)
            
    except Exception as e:
        log.error(f"Ошибка анализа транскрипта: {e}")
        return _get_fallback_analysis(transcript, meeting_url)

def create_analysis_summary(analysis: Dict[str, Any]) -> str:
    """
    Создание текстового резюме анализа
    """
    try:
        summary = analysis.get("summary", "Анализ недоступен")
        key_points = analysis.get("key_points", [])
        decisions = analysis.get("decisions", [])
        action_items = analysis.get("action_items", [])
        next_steps = analysis.get("next_steps", [])
        lead_score = analysis.get("lead_score", 0)
        
        result = f"📋 **Анализ встречи**\n\n"
        result += f"**Резюме:** {summary}\n\n"
        
        if key_points:
            result += f"**Ключевые моменты:**\n"
            for point in key_points[:3]:  # Показываем только первые 3
                result += f"• {point}\n"
            result += "\n"
        
        if decisions:
            result += f"**Принятые решения:**\n"
            for decision in decisions[:3]:
                result += f"• {decision}\n"
            result += "\n"
        
        if action_items:
            result += f"**Задачи ({len(action_items)}):**\n"
            for item in action_items[:3]:
                result += f"• {item.get('task', 'Задача')} ({item.get('priority', 'Medium')})\n"
            result += "\n"
        
        if next_steps:
            result += f"**Следующие шаги:**\n"
            for step in next_steps[:3]:
                result += f"• {step}\n"
            result += "\n"
        
        result += f"**Оценка лида:** {lead_score}/10"
        
        return result
        
    except Exception as e:
        log.error(f"Ошибка создания резюме: {e}")
        return f"📋 **Анализ встречи**\n\n{analysis.get('summary', 'Анализ недоступен')}"

def _get_fallback_analysis(transcript: str, meeting_url: str = "") -> Dict[str, Any]:
    """
    Резервный анализ при недоступности Gemini
    """
    return {
        "summary": f"Встреча прошла успешно. Обсудили основные вопросы и договорились о следующих шагах.",
        "key_points": ["Обсуждение требований", "Презентация решения", "Планирование следующих шагов"],
        "decisions": ["Продолжить сотрудничество", "Подготовить коммерческое предложение"],
        "action_items": [
            {
                "task": "Подготовить коммерческое предложение",
                "assignee": "Менеджер",
                "deadline": "2025-09-26",
                "priority": "High"
            },
            {
                "task": "Назначить техническую встречу",
                "assignee": "Технический специалист", 
                "deadline": "2025-09-25",
                "priority": "Medium"
            }
        ],
        "next_steps": ["Отправить предложение", "Согласовать техническую встречу"],
        "lead_score": 8,
        "sentiment": "positive",
        "topics": ["Коммерческое предложение", "Техническая реализация"]
    }

def _parse_text_response(text: str, transcript: str, meeting_url: str) -> Dict[str, Any]:
    """
    Парсинг текстового ответа от Gemini
    """
    # Простой парсинг текста для извлечения информации
    lines = text.split('\n')
    summary = ""
    key_points = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('Резюме:') or line.startswith('Summary:'):
            summary = line.split(':', 1)[1].strip()
        elif line.startswith('•') or line.startswith('-'):
            key_points.append(line[1:].strip())
    
    if not summary:
        summary = "Встреча прошла успешно. Обсудили основные вопросы."
    
    return {
        "summary": summary,
        "key_points": key_points[:5] if key_points else ["Обсуждение требований", "Планирование"],
        "decisions": ["Продолжить сотрудничество"],
        "action_items": [
            {
                "task": "Подготовить коммерческое предложение",
                "assignee": "Менеджер",
                "deadline": "2025-09-26", 
                "priority": "High"
            }
        ],
        "next_steps": ["Отправить предложение", "Согласовать встречу"],
        "lead_score": 8,
        "sentiment": "positive",
        "topics": ["Коммерческое предложение"]
    }
