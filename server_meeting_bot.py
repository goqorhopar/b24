"""
Серверный бот для автоматизации встреч
Подключается к встречам как "Асистент Григория", записывает, транскрибирует и анализирует
"""
import os
import logging
import threading
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import tempfile
import subprocess
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import config
from gemini_client import analyze_transcript_structured
from bitrix import update_lead_comprehensive
from speech_transcriber import SpeechTranscriber
from audio_capture import MeetingAudioRecorder

log = logging.getLogger(__name__)

class ServerMeetingBot:
    """Основной класс серверного бота для автоматизации встреч"""
    
    def __init__(self):
        self.driver = None
        self.audio_recorder = None
        self.speech_transcriber = None
        self.active_meetings = {}
        self.meeting_threads = {}
        self.display_name = config.MEETING_DISPLAY_NAME or "Асистент Григория"
        
        # Инициализация компонентов
        self._initialize_components()
    
    def _initialize_components(self):
        """Инициализация всех необходимых компонентов"""
        try:
            # Инициализация аудиорекордера
            self.audio_recorder = MeetingAudioRecorder(recording_method="auto")
            log.info("Аудиорекордер инициализирован")
            
            # Инициализация транскрибера
            self.speech_transcriber = SpeechTranscriber(
                model_name="base",  # Быстрая модель для сервера
                language="ru"
            )
            log.info("Транскрибер инициализирован")
            
        except Exception as e:
            log.error(f"Ошибка при инициализации компонентов: {e}")
    
    def setup_driver(self) -> bool:
        """Настройка WebDriver для серверного режима"""
        try:
            chrome_options = Options()
            
            # Серверный режим (без GUI)
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Настройки для аудио
            chrome_options.add_argument('--use-fake-ui-for-media-stream')
            chrome_options.add_argument('--allow-file-access-from-files')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Отключение изображений для экономии трафика
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.media_stream": 1,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            log.info("WebDriver успешно настроен для серверного режима")
            return True
            
        except Exception as e:
            log.error(f"Ошибка при настройке WebDriver: {e}")
            return False
    
    def detect_platform(self, meeting_url: str) -> Optional[str]:
        """Определение платформы встречи"""
        try:
            parsed = urlparse(meeting_url)
            domain = parsed.netloc.lower()
            
            if 'zoom.us' in domain:
                return 'zoom'
            elif 'meet.google.com' in domain:
                return 'google_meet'
            elif 'teams.microsoft.com' in domain:
                return 'teams'
            elif 'talk.kontur.ru' in domain or 'ktalk.ru' in domain:
                return 'kontur_talk'
            elif 'telemost.yandex.ru' in domain:
                return 'yandex_telemost'
            
            return None
            
        except Exception as e:
            log.error(f"Ошибка при определении платформы: {e}")
            return None
    
    def join_meeting(self, meeting_url: str, chat_id: int) -> bool:
        """Присоединение к встрече"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            platform = self.detect_platform(meeting_url)
            if not platform:
                log.error(f"Неподдерживаемая платформа для URL: {meeting_url}")
                return False
            
            log.info(f"Присоединение к встрече на платформе {platform}")
            
            # Переход на страницу встречи
            self.driver.get(meeting_url)
            time.sleep(5)
            
            # Присоединение в зависимости от платформы
            if platform == 'zoom':
                return self._join_zoom_meeting()
            elif platform == 'google_meet':
                return self._join_google_meet()
            elif platform == 'teams':
                return self._join_teams_meeting()
            elif platform == 'kontur_talk':
                return self._join_kontur_talk()
            elif platform == 'yandex_telemost':
                return self._join_yandex_telemost()
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к встрече: {e}")
            return False
    
    def _join_zoom_meeting(self) -> bool:
        """Присоединение к Zoom встрече"""
        try:
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Ввод имени
            try:
                name_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "inputname"))
                )
                name_input.clear()
                name_input.send_keys(self.display_name)
                log.info(f"Введено имя: {self.display_name}")
            except TimeoutException:
                log.info("Поле для имени не найдено, продолжаем")
            
            # Нажатие кнопки присоединения
            join_selectors = [
                (By.ID, "joinBtn"),
                (By.CSS_SELECTOR, "button[aria-label*='Join']"),
                (By.CSS_SELECTOR, "button.preview-join-button"),
                (By.XPATH, "//button[contains(text(), 'Join')]")
            ]
            
            for selector in join_selectors:
                try:
                    join_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    join_button.click()
                    log.info("Нажата кнопка присоединения к Zoom")
                    break
                except TimeoutException:
                    continue
            
            # Ожидание входа в комнату
            time.sleep(10)
            
            # Отключение камеры и микрофона
            self._mute_audio_video()
            
            return self._is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Zoom: {e}")
            return False
    
    def _join_google_meet(self) -> bool:
        """Присоединение к Google Meet"""
        try:
            # Ожидание загрузки
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Нажатие кнопки присоединения
            join_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Join now']"),
                (By.CSS_SELECTOR, "button[aria-label*='Ask to join']"),
                (By.XPATH, "//button[contains(text(), 'Join now')]")
            ]
            
            for selector in join_selectors:
                try:
                    join_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(selector)
                    )
                    join_button.click()
                    log.info("Нажата кнопка присоединения к Google Meet")
                    break
                except TimeoutException:
                    continue
            
            time.sleep(10)
            
            # Отключение камеры и микрофона
            self._mute_audio_video()
            
            return self._is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Google Meet: {e}")
            return False
    
    def _join_teams_meeting(self) -> bool:
        """Присоединение к Teams встрече"""
        try:
            # Ожидание загрузки
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Нажатие кнопки присоединения
            join_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Join now']"),
                (By.CSS_SELECTOR, "button[aria-label*='Join meeting']"),
                (By.XPATH, "//button[contains(text(), 'Join now')]")
            ]
            
            for selector in join_selectors:
                try:
                    join_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(selector)
                    )
                    join_button.click()
                    log.info("Нажата кнопка присоединения к Teams")
                    break
                except TimeoutException:
                    continue
            
            time.sleep(10)
            
            # Отключение камеры и микрофона
            self._mute_audio_video()
            
            return self._is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Teams: {e}")
            return False
    
    def _join_kontur_talk(self) -> bool:
        """Присоединение к Контур.Толк"""
        try:
            # Ожидание загрузки
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Нажатие кнопки присоединения
            join_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Войти']"),
                (By.CSS_SELECTOR, "button[aria-label*='Присоединиться']"),
                (By.XPATH, "//button[contains(text(), 'Войти')]"),
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]")
            ]
            
            for selector in join_selectors:
                try:
                    join_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(selector)
                    )
                    join_button.click()
                    log.info("Нажата кнопка присоединения к Контур.Толк")
                    break
                except TimeoutException:
                    continue
            
            time.sleep(10)
            
            # Отключение камеры и микрофона
            self._mute_audio_video()
            
            return self._is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Контур.Толк: {e}")
            return False
    
    def _join_yandex_telemost(self) -> bool:
        """Присоединение к Яндекс.Телемост"""
        try:
            # Ожидание загрузки
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Нажатие кнопки присоединения
            join_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Войти']"),
                (By.CSS_SELECTOR, "button[aria-label*='Присоединиться']"),
                (By.XPATH, "//button[contains(text(), 'Войти')]"),
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]")
            ]
            
            for selector in join_selectors:
                try:
                    join_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable(selector)
                    )
                    join_button.click()
                    log.info("Нажата кнопка присоединения к Яндекс.Телемост")
                    break
                except TimeoutException:
                    continue
            
            time.sleep(10)
            
            # Отключение камеры и микрофона
            self._mute_audio_video()
            
            return self._is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Яндекс.Телемост: {e}")
            return False
    
    def _mute_audio_video(self):
        """Отключение аудио и видео"""
        try:
            # Отключение микрофона
            mute_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='Unmute']"),
                (By.CSS_SELECTOR, "button[aria-label*='микрофон']"),
                (By.CSS_SELECTOR, "button[aria-label*='microphone']")
            ]
            
            for selector in mute_selectors:
                try:
                    mute_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    mute_button.click()
                    log.info("Микрофон отключен")
                    break
                except TimeoutException:
                    continue
            
            # Отключение камеры
            video_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Stop Video']"),
                (By.CSS_SELECTOR, "button[aria-label*='Start Video']"),
                (By.CSS_SELECTOR, "button[aria-label*='камера']"),
                (By.CSS_SELECTOR, "button[aria-label*='camera']")
            ]
            
            for selector in video_selectors:
                try:
                    video_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    video_button.click()
                    log.info("Камера отключена")
                    break
                except TimeoutException:
                    continue
                    
        except Exception as e:
            log.error(f"Ошибка при отключении аудио/видео: {e}")
    
    def _is_in_meeting(self) -> bool:
        """Проверка, находимся ли мы в встрече"""
        try:
            # Проверка наличия элементов управления встречей
            meeting_indicators = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='Stop Video']"),
                (By.CSS_SELECTOR, "button[aria-label*='Leave']"),
                (By.CSS_SELECTOR, "button[aria-label*='микрофон']"),
                (By.CSS_SELECTOR, "button[aria-label*='камера']")
            ]
            
            for selector in meeting_indicators:
                try:
                    element = self.driver.find_element(*selector)
                    if element.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def start_audio_recording(self) -> bool:
        """Начать запись аудио"""
        try:
            if self.audio_recorder:
                success = self.audio_recorder.start_meeting_recording()
                if success:
                    log.info("Запись аудио начата")
                else:
                    log.error("Не удалось начать запись аудио")
                return success
            return False
            
        except Exception as e:
            log.error(f"Ошибка при начале записи аудио: {e}")
            return False
    
    def stop_audio_recording(self) -> Optional[str]:
        """Остановить запись аудио и вернуть путь к файлу"""
        try:
            if self.audio_recorder:
                audio_file = self.audio_recorder.stop_meeting_recording()
                if audio_file:
                    log.info(f"Запись аудио остановлена, файл: {audio_file}")
                else:
                    log.error("Не удалось получить аудиофайл")
                return audio_file
            return None
            
        except Exception as e:
            log.error(f"Ошибка при остановке записи аудио: {e}")
            return None
    
    def transcribe_audio(self, audio_file: str) -> Optional[Dict[str, Any]]:
        """Транскрибировать аудиофайл"""
        try:
            if not self.speech_transcriber:
                log.error("Транскрибер не инициализирован")
                return None
            
            log.info(f"Начало транскрипции файла: {audio_file}")
            
            # Проверка существования файла
            if not os.path.exists(audio_file):
                log.error(f"Аудиофайл не найден: {audio_file}")
                return None
            
            # Транскрипция
            result = self.speech_transcriber.transcribe_file(audio_file)
            
            if result and result.get('text'):
                log.info(f"Транскрипция завершена, длина: {len(result['text'])} символов")
                return result
            else:
                log.error("Транскрипция не удалась")
                return None
                
        except Exception as e:
            log.error(f"Ошибка при транскрипции: {e}")
            return None
    
    def analyze_meeting(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Анализ встречи через Gemini"""
        try:
            log.info("Начало анализа встречи через Gemini")
            
            # Анализ через Gemini
            analysis_result = analyze_transcript_structured(transcript)
            
            if analysis_result:
                log.info("Анализ встречи завершен")
                return analysis_result
            else:
                log.error("Анализ встречи не удался")
                return None
                
        except Exception as e:
            log.error(f"Ошибка при анализе встречи: {e}")
            return None
    
    def update_lead_in_bitrix(self, lead_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Обновление лида в Bitrix24"""
        try:
            log.info(f"Обновление лида {lead_id} в Bitrix24")
            
            # Обновление лида
            result = update_lead_comprehensive(lead_id, analysis)
            
            if result.get('updated') or result.get('task_created'):
                log.info(f"Лид {lead_id} успешно обновлен")
            else:
                log.warning(f"Лид {lead_id} не был обновлен")
            
            return result
            
        except Exception as e:
            log.error(f"Ошибка при обновлении лида {lead_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def leave_meeting(self) -> bool:
        """Покинуть встречу"""
        try:
            if not self.driver:
                return False
            
            # Поиск кнопки выхода
            leave_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Leave']"),
                (By.CSS_SELECTOR, "button[aria-label*='End']"),
                (By.CSS_SELECTOR, "button[aria-label*='Выйти']"),
                (By.CSS_SELECTOR, "button[aria-label*='Покинуть']"),
                (By.XPATH, "//button[contains(text(), 'Leave')]"),
                (By.XPATH, "//button[contains(text(), 'End')]")
            ]
            
            for selector in leave_selectors:
                try:
                    leave_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    leave_button.click()
                    log.info("Выход из встречи выполнен")
                    return True
                except TimeoutException:
                    continue
            
            log.warning("Кнопка выхода не найдена")
            return False
            
        except Exception as e:
            log.error(f"Ошибка при выходе из встречи: {e}")
            return False
    
    def process_meeting(self, meeting_url: str, chat_id: int, lead_id: Optional[str] = None) -> Dict[str, Any]:
        """Полный процесс обработки встречи"""
        result = {
            'success': False,
            'message': '',
            'transcript': None,
            'analysis': None,
            'lead_update': None
        }
        
        try:
            log.info(f"Начало обработки встречи для чата {chat_id}")
            
            # Шаг 1: Присоединение к встрече
            log.info("Шаг 1: Присоединение к встрече")
            if not self.join_meeting(meeting_url, chat_id):
                result['message'] = "Не удалось присоединиться к встрече"
                return result
            
            # Шаг 2: Начало записи аудио
            log.info("Шаг 2: Начало записи аудио")
            if not self.start_audio_recording():
                result['message'] = "Не удалось начать запись аудио"
                self.leave_meeting()
                return result
            
            # Шаг 3: Ожидание окончания встречи
            log.info("Шаг 3: Ожидание окончания встречи")
            start_time = time.time()
            max_duration = config.MEETING_DURATION_MINUTES * 60
            
            while time.time() - start_time < max_duration:
                if not self._is_in_meeting():
                    log.info("Встреча завершена")
                    break
                time.sleep(10)
            
            # Шаг 4: Остановка записи
            log.info("Шаг 4: Остановка записи аудио")
            audio_file = self.stop_audio_recording()
            if not audio_file:
                result['message'] = "Не удалось получить аудиофайл"
                self.leave_meeting()
                return result
            
            # Шаг 5: Выход из встречи
            log.info("Шаг 5: Выход из встречи")
            self.leave_meeting()
            
            # Шаг 6: Транскрипция
            log.info("Шаг 6: Транскрипция аудио")
            transcript_result = self.transcribe_audio(audio_file)
            if not transcript_result:
                result['message'] = "Не удалось транскрибировать аудио"
                return result
            
            result['transcript'] = transcript_result
            
            # Шаг 7: Анализ
            log.info("Шаг 7: Анализ встречи")
            analysis = self.analyze_meeting(transcript_result['text'])
            if not analysis:
                result['message'] = "Не удалось проанализировать встречу"
                return result
            
            result['analysis'] = analysis
            
            # Шаг 8: Обновление лида (если указан)
            if lead_id:
                log.info(f"Шаг 8: Обновление лида {lead_id}")
                lead_update = self.update_lead_in_bitrix(lead_id, analysis)
                result['lead_update'] = lead_update
            
            result['success'] = True
            result['message'] = "Встреча успешно обработана"
            
            log.info("Обработка встречи завершена успешно")
            return result
            
        except Exception as e:
            log.error(f"Ошибка при обработке встречи: {e}")
            result['message'] = f"Ошибка при обработке встречи: {e}"
            return result
        
        finally:
            # Очистка
            self.leave_meeting()
            if self.audio_recorder:
                self.audio_recorder.cleanup()
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                log.info("WebDriver закрыт")
            
            if self.audio_recorder:
                self.audio_recorder.cleanup()
                log.info("Аудиорекордер очищен")
            
            if self.speech_transcriber:
                self.speech_transcriber.cleanup()
                log.info("Транскрибер очищен")
                
        except Exception as e:
            log.error(f"Ошибка при очистке ресурсов: {e}")

# Глобальный экземпляр бота
server_bot = ServerMeetingBot()
