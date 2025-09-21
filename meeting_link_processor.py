"""
Модуль обработки ссылок на встречи и автоматического участия
"""
import os
import logging
import threading
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse

from config import config
from aggressive_meeting_automation import AggressiveMeetingAutomation
from speech_transcriber import SpeechTranscriber
from meeting_analyzer import MeetingAnalyzer
from bitrix_meeting_integration import update_lead_from_meeting_analysis, create_meeting_follow_up_tasks
from platform_detector import MeetingPlatformDetector

log = logging.getLogger(__name__)

class MeetingLinkProcessor:
    """Класс для обработки ссылок на встречи и автоматического участия"""
    
    def __init__(self):
        self.meeting_automation = AggressiveMeetingAutomation()
        self.speech_transcriber = SpeechTranscriber()
        self.meeting_analyzer = MeetingAnalyzer()
        self.platform_detector = MeetingPlatformDetector()
        self.active_meetings = {}  # {chat_id: meeting_info}
        self.meeting_threads = {}  # {chat_id: thread}
        
    def process_meeting_link(self, meeting_url: str, chat_id: int, initiator_name: str = "Пользователь") -> Dict[str, Any]:
        """
        Обработка ссылки на встречу и запуск автоматического участия
        """
        result = {
            'success': False,
            'message': '',
            'meeting_id': None,
            'platform': None,
            'analysis': None,
            'lead_update_result': None
        }
        
        try:
            log.info(f"Получена ссылка на встречу от {initiator_name} (chat_id: {chat_id}): {meeting_url}")
            
            # Валидация URL
            if not self._validate_meeting_url(meeting_url):
                result['message'] = "❌ Некорректная ссылка на встречу. Пожалуйста, отправьте действительную ссылку."
                return result
            
            # Определение платформы
            platform = self.platform_detector.detect_platform(meeting_url)
            if not platform:
                result['message'] = "❌ Не удалось определить платформу встречи. Поддерживаются: Zoom, Google Meet, Teams, Контур.Толк"
                return result
            
            # Проверка, нет ли уже активной встречи для этого чата
            if chat_id in self.active_meetings:
                active_meeting = self.active_meetings[chat_id]
                result['message'] = f"❌ У вас уже есть активная встреча на платформе {active_meeting['platform']}. Дождитесь ее завершения."
                return result
            
            # Создание уникального ID встречи
            meeting_id = f"{chat_id}_{int(time.time())}"
            
            # Инициализация компонентов
            if not self._initialize_components():
                result['message'] = "❌ Не удалось инициализировать компоненты для участия во встрече."
                return result
            
            # Сохранение информации о встрече
            meeting_info = {
                'meeting_id': meeting_id,
                'url': meeting_url,
                'platform': platform,
                'chat_id': chat_id,
                'initiator_name': initiator_name,
                'start_time': datetime.now(),
                'status': 'joining',
                'transcript': '',
                'analysis': None
            }
            
            self.active_meetings[chat_id] = meeting_info
            
            # Отправка уведомления о начале процесса
            self._send_notification(chat_id, f"🚀 Начинаю присоединение к встрече на платформе {platform['platform_name']}...")
            
            # Запуск встречи в отдельном потоке
            meeting_thread = threading.Thread(
                target=self._run_meeting,
                args=(meeting_info,),
                daemon=True
            )
            meeting_thread.start()
            
            self.meeting_threads[chat_id] = meeting_thread
            
            result['success'] = True
            result['message'] = f"✅ Запущено присоединение к встрече на {platform['platform_name']}. Я сообщу о прогрессе."
            result['meeting_id'] = meeting_id
            result['platform'] = platform
            
        except Exception as e:
            log.error(f"Ошибка при обработке ссылки на встречу: {e}")
            result['message'] = f"❌ Ошибка при обработке ссылки: {e}"
            
            # Очистка при ошибке
            if chat_id in self.active_meetings:
                del self.active_meetings[chat_id]
        
        return result
    
    def _run_meeting(self, meeting_info: Dict[str, Any]):
        """
        Основной метод запуска и обработки встречи
        """
        chat_id = meeting_info['chat_id']
        meeting_url = meeting_info['url']
        platform = meeting_info['platform']
        
        try:
            # Шаг 1: Присоединение к встрече
            self._send_notification(chat_id, "🔗 Присоединяюсь к встрече...")
            
            # Используем агрессивную автоматизацию для присоединения
            join_success = self.meeting_automation.join_meeting_aggressive(meeting_url)
            
            if not join_success:
                meeting_info['status'] = 'failed'
                self._send_notification(chat_id, "❌ Не удалось присоединиться к встрече.")
                self._cleanup_meeting(chat_id)
                return
            
            meeting_info['status'] = 'in_meeting'
            self._send_notification(chat_id, "✅ Успешно присоединился к встрече. Начинаю запись...")
            
            # Шаг 2: Начало записи аудио
            self._send_notification(chat_id, "🎙️ Начинаю запись аудио...")
            
            # Используем аудиозапись из агрессивной автоматизации (parecord)
            audio_success = self.meeting_automation.start_audio_recording()
            if not audio_success:
                meeting_info['status'] = 'audio_failed'
                self._send_notification(chat_id, "❌ Не удалось начать запись аудио.")
                self._cleanup_meeting(chat_id)
                return
            
            meeting_info['status'] = 'recording'
            self._send_notification(chat_id, "⏱️ Запись аудио начата. Буду записывать встречу...")
            
            # Шаг 3: Ожидание окончания встречи
            self._send_notification(chat_id, f"⏳ Запись встречи в процессе... Максимальная длительность: {config.MEETING_DURATION_MINUTES} минут")
            
            start_time = time.time()
            max_duration = config.MEETING_DURATION_MINUTES * 60
            last_status_check = start_time
            meeting_ended = False
            
            while time.time() - start_time < max_duration:
                try:
                    # Проверка, все еще ли мы в встречи
                    current_time = time.time()
                    if current_time - last_status_check >= 30:  # Проверка каждые 30 секунд
                        in_meeting = self.meeting_automation.is_in_meeting()
                        last_status_check = current_time
                        
                        if not in_meeting:
                            self._send_notification(chat_id, "📤 Встреча завершена. Прекращаю запись...")
                            meeting_ended = True
                            break
                        
                        # Периодические уведомления о статусе
                        elapsed_minutes = int((current_time - start_time) / 60)
                        if elapsed_minutes > 0 and elapsed_minutes % 5 == 0:
                            self._send_notification(chat_id, f"⏱️ Запись продолжается... Прошло {elapsed_minutes} минут")
                    
                    # Короткая пауза для снижения нагрузки
                    time.sleep(5)
                    
                except Exception as e:
                    log.error(f"Ошибка при проверке статуса встречи: {e}")
                    # Если ошибка при проверке, считаем что встреча завершена
                    meeting_ended = True
                    break
            
            # Если встреча не завершилась принудительно, но достигнут лимит времени
            if not meeting_ended and time.time() - start_time >= max_duration:
                self._send_notification(chat_id, f"⏰ Достигнут лимит времени ({config.MEETING_DURATION_MINUTES} минут). Прекращаю запись...")
                meeting_ended = True
            
            # Шаг 4: Выход из встречи и остановка записи
            self._send_notification(chat_id, "🚪 Выхожу из встречи...")
            try:
                leave_success = self.meeting_automation.leave_meeting()
                if leave_success:
                    self._send_notification(chat_id, "✅ Успешно вышел из встречи.")
                else:
                    self._send_notification(chat_id, "⚠️ Не удалось корректно выйти из встречи, но продолжаю обработку...")
            except Exception as e:
                log.error(f"Ошибка при выходе из встречи: {e}")
                self._send_notification(chat_id, "⚠️ Ошибка при выходе из встречи, но продолжаю обработку...")
            
            # Шаг 5: Остановка записи
            self._send_notification(chat_id, "⏹️ Останавливаю запись аудио...")
            audio_file = self.meeting_automation.stop_audio_recording()
            
            if not audio_file:
                meeting_info['status'] = 'no_audio'
                self._send_notification(chat_id, "❌ Не удалось получить записанный аудиофайл.")
                self._cleanup_meeting(chat_id)
                return
            
            # Проверяем, что файл существует
            if not os.path.exists(audio_file):
                meeting_info['status'] = 'no_audio'
                self._send_notification(chat_id, "❌ Аудиофайл не найден.")
                self._cleanup_meeting(chat_id)
                return
            
            meeting_info['status'] = 'processing'
            self._send_notification(chat_id, "📝 Начинаю транскрипцию аудио...")
            
            # Шаг 6: Транскрипция аудио
            self._send_notification(chat_id, "🎤 Начинаю транскрипцию аудио...")
            
            # Проверяем существование файла
            if not os.path.exists(audio_file):
                meeting_info['status'] = 'transcription_failed'
                self._send_notification(chat_id, f"❌ Аудиофайл не найден: {audio_file}")
                self._cleanup_meeting(chat_id)
                return
            
            # Проверяем размер файла
            file_size = os.path.getsize(audio_file)
            if file_size < 1024:  # Меньше 1KB
                meeting_info['status'] = 'transcription_failed'
                self._send_notification(chat_id, "❌ Аудиофайл слишком мал, возможно запись не удалась")
                self._cleanup_meeting(chat_id)
                return
            
            self._send_notification(chat_id, f"📁 Размер аудиофайла: {file_size / 1024:.1f} KB")
            
            try:
                transcript_result = self.speech_transcriber.transcribe_file(audio_file)
                
                if not transcript_result or not transcript_result.get('text'):
                    meeting_info['status'] = 'transcription_failed'
                    self._send_notification(chat_id, "❌ Не удалось выполнить транскрипцию аудио.")
                    self._cleanup_meeting(chat_id)
                    return
                
                transcript_text = transcript_result['text']
                if len(transcript_text.strip()) < 10:
                    meeting_info['status'] = 'transcription_failed'
                    self._send_notification(chat_id, "❌ Транскрипт слишком короткий, возможно аудио не содержит речи")
                    self._cleanup_meeting(chat_id)
                    return
                
                meeting_info['transcript'] = transcript_text
                self._send_notification(chat_id, f"✅ Транскрипция завершена! Длина: {len(transcript_text)} символов")
                
            except Exception as e:
                meeting_info['status'] = 'transcription_failed'
                self._send_notification(chat_id, f"❌ Ошибка транскрипции: {str(e)}")
                self._cleanup_meeting(chat_id)
                return
            
            self._send_notification(chat_id, f"✅ Транскрипция завершена. Длина: {len(transcript_text)} символов.")
            
            # Шаг 7: Анализ встречи с чек-листом
            self._send_notification(chat_id, "🧠 Начинаю анализ встречи с использованием чек-листа...")
            
            try:
                # Используем MeetingAnalyzer для анализа с чек-листом
                from meeting_analyzer import MeetingAnalyzer
                analyzer = MeetingAnalyzer()
                
                # Анализируем встречу с чек-листом
                analysis_result = analyzer.analyze_meeting_with_checklist(
                    transcript_text, 
                    checklist_type='sales_meeting'  # Можно настроить тип чек-листа
                )
                
                if not analysis_result:
                    meeting_info['status'] = 'analysis_failed'
                    self._send_notification(chat_id, "❌ Не удалось выполнить анализ встречи.")
                    self._cleanup_meeting(chat_id)
                    return
                
                meeting_info['analysis'] = analysis_result
                meeting_info['status'] = 'analyzed'
                
                # Отправляем краткий отчет о результатах
                score = analysis_result.get('score', 0)
                self._send_notification(chat_id, f"✅ Анализ завершен! Оценка встречи: {score}/100 баллов")
                
            except Exception as e:
                log.error(f"Ошибка анализа встречи: {e}")
                meeting_info['status'] = 'analysis_failed'
                self._send_notification(chat_id, f"❌ Ошибка анализа встречи: {e}")
                self._cleanup_meeting(chat_id)
                return
            
            # Шаг 8: Отправка анализа пользователю
            self._send_analysis_to_user(chat_id, analysis_result)
            
            # Отправляем детальный анализ
            self._send_detailed_analysis(chat_id, analysis_result)
            
            # Шаг 9: Запрос ID лида
            self._send_notification(chat_id, "🔍 Пожалуйста, отправьте ID лида в Bitrix24 для обновления:")
            
            # Шаг 10: Уведомление администратора
            self._notify_admin(meeting_info)
            
        except Exception as e:
            log.error(f"Ошибка при проведении встречи: {e}")
            meeting_info['status'] = 'error'
            self._send_notification(chat_id, f"❌ Ошибка при проведении встречи: {e}")
            self._notify_admin_about_error(meeting_info, str(e))
        
        finally:
            # Шаг 11: Выход из встречи и очистка
            if config.MEETING_AUTO_LEAVE:
                self._send_notification(chat_id, "🚪 Выхожу из встречи...")
                self.meeting_automation.leave_meeting()
            
            # Не удаляем из active_meetings, ждем ID лида от пользователя
            meeting_info['status'] = 'awaiting_lead_id'
    
    def update_lead_from_meeting(self, chat_id: int, lead_id: str) -> Dict[str, Any]:
        """
        Обновление лида на основе анализа встречи
        """
        result = {
            'success': False,
            'message': '',
            'lead_update_result': None
        }
        
        try:
            # Проверка наличия анализа для этого чата
            if chat_id not in self.active_meetings:
                result['message'] = "❌ Не найден анализ встречи для этого чата."
                return result
            
            meeting_info = self.active_meetings[chat_id]
            analysis = meeting_info.get('analysis')
            
            if not analysis:
                result['message'] = "❌ Анализ встречи не найден."
                return result
            
            # Обновление лида
            self._send_notification(chat_id, f"🔄 Обновляю лид {lead_id} на основе анализа встречи...")
            
            try:
                lead_update_result = update_lead_from_meeting_analysis(lead_id, analysis)
                
                if lead_update_result.get('updated') or lead_update_result.get('meeting_data_processed'):
                    result['success'] = True
                    result['message'] = f"✅ Лид {lead_id} успешно обновлен!"
                    result['lead_update_result'] = lead_update_result
                    
                    # Дополнительная информация
                    if lead_update_result.get('task_created'):
                        tasks = lead_update_result.get('tasks', [])
                        if tasks:
                            task_info = f"Создано задач: {len(tasks)}"
                            for task in tasks[:3]:  # Показываем только первые 3
                                task_info += f"\n• {task.get('title', 'Без названия')}"
                            result['message'] += f"\n\n📋 {task_info}"
                    
                    if lead_update_result.get('comment_updated'):
                        result['message'] += "\n💬 Комментарий обновлен"
                    
                    # Показываем обновленные поля
                    fields_updated = lead_update_result.get('fields_updated', [])
                    if fields_updated:
                        fields_info = f"Обновлено полей: {len(fields_updated)}"
                        for field in fields_updated[:5]:  # Показываем только первые 5
                            fields_info += f"\n• {field}"
                        result['message'] += f"\n\n📝 {fields_info}"
                    
                    # Уведомление администратора об успешном обновлении
                    self._notify_admin_about_lead_update(meeting_info, lead_id, lead_update_result)
                    
                    # Очистка после успешного обновления
                    self._cleanup_meeting(chat_id)
                    
                else:
                    result['message'] = f"⚠️ Не удалось обновить лид {lead_id}. Проверьте ID и попробуйте снова."
                    result['lead_update_result'] = lead_update_result
                    
            except Exception as e:
                log.error(f"Ошибка при обновлении лида {lead_id}: {e}")
                result['message'] = f"❌ Ошибка при обновлении лида: {e}"
            
        except Exception as e:
            log.error(f"Ошибка при обновлении лида: {e}")
            result['message'] = f"❌ Ошибка при обновлении лида: {e}"
        
        return result
    
    def _validate_meeting_url(self, url: str) -> bool:
        """
        Валидация URL встречи
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Проверка на поддерживаемые платформы
            supported_domains = [
                'zoom.us', 'meet.google.com', 'teams.microsoft.com', 
                'talk.kontur.ru', 'ktalk.ru', 'telemost.yandex.ru'
            ]
            
            return any(domain in parsed.netloc.lower() for domain in supported_domains)
            
        except Exception:
            return False
    
    def _initialize_components(self) -> bool:
        """
        Инициализация компонентов для участия во встрече
        """
        try:
            # Инициализация автоматизации встреч
            if not self.meeting_automation:
                self.meeting_automation = meeting_automation

            # Инициализация транскрибера
            if not self.speech_transcriber:
                self.speech_transcriber = SpeechTranscriber()

            # Инициализация анализатора
            if not self.meeting_analyzer:
                self.meeting_analyzer = MeetingAnalyzer()

            return True

        except Exception as e:
            log.error(f"Ошибка при инициализации компонентов: {e}")
            return False
    
    def _send_notification(self, chat_id: int, message: str):
        """
        Отправка уведомления в Telegram
        """
        try:
            # Импортируем здесь, чтобы избежать циклического импорта
            from main import send_message
            send_message(chat_id, message)
        except Exception as e:
            log.error(f"Ошибка при отправке уведомления в чат {chat_id}: {e}")
    
    def _send_analysis_to_user(self, chat_id: int, analysis: Dict[str, Any]):
        """
        Отправка анализа встречи пользователю
        """
        try:
            # Форматирование анализа для отправки
            analysis_text = self._format_analysis_for_telegram(analysis)
            self._send_notification(chat_id, analysis_text)
        except Exception as e:
            log.error(f"Ошибка при отправке анализа пользователю: {e}")
    
    def _send_detailed_analysis(self, chat_id: int, analysis: Dict[str, Any]):
        """
        Отправка детального анализа с чек-листом
        """
        try:
            # Основные результаты
            score = analysis.get('score', 0)
            checklist_responses = analysis.get('checklist_responses', {})
            
            message = f"📊 **Детальный анализ встречи**\n\n"
            message += f"🎯 **Общая оценка: {score}/100 баллов**\n\n"
            
            # Результаты чек-листа
            if checklist_responses:
                message += "📋 **Результаты чек-листа:**\n"
                for item, response in checklist_responses.items():
                    status = "✅" if response else "❌"
                    message += f"{status} {item}\n"
                message += "\n"
            
            # Ключевые выводы
            key_findings = analysis.get('key_findings', [])
            if key_findings:
                message += "🔍 **Ключевые выводы:**\n"
                for finding in key_findings[:5]:  # Показываем только первые 5
                    message += f"• {finding}\n"
                message += "\n"
            
            # Рекомендации
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                message += "💡 **Рекомендации:**\n"
                for rec in recommendations[:3]:  # Показываем только первые 3
                    message += f"• {rec}\n"
            
            self._send_notification(chat_id, message)
            
        except Exception as e:
            log.error(f"Ошибка при отправке детального анализа: {e}")
            self._send_notification(chat_id, f"❌ Ошибка при отправке детального анализа: {e}")
    
    def _format_analysis_for_telegram(self, analysis: Dict[str, Any]) -> str:
        """
        Форматирование анализа для отправки в Telegram
        """
        try:
            lines = []
            lines.append("📊 **Анализ встречи завершен!**")
            lines.append("=" * 40)
            lines.append("")
            
            # Основная информация
            meeting_info = analysis.get('meeting_info', {})
            if meeting_info:
                lines.append(f"📅 **Платформа:** {meeting_info.get('platform', 'Unknown')}")
                lines.append(f"⏰ **Время:** {meeting_info.get('start_time', 'N/A')}")
                lines.append("")
            
            # Оценка
            checklist_score = analysis.get('checklist_score', {})
            if checklist_score:
                overall_score = checklist_score.get('overall_score', 0)
                checklist_name = checklist_score.get('checklist_name', 'Unknown')
                
                lines.append(f"📈 **Тип встречи:** {checklist_name}")
                lines.append(f"🎯 **Общая оценка:** {overall_score}%")
                
                if overall_score >= 80:
                    lines.append("✅ **Результат:** Отлично")
                elif overall_score >= 60:
                    lines.append("🟡 **Результат:** Хорошо")
                else:
                    lines.append("🔔 **Результат:** Требует внимания")
                
                lines.append("")
            
            # Ключевые темы
            gemini_analysis = analysis.get('gemini_analysis', {})
            key_topics = gemini_analysis.get('key_topics', [])
            if key_topics:
                lines.append("🎯 **Ключевые темы:**")
                for topic in key_topics[:5]:  # Максимум 5 тем
                    lines.append(f"• {topic}")
                lines.append("")
            
            # Решения
            decisions = gemini_analysis.get('decisions_made', [])
            if decisions:
                lines.append("✅ **Решения:**")
                for decision in decisions[:3]:  # Максимум 3 решения
                    lines.append(f"• {decision}")
                lines.append("")
            
            # Пункты действий
            action_items = analysis.get('action_items', [])
            if action_items:
                lines.append("📝 **Пункты действий:**")
                for item in action_items[:3]:  # Максимум 3 пункта
                    task = item.get('task', '')
                    responsible = item.get('responsible', 'N/A')
                    lines.append(f"• {task}")
                    if responsible != 'N/A':
                        lines.append(f"  - Ответственный: {responsible}")
                lines.append("")
            
            # Рекомендации
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                lines.append("💡 **Рекомендации:**")
                for rec in recommendations[:3]:  # Максимум 3 рекомендации
                    lines.append(f"• {rec}")
                lines.append("")
            
            # Настроение
            sentiment = gemini_analysis.get('sentiment', 'neutral')
            risk_level = gemini_analysis.get('risk_level', 'medium')
            
            lines.append("🎭 **Анализ тональности:**")
            lines.append(f"• Настроение: {sentiment}")
            lines.append(f"• Уровень риска: {risk_level}")
            lines.append("")
            
            lines.append("🔍 **Пожалуйста, отправьте ID лида для обновления в Bitrix24:**")
            
            return "\n".join(lines)
            
        except Exception as e:
            log.error(f"Ошибка при форматировании анализа: {e}")
            return f"Анализ встречи получен. Ошибка форматирования: {e}"
    
    def _notify_admin(self, meeting_info: Dict[str, Any]):
        """
        Уведомление администратора о проведенной встрече
        """
        try:
            admin_chat_id = config.ADMIN_CHAT_ID
            if not admin_chat_id:
                return
            
            analysis = meeting_info.get('analysis')
            if not analysis:
                return
            
            # Форматирование сообщения для администратора
            message_lines = [
                "🔔 **Уведомление о встрече**",
                "=" * 30,
                "",
                f"👤 **Инициатор:** {meeting_info.get('initiator_name', 'Unknown')}",
                f"💬 **Chat ID:** {meeting_info.get('chat_id', 'Unknown')}",
                f"🌐 **Платформа:** {meeting_info.get('platform', {}).get('platform_name', 'Unknown')}",
                f"⏰ **Время начала:** {meeting_info.get('start_time', 'N/A')}",
                f"📊 **Статус:** {meeting_info.get('status', 'Unknown')}",
                ""
            ]
            
            # Добавление ключевой информации из анализа
            if analysis:
                checklist_score = analysis.get('checklist_score', {})
                overall_score = checklist_score.get('overall_score', 0)
                
                message_lines.extend([
                    f"📈 **Оценка встречи:** {overall_score}%",
                    ""
                ])
                
                # Ключевые темы
                gemini_analysis = analysis.get('gemini_analysis', {})
                key_topics = gemini_analysis.get('key_topics', [])
                if key_topics:
                    message_lines.append("🎯 **Ключевые темы:**")
                    for topic in key_topics[:3]:
                        message_lines.append(f"• {topic}")
                    message_lines.append("")
                
                # Пункты действий
                action_items = analysis.get('action_items', [])
                if action_items:
                    message_lines.append("📝 **Пункты действий:**")
                    for item in action_items[:3]:
                        task = item.get('task', '')
                        message_lines.append(f"• {task}")
                    message_lines.append("")
            
            message_lines.append("⏳ **Ожидается ID лида для обновления...**")
            
            admin_message = "\n".join(message_lines)
            self._send_notification(int(admin_chat_id), admin_message)
            
        except Exception as e:
            log.error(f"Ошибка при уведомлении администратора: {e}")
    
    def _notify_admin_about_lead_update(self, meeting_info: Dict[str, Any], lead_id: str, update_result: Dict[str, Any]):
        """
        Уведомление администратора об обновлении лида
        """
        try:
            admin_chat_id = config.ADMIN_CHAT_ID
            if not admin_chat_id:
                return
            
            message_lines = [
                "✅ **Лид успешно обновлен!**",
                "=" * 30,
                "",
                f"👤 **Инициатор:** {meeting_info.get('initiator_name', 'Unknown')}",
                f"💬 **Chat ID:** {meeting_info.get('chat_id', 'Unknown')}",
                f"🔢 **ID лида:** {lead_id}",
                f"🌐 **Платформа:** {meeting_info.get('platform', {}).get('platform_name', 'Unknown')}",
                ""
            ]
            
            # Результаты обновления
            if update_result.get('updated'):
                message_lines.append("✅ **Поля лида обновлены**")
            
            if update_result.get('comment_updated'):
                message_lines.append("💬 **Комментарий добавлен**")
            
            if update_result.get('task_created'):
                tasks = update_result.get('tasks', [])
                message_lines.append(f"🗓 **Создано задач:** {len(tasks)}")
                for task in tasks:
                    message_lines.append(f"  • {task.get('title', 'Unknown')} (ID: {task.get('id', 'N/A')})")
            
            admin_message = "\n".join(message_lines)
            self._send_notification(int(admin_chat_id), admin_message)
            
        except Exception as e:
            log.error(f"Ошибка при уведомлении администратора об обновлении лида: {e}")
    
    def _notify_admin_about_error(self, meeting_info: Dict[str, Any], error_message: str):
        """
        Уведомление администратора об ошибке
        """
        try:
            admin_chat_id = config.ADMIN_CHAT_ID
            if not admin_chat_id:
                return
            
            message_lines = [
                "❌ **Ошибка при проведении встречи!**",
                "=" * 30,
                "",
                f"👤 **Инициатор:** {meeting_info.get('initiator_name', 'Unknown')}",
                f"💬 **Chat ID:** {meeting_info.get('chat_id', 'Unknown')}",
                f"🌐 **Платформа:** {meeting_info.get('platform', {}).get('platform_name', 'Unknown')}",
                f"⏰ **Время начала:** {meeting_info.get('start_time', 'N/A')}",
                f"📊 **Статус:** {meeting_info.get('status', 'Unknown')}",
                "",
                f"🚨 **Ошибка:** {error_message}",
                ""
            ]
            
            admin_message = "\n".join(message_lines)
            self._send_notification(int(admin_chat_id), admin_message)
            
        except Exception as e:
            log.error(f"Ошибка при уведомлении администратора об ошибке: {e}")
    
    def _cleanup_meeting(self, chat_id: int):
        """
        Очистка ресурсов после встречи
        """
        try:
            # Удаление из активных встреч
            if chat_id in self.active_meetings:
                del self.active_meetings[chat_id]
            
            # Удаление потоков
            if chat_id in self.meeting_threads:
                del self.meeting_threads[chat_id]
            
            log.info(f"Очистка ресурсов для чата {chat_id} завершена")
            
        except Exception as e:
            log.error(f"Ошибка при очистке ресурсов: {e}")
    
    def get_active_meetings(self) -> Dict[str, Any]:
        """
        Получение информации об активных встречах
        """
        return self.active_meetings.copy()
    
    def get_meeting_status(self, chat_id: int) -> Optional[str]:
        """
        Получение статуса встречи для чата
        """
        if chat_id in self.active_meetings:
            return self.active_meetings[chat_id].get('status')
        return None

# Глобальный экземпляр процессора
meeting_link_processor = MeetingLinkProcessor()
