"""
Улучшенный модуль анализа встреч через Gemini с чеклистами
"""
import os
import time
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from gemini_client import analyze_transcript_structured, create_analysis_summary

log = logging.getLogger(__name__)

class MeetingChecklist:
    """Класс для управления чеклистами анализа встреч"""
    
    def __init__(self):
        self.checklists = {
            'sales_meeting': {
                'name': 'Продажная встреча',
                'description': 'Анализ встреч с потенциальными клиентами',
                'items': [
                    {
                        'id': 'client_needs',
                        'question': 'Выявлены ли потребности клиента?',
                        'weight': 10,
                        'type': 'boolean'
                    },
                    {
                        'id': 'budget_discussed',
                        'question': 'Обсуждался ли бюджет проекта?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'timeline_defined',
                        'question': 'Определены ли сроки реализации?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'decision_maker_present',
                        'question': 'Присутствует ли лицо, принимающее решение?',
                        'weight': 9,
                        'type': 'boolean'
                    },
                    {
                        'id': 'next_steps_defined',
                        'question': 'Определены ли следующие шаги?',
                        'weight': 10,
                        'type': 'boolean'
                    },
                    {
                        'id': 'competitors_mentioned',
                        'question': 'Упоминались ли конкуренты?',
                        'weight': 6,
                        'type': 'boolean'
                    },
                    {
                        'id': 'objections_handled',
                        'question': 'Были ли обработаны возражения?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'client_interest_level',
                        'question': 'Какой уровень интереса клиента? (1-10)',
                        'weight': 10,
                        'type': 'scale'
                    },
                    {
                        'id': 'meeting_objective_achieved',
                        'question': 'Достигнута ли цель встречи?',
                        'weight': 10,
                        'type': 'boolean'
                    },
                    {
                        'id': 'follow_up_required',
                        'question': 'Требуется ли последующее взаимодействие?',
                        'weight': 7,
                        'type': 'boolean'
                    }
                ]
            },
            'project_meeting': {
                'name': 'Проектная встреча',
                'description': 'Анализ рабочих встреч по проектам',
                'items': [
                    {
                        'id': 'progress_reviewed',
                        'question': 'Был ли рассмотрен прогресс по проекту?',
                        'weight': 9,
                        'type': 'boolean'
                    },
                    {
                        'id': 'issues_identified',
                        'question': 'Выявлены ли проблемы/риски?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'solutions_discussed',
                        'question': 'Обсуждались ли решения проблем?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'tasks_assigned',
                        'question': 'Назначены ли задачи участникам?',
                        'weight': 10,
                        'type': 'boolean'
                    },
                    {
                        'id': 'deadlines_set',
                        'question': 'Установлены ли дедлайны?',
                        'weight': 9,
                        'type': 'boolean'
                    },
                    {
                        'id': 'resources_allocated',
                        'question': 'Распределены ли ресурсы?',
                        'weight': 7,
                        'type': 'boolean'
                    },
                    {
                        'id': 'stakeholders_updated',
                        'question': 'Информированы ли стейкхолдеры?',
                        'weight': 6,
                        'type': 'boolean'
                    },
                    {
                        'id': 'next_phase_planned',
                        'question': 'Запланирован ли следующий этап?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'meeting_effectiveness',
                        'question': 'Эффективность встречи (1-10)?',
                        'weight': 8,
                        'type': 'scale'
                    },
                    {
                        'id': 'action_items_clear',
                        'question': 'Понятны ли пункты действий?',
                        'weight': 9,
                        'type': 'boolean'
                    }
                ]
            },
            'team_meeting': {
                'name': 'Командная встреча',
                'description': 'Анализ внутренних командных встреч',
                'items': [
                    {
                        'id': 'attendance_complete',
                        'question': 'Присутствовали ли все необходимые участники?',
                        'weight': 7,
                        'type': 'boolean'
                    },
                    {
                        'id': 'agenda_followed',
                        'question': 'Соблюдалась ли повестка?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'participation_balanced',
                        'question': 'Было ли участие сбалансированным?',
                        'weight': 8,
                        'type': 'boolean'
                    },
                    {
                        'id': 'decisions_made',
                        'question': 'Были ли приняты решения?',
                        'weight': 9,
                        'type': 'boolean'
                    },
                    {
                        'id': 'conflicts_resolved',
                        'question': 'Были ли разрешены конфликты?',
                        'weight': 7,
                        'type': 'boolean'
                    },
                    {
                        'id': 'action_items_assigned',
                        'question': 'Назначены ли задачи?',
                        'weight': 10,
                        'type': 'boolean'
                    },
                    {
                        'id': 'time_management',
                        'question': 'Эффективное управление временем (1-10)?',
                        'weight': 8,
                        'type': 'scale'
                    },
                    {
                        'id': 'communication_quality',
                        'question': 'Качество коммуникации (1-10)?',
                        'weight': 9,
                        'type': 'scale'
                    },
                    {
                        'id': 'team_morale',
                        'question': 'Настроение команды (1-10)?',
                        'weight': 7,
                        'type': 'scale'
                    },
                    {
                        'id': 'follow_up_scheduled',
                        'question': 'Запланирована ли следующая встреча?',
                        'weight': 6,
                        'type': 'boolean'
                    }
                ]
            }
        }
    
    def get_checklist(self, checklist_type: str) -> Optional[Dict[str, Any]]:
        """Получить чеклист по типу"""
        return self.checklists.get(checklist_type)
    
    def get_available_checklists(self) -> List[str]:
        """Получить список доступных чеклистов"""
        return list(self.checklists.keys())
    
    def calculate_score(self, checklist_type: str, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитать оценку по чеклисту"""
        checklist = self.get_checklist(checklist_type)
        if not checklist:
            return {'error': 'Checklist not found'}
        
        total_weight = 0
        earned_weight = 0
        item_results = []
        
        for item in checklist['items']:
            item_id = item['id']
            weight = item['weight']
            total_weight += weight
            
            response = responses.get(item_id)
            
            if item['type'] == 'boolean':
                if response is True:
                    earned_weight += weight
                    item_results.append({
                        'item_id': item_id,
                        'question': item['question'],
                        'response': response,
                        'score': weight,
                        'max_score': weight
                    })
                else:
                    item_results.append({
                        'item_id': item_id,
                        'question': item['question'],
                        'response': response,
                        'score': 0,
                        'max_score': weight
                    })
            
            elif item['type'] == 'scale':
                if isinstance(response, (int, float)) and 1 <= response <= 10:
                    normalized_score = (response / 10) * weight
                    earned_weight += normalized_score
                    item_results.append({
                        'item_id': item_id,
                        'question': item['question'],
                        'response': response,
                        'score': normalized_score,
                        'max_score': weight
                    })
                else:
                    item_results.append({
                        'item_id': item_id,
                        'question': item['question'],
                        'response': response,
                        'score': 0,
                        'max_score': weight
                    })
        
        overall_score = (earned_weight / total_weight * 100) if total_weight > 0 else 0
        
        return {
            'checklist_type': checklist_type,
            'checklist_name': checklist['name'],
            'overall_score': round(overall_score, 2),
            'total_weight': total_weight,
            'earned_weight': round(earned_weight, 2),
            'item_results': item_results,
            'recommendation': self._generate_recommendation(overall_score, checklist_type)
        }
    
    def _generate_recommendation(self, score: float, checklist_type: str) -> str:
        """Сгенерировать рекомендацию на основе оценки"""
        if score >= 80:
            return "Отличная встреча! Цели достигнуты, высокая эффективность."
        elif score >= 60:
            return "Хорошая встреча. Есть возможности для улучшения."
        elif score >= 40:
            return "Удовлетворительная встреча. Требуется внимание к организации."
        else:
            return "Встреча требует значительных улучшений. Рекомендуется пересмотреть подход."

class MeetingAnalyzer:
    """Улучшенный анализатор встреч с чеклистами"""
    
    def __init__(self):
        self.checklist = MeetingChecklist()
        self.analysis_history = []
    
    def analyze_meeting(self, transcript: str, meeting_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Базовый метод анализа встречи (для совместимости)"""
        return self.analyze_meeting_with_checklist(
            transcript=transcript,
            checklist_type='sales_meeting',
            meeting_info=meeting_info
        )
    
    def analyze_meeting_with_checklist(self, 
                                    transcript: str,
                                    checklist_type: str = 'sales_meeting',
                                    meeting_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Проанализировать встречу с использованием чеклиста"""
        try:
            log.info(f"Начало анализа встречи с чеклистом: {checklist_type}")
            
            # Получение чеклиста
            checklist_data = self.checklist.get_checklist(checklist_type)
            if not checklist_data:
                log.error(f"Чеклист не найден: {checklist_type}")
                return {'error': f'Checklist {checklist_type} not found'}
            
            # Создание промпта для Gemini с чеклистом
            enhanced_prompt = self._build_enhanced_prompt(transcript, checklist_data)
            
            # Анализ через Gemini
            gemini_analysis = self._analyze_with_gemini(enhanced_prompt, transcript)
            
            if not gemini_analysis:
                log.error("Не удалось выполнить анализ через Gemini")
                return {'error': 'Gemini analysis failed'}
            
            # Извлечение ответов по чеклисту из анализа
            checklist_responses = self._extract_checklist_responses(gemini_analysis, checklist_data)
            
            # Расчет оценки по чеклисту
            checklist_score = self.checklist.calculate_score(checklist_type, checklist_responses)
            
            # Комбинированный результат
            analysis_result = {
                'meeting_info': meeting_info or {},
                'checklist_type': checklist_type,
                'checklist_name': checklist_data['name'],
                'transcript_summary': gemini_analysis.get('summary', ''),
                'gemini_analysis': gemini_analysis,
                'checklist_responses': checklist_responses,
                'checklist_score': checklist_score,
                'extracted_entities': self._extract_entities(gemini_analysis),
                'action_items': self._extract_action_items(gemini_analysis),
                'recommendations': self._generate_recommendations(gemini_analysis, checklist_score),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            # Сохранение в историю
            self.analysis_history.append(analysis_result)
            
            log.info(f"Анализ встречи завершен. Оценка: {checklist_score.get('overall_score', 0)}%")
            return analysis_result
            
        except Exception as e:
            log.error(f"Ошибка при анализе встречи: {e}")
            return {'error': str(e)}
    
    def _build_enhanced_prompt(self, transcript: str, checklist_data: Dict[str, Any]) -> str:
        """Построить улучшенный промпт для Gemini с чеклистом"""
        
        checklist_items_text = ""
        for item in checklist_data['items']:
            checklist_items_text += f"- {item['question']}\n"
        
        prompt = f"""
Проанализируй транскрипт бизнес-встречи и предоставь структурированный анализ.

Тип встречи: {checklist_data['name']}
Описание: {checklist_data['description']}

Чеклист для оценки (ответь на каждый вопрос):
{checklist_items_text}

Транскрипт встречи:
{transcript}

Предоставь анализ в формате JSON со следующей структурой:
{{
  "summary": "Краткое резюме встречи (2-3 предложения)",
  "participants": ["Участник 1", "Участник 2"],
  "key_topics": ["Тема 1", "Тема 2"],
  "decisions_made": ["Решение 1", "Решение 2"],
  "action_items": [
    {{
      "task": "Задача",
      "responsible": "Ответственный",
      "deadline": "Срок"
    }}
  ],
  "checklist_responses": {{
    "client_needs": true/false,
    "budget_discussed": true/false,
    "timeline_defined": true/false,
    "decision_maker_present": true/false,
    "next_steps_defined": true/false,
    "competitors_mentioned": true/false,
    "objections_handled": true/false,
    "client_interest_level": 1-10,
    "meeting_objective_achieved": true/false,
    "follow_up_required": true/false
  }},
  "extracted_data": {{
    "company": "Название компании",
    "contact_person": "Контактное лицо",
    "budget": "Бюджет",
    "timeline": "Сроки",
    "priority": "Приоритет",
    "status": "Статус"
  }},
  "sentiment": "positive/neutral/negative",
  "risk_level": "low/medium/high",
  "next_steps": ["Следующий шаг 1", "Следующий шаг 2"]
}}

Особое внимание удели:
1. Точности ответов на вопросы чеклиста
2. Выявлению конкретных задач и ответственных
3. Определению ключевых показателей (бюджет, сроки, приоритет)
4. Оценке общего тона и результата встречи
"""
        
        return prompt
    
    def _analyze_with_gemini(self, prompt: str, transcript: str) -> Optional[Dict[str, Any]]:
        """Выполнить анализ через Gemini"""
        try:
            # Используем существующую функцию из gemini_client
            result = analyze_transcript_structured(transcript)
            
            if result:
                # Дополнительная обработка для чеклиста
                enhanced_result = {
                    'summary': result.get('summary', ''),
                    'participants': result.get('participants', []),
                    'key_topics': result.get('key_topics', []),
                    'decisions_made': result.get('decisions_made', []),
                    'action_items': result.get('action_items', []),
                    'checklist_responses': self._generate_checklist_responses_from_analysis(result),
                    'extracted_data': result.get('extracted_data', {}),
                    'sentiment': result.get('sentiment', 'neutral'),
                    'risk_level': result.get('risk_level', 'medium'),
                    'next_steps': result.get('next_steps', [])
                }
                return enhanced_result
            
            return None
            
        except Exception as e:
            log.error(f"Ошибка при анализе через Gemini: {e}")
            return None
    
    def _generate_checklist_responses_from_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Сгенерировать ответы чеклиста на основе анализа"""
        responses = {}
        
        # Базовые ответы на основе анализа
        responses['client_needs'] = bool(analysis.get('key_topics'))
        responses['budget_discussed'] = bool(analysis.get('extracted_data', {}).get('budget'))
        responses['timeline_defined'] = bool(analysis.get('extracted_data', {}).get('timeline'))
        responses['decision_maker_present'] = len(analysis.get('participants', [])) > 1
        responses['next_steps_defined'] = bool(analysis.get('next_steps'))
        responses['competitors_mentioned'] = False  # По умолчанию
        responses['objections_handled'] = analysis.get('sentiment') != 'negative'
        responses['client_interest_level'] = 7 if analysis.get('sentiment') == 'positive' else 5
        responses['meeting_objective_achieved'] = bool(analysis.get('decisions_made'))
        responses['follow_up_required'] = bool(analysis.get('action_items'))
        
        return responses
    
    def _extract_checklist_responses(self, gemini_analysis: Dict[str, Any], 
                                   checklist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечь ответы по чеклисту из анализа"""
        # Если в анализе уже есть ответы чеклиста, используем их
        if 'checklist_responses' in gemini_analysis:
            return gemini_analysis['checklist_responses']
        
        # Иначе генерируем на основе анализа
        return self._generate_checklist_responses_from_analysis(gemini_analysis)
    
    def _extract_entities(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечь сущности из анализа"""
        return analysis.get('extracted_data', {})
    
    def _extract_action_items(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Извлечь пункты действий из анализа"""
        return analysis.get('action_items', [])
    
    def _generate_recommendations(self, analysis: Dict[str, Any], 
                                 checklist_score: Dict[str, Any]) -> List[str]:
        """Сгенерировать рекомендации"""
        recommendations = []
        
        # Рекомендации на основе оценки чеклиста
        score = checklist_score.get('overall_score', 0)
        if score < 60:
            recommendations.append("Рекомендуется улучшить планирование и подготовку к встречам")
        
        # Рекомендации на основе анализа
        sentiment = analysis.get('sentiment', 'neutral')
        if sentiment == 'negative':
            recommendations.append("Обратить внимание на коммуникацию и решение проблем")
        
        risk_level = analysis.get('risk_level', 'medium')
        if risk_level == 'high':
            recommendations.append("Требуется дополнительное внимание к рискам проекта")
        
        # Рекомендации на основе пунктов действий
        action_items = analysis.get('action_items', [])
        if not action_items:
            recommendations.append("Определить конкретные задачи и ответственных")
        
        return recommendations
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Получить текстовое резюме анализа"""
        try:
            checklist_score = analysis_result.get('checklist_score', {})
            overall_score = checklist_score.get('overall_score', 0)
            
            summary = f"""
📊 Анализ встречи завершен

🎯 Тип встречи: {analysis_result.get('checklist_name', 'Unknown')}
📈 Общая оценка: {overall_score}%

📋 Ключевые моменты:
- Участники: {', '.join(analysis_result.get('gemini_analysis', {}).get('participants', []))}
- Основные темы: {', '.join(analysis_result.get('gemini_analysis', {}).get('key_topics', []))}
- Настроение: {analysis_result.get('gemini_analysis', {}).get('sentiment', 'neutral')}
- Уровень риска: {analysis_result.get('gemini_analysis', {}).get('risk_level', 'medium')}

✅ Решения: {len(analysis_result.get('gemini_analysis', {}).get('decisions_made', []))}
📝 Задачи: {len(analysis_result.get('action_items', []))}

💡 Рекомендации:
{chr(10).join(f'- {rec}' for rec in analysis_result.get('recommendations', []))}
"""
            
            return summary.strip()
            
        except Exception as e:
            log.error(f"Ошибка при формировании резюме: {e}")
            return "Ошибка при формировании резюме анализа"
    
    def get_available_checklists(self) -> List[Dict[str, Any]]:
        """Получить информацию о доступных чеклистах"""
        checklists_info = []
        for key, checklist in self.checklist.checklists.items():
            checklists_info.append({
                'type': key,
                'name': checklist['name'],
                'description': checklist['description'],
                'items_count': len(checklist['items'])
            })
        return checklists_info
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Получить историю анализов"""
        return self.analysis_history
    
    def export_analysis(self, analysis_result: Dict[str, Any], 
                       output_format: str = "json",
                       output_file: Optional[str] = None) -> Optional[str]:
        """Экспортировать анализ в файл"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"meeting_analysis_{timestamp}.{output_format}"
            
            if output_format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            elif output_format.lower() == "txt":
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(self.get_analysis_summary(analysis_result))
            
            log.info(f"Анализ экспортирован в файл: {output_file}")
            return output_file
            
        except Exception as e:
            log.error(f"Ошибка при экспорте анализа: {e}")
            return None

# Функция для создания экземпляра анализатора
def create_meeting_analyzer() -> MeetingAnalyzer:
    """Создать экземпляр анализатора встреч"""
    return MeetingAnalyzer()
