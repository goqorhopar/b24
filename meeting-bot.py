#!/usr/bin/env python3
"""
Meeting Bot - Улучшенная версия для работы на VPS
Поддержка: Google Meet, Zoom, Яндекс Телемост, Контур.Толк
Версия: 2.1 - Исправлена запись на всю встречу, улучшено присоединение
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import subprocess
import tempfile
import re
import time
from pathlib import Path

# Selenium для автоматизации браузера
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Whisper для транскрипции
from faster_whisper import WhisperModel

# GitHub
from github import Github

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Импорт модуля авторизации
from load_auth_data import get_auth_loader

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'goqorhopar/b24')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
RECORD_DIR = os.getenv('RECORD_DIR', '/tmp/recordings')
MEETING_TIMEOUT_MIN = int(os.getenv('MEETING_TIMEOUT_MIN', '180'))  # 3 часа по умолчанию

# Создаем директорию для записей
Path(RECORD_DIR).mkdir(parents=True, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class MeetingBot:
    """Основной класс для работы с встречами"""
    
    def __init__(self):
        self.driver = None
        self.recording = False
        self.audio_file = None
        self.transcript = []
        self.recording_process = None
        self.meeting_url = None
        self.start_time = None
        self.monitoring_task = None
        self.meeting_active = True
        self.auth_loader = get_auth_loader()
        
        # Инициализация GitHub
        if GITHUB_TOKEN:
            try:
                self.github = Github(GITHUB_TOKEN)
                self.repo = self.github.get_repo(GITHUB_REPO)
                logger.info("GitHub репозиторий подключен")
            except Exception as e:
                logger.error(f"Ошибка подключения к GitHub: {e}")
                self.github = None
                self.repo = None
        else:
            self.github = None
            self.repo = None
            logger.warning("GitHub токен не настроен")
        
        # Инициализация Whisper модели
        try:
            logger.info(f"Загрузка Whisper модели: {WHISPER_MODEL}")
            self.whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            logger.info("Whisper модель загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки Whisper: {e}")
            self.whisper_model = None
        
    def setup_driver(self, headless=True):
        """Настройка Chrome драйвера для VPS"""
        options = Options()

        # Критичные настройки для headless режима
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-extensions')

        # Настройки для медиа
        options.add_argument('--use-fake-ui-for-media-stream')
        options.add_argument('--use-fake-device-for-media-stream')
        options.add_argument('--autoplay-policy=no-user-gesture-required')
        options.add_argument('--disable-blink-features=AutomationControlled')

        # Размер окна
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')

        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Разрешения для микрофона и камеры
        prefs = {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
        }
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Уникальный user-data-dir для каждого запуска
        import tempfile
        unique_profile_dir = tempfile.mkdtemp(prefix="meetingbot_chrome_profile_")
        options.add_argument(f'--user-data-dir={unique_profile_dir}')

        # Инициализация драйвера
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info(f"Chrome драйвер инициализирован с профилем: {unique_profile_dir}")

            # Применяем сохраненные данные авторизации
            auth_status = self.auth_loader.get_auth_status()
            logger.info(f"Статус авторизации: {auth_status}")

            # Применяем авторизацию только если файлы существуют
            auth_files = self.auth_loader.check_auth_files_exist()
            if any(auth_files.values()):
                if self.auth_loader.setup_authenticated_driver(self.driver):
                    logger.info("✅ Драйвер настроен с авторизацией")
                else:
                    logger.warning("⚠️ Не удалось применить авторизацию")
            else:
                logger.warning("⚠️ Файлы авторизации не найдены - возможны проблемы с закрытыми встречами")
                logger.info("💡 Запустите: python simple_auth.py для настройки авторизации")

        except Exception as e:
            logger.error(f"Ошибка инициализации Chrome: {e}")
            raise
        
    def detect_meeting_type(self, url: str) -> str:
        """Определить тип встречи по URL"""
        url_lower = url.lower()
        if 'meet.google.com' in url_lower:
            return 'google_meet'
        elif 'zoom.us' in url_lower or 'zoom.com' in url_lower:
            return 'zoom'
        elif 'telemost.yandex' in url_lower:
            return 'yandex'
        elif 'talk.contour.ru' in url_lower or 'contour.ru' in url_lower:
            return 'contour'
        elif 'teams.microsoft.com' in url_lower:
            return 'teams'
        else:
            return 'unknown'
    
    def join_google_meet(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Google Meet с улучшенной логикой"""
        try:
            logger.info(f"Открываем Google Meet: {meeting_url}")
            self.driver.get(meeting_url)
            self.meeting_url = meeting_url
            
            # Ждем загрузки страницы
            time.sleep(8)
            
            # Проверяем, не требуется ли вход в аккаунт
            if "accounts.google.com" in self.driver.current_url:
                logger.warning("Требуется вход в Google аккаунт - встреча может быть закрытой")
                return False
            
            # Проверяем, не находимся ли уже в встрече
            if "meet.google.com" in self.driver.current_url and "meet.google.com/" in self.driver.current_url:
                logger.info("Уже находимся в Google Meet - возможно, автоматически подключились")
                # Отключаем камеру и микрофон если уже в встрече
                self._disable_media_in_meeting()
                return True
            
            # Ищем поле ввода имени (если есть)
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for inp in name_inputs:
                    placeholder = (inp.get_attribute('placeholder') or '').lower()
                    aria_label = (inp.get_attribute('aria-label') or '').lower()
                    if 'name' in placeholder or 'имя' in placeholder or 'name' in aria_label:
                        inp.clear()
                        inp.send_keys(name)
                        logger.info(f"Введено имя: {name}")
                        time.sleep(1)
                        break
            except Exception as e:
                logger.debug(f"Не удалось ввести имя: {e}")
            
            # Нажимаем кнопку присоединения
            join_clicked = False
            join_patterns = [
                ('css', "button[jsname='Qx7uuf']"),
                ('css', "button[aria-label*='Join now' i]"),
                ('css', "button[aria-label*='Ask to join' i]"),
                ('css', "button[data-is-muted='false'][aria-label*='Join']"),
                ('xpath', "//button[contains(translate(., 'JOIN', 'join'), 'join')]"),
                ('xpath', "//button[contains(., 'Присоединиться')]"),
                ('xpath', "//span[contains(translate(., 'JOIN', 'join'), 'join')]/parent::button"),
                ('xpath', "//button[contains(., 'Ask to join')]"),
            ]
            
            for method, selector in join_patterns:
                try:
                    if method == 'css':
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            logger.info(f"Нажата кнопка присоединения: {btn.text or btn.get_attribute('aria-label')}")
                            join_clicked = True
                            time.sleep(5)  # Ждем дольше после нажатия
                            break
                    if join_clicked:
                        break
                except Exception as e:
                    logger.debug(f"Попытка нажать кнопку {selector}: {e}")
            
            if not join_clicked:
                # Последняя попытка - ищем любую кнопку с текстом
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    text = btn.text.lower()
                    if any(word in text for word in ['join', 'присоединиться', 'войти', 'ask to join']):
                        try:
                            btn.click()
                            logger.info(f"Нажата кнопка: {btn.text}")
                            join_clicked = True
                            time.sleep(5)
                            break
                        except:
                            pass
            
            # Проверяем, удалось ли присоединиться
            time.sleep(5)  # Увеличиваем время ожидания
            
            # Проверяем несколько индикаторов успешного подключения
            connection_success = False
            
            # 1. Проверяем URL
            if "meet.google.com" in self.driver.current_url:
                logger.info("URL указывает на Google Meet")
                connection_success = True
            
            # 2. Проверяем наличие элементов встречи
            try:
                meeting_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[jsname='BOHaEe'], div[data-is-muted], button[aria-label*='camera'], button[aria-label*='microphone']")
                if meeting_elements:
                    logger.info(f"Найдены элементы управления встречей: {len(meeting_elements)}")
                    connection_success = True
            except Exception as e:
                logger.debug(f"Ошибка поиска элементов встречи: {e}")
            
            # 3. Проверяем, что нет сообщений об ошибке
            try:
                error_messages = self.driver.find_elements(By.XPATH, 
                    "//div[contains(text(), 'Unable to join') or contains(text(), 'Meeting not found') or contains(text(), 'Access denied')]")
                if error_messages:
                    logger.warning("Найдены сообщения об ошибке подключения")
                    connection_success = False
            except Exception as e:
                logger.debug(f"Ошибка проверки сообщений об ошибке: {e}")
            
            if connection_success:
                logger.info(f"✅ Успешно присоединились к Google Meet: {meeting_url}")
                self._disable_media_in_meeting()
                return True
            else:
                logger.warning("⚠️ Не удалось присоединиться к встрече")
                # Сохраняем скриншот для диагностики
                try:
                    screenshot_path = f"/tmp/meetingbot_googlemeet_fail_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.warning(f"Скриншот ошибки сохранен: {screenshot_path}")
                    # Отправка скриншота админу
                    self._send_screenshot_to_admin(screenshot_path, meeting_url)
                except Exception as err:
                    logger.error(f"Ошибка сохранения скриншота: {err}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при присоединении к Google Meet: {e}")
            return False
    
    def _disable_media_in_meeting(self):
        """Отключить камеру и микрофон в активной встрече"""
        try:
            # Отключаем камеру
            camera_selectors = [
                "button[aria-label*='camera' i][data-is-muted='false']",
                "button[aria-label*='Turn off camera' i]",
                "div[jscontroller][jsaction*='camera'] button",
                "button[jsname='BOHaEe']",
                "button[data-is-muted='false'][aria-label*='camera']",
            ]
            
            for selector in camera_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        aria_label = el.get_attribute('aria-label') or ''
                        if 'camera' in aria_label.lower() and 'turn off' in aria_label.lower():
                            el.click()
                            logger.info("Камера отключена")
                            time.sleep(0.5)
                            break
                except Exception as e:
                    logger.debug(f"Попытка отключить камеру через {selector}: {e}")
            
            # Отключаем микрофон
            mic_selectors = [
                "button[aria-label*='microphone' i][data-is-muted='false']",
                "button[aria-label*='Turn off microphone' i]",
                "div[jscontroller][jsaction*='microphone'] button",
                "button[data-is-muted='false'][aria-label*='microphone']",
            ]
            
            for selector in mic_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        aria_label = el.get_attribute('aria-label') or ''
                        if ('microphone' in aria_label.lower() or 'mic' in aria_label.lower()) and 'turn off' in aria_label.lower():
                            el.click()
                            logger.info("Микрофон отключен")
                            time.sleep(0.5)
                            break
                except Exception as e:
                    logger.debug(f"Попытка отключить микрофон через {selector}: {e}")
        except Exception as e:
            logger.debug(f"Ошибка при отключении медиа: {e}")
    
    def join_zoom_meeting(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Zoom встрече"""
        try:
            logger.info(f"Открываем Zoom: {meeting_url}")
            
            # Если это ссылка вида zoom.us/j/123456789
            if '/j/' in meeting_url:
                # Добавляем параметр для веб-клиента
                if '?' in meeting_url:
                    meeting_url += '&web=1'
                else:
                    meeting_url += '?web=1'
            
            self.driver.get(meeting_url)
            self.meeting_url = meeting_url
            time.sleep(8)  # Увеличиваем время ожидания
            
            # Ищем кнопку "Join from Browser" / "Launch Meeting"
            try:
                web_join_buttons = self.driver.find_elements(By.XPATH, 
                    "//a[contains(text(), 'Join from Browser') or contains(text(), 'Launch Meeting') or contains(text(), 'browser')]")
                for btn in web_join_buttons:
                    if btn.is_displayed():
                        btn.click()
                        logger.info("Нажата кнопка входа через браузер")
                        time.sleep(5)
                        break
            except Exception as e:
                logger.debug(f"Кнопка входа через браузер не найдена: {e}")
            
            # Вводим имя
            try:
                name_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "inputname"))
                )
                name_input.clear()
                name_input.send_keys(name)
                logger.info(f"Введено имя: {name}")
                time.sleep(2)
            except Exception as e:
                logger.debug(f"Не удалось ввести имя: {e}")
            
            # Ищем и нажимаем кнопку Join
            join_clicked = False
            
            # Список всех возможных селекторов для кнопки Join
            join_selectors = [
                ('id', 'joinBtn'),
                ('css', 'button[data-tooltip="Join Meeting"]'),
                ('css', 'button[aria-label="Join Meeting"]'),
                ('css', 'button[aria-label="Join"]'),
                ('css', 'button[data-tooltip="Join"]'),
                ('css', '.zm-btn--primary'),
                ('css', '.join-btn'),
                ('css', 'button[class*="join"]'),
                ('xpath', "//button[contains(text(), 'Join')]"),
                ('xpath', "//button[contains(text(), 'Join Meeting')]"),
                ('xpath', "//button[contains(text(), 'Войти')]"),
                ('xpath', "//button[contains(text(), 'Присоединиться')]"),
                ('xpath', "//a[contains(text(), 'Join')]"),
                ('xpath', "//a[contains(text(), 'Join Meeting')]"),
            ]
            
            for method, selector in join_selectors:
                try:
                    if method == 'id':
                        elements = self.driver.find_elements(By.ID, selector)
                    elif method == 'css':
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:  # xpath
                        elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for btn in elements:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            logger.info(f"Нажата кнопка Join через {method}: {selector}")
                            join_clicked = True
                            time.sleep(5)
                            break
                    if join_clicked:
                        break
                except Exception as e:
                    logger.debug(f"Попытка {method} {selector}: {e}")
            
            if not join_clicked:
                logger.warning("Не удалось найти кнопку Join ни одним способом")
                # Последняя попытка - ищем любые кнопки
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in all_buttons:
                    try:
                        text = btn.text.lower()
                        if any(word in text for word in ['join', 'войти', 'присоединиться', 'enter']):
                            if btn.is_displayed() and btn.is_enabled():
                                btn.click()
                                logger.info(f"Нажата кнопка по тексту: {btn.text}")
                                join_clicked = True
                                time.sleep(5)
                                break
                    except:
                        pass
            
            # Ждем загрузки встречи и проверяем, что мы действительно в ней
            time.sleep(10)
            
            # Проверяем, что мы в активной встрече
            current_url = self.driver.current_url
            logger.info(f"Текущий URL после присоединения: {current_url}")
            
            # Ищем индикаторы того, что мы в активной встрече
            meeting_indicators = [
                "//div[contains(@class, 'meeting-client')]",
                "//div[contains(@class, 'video-container')]",
                "//button[contains(@aria-label, 'Mute')]",
                "//button[contains(@aria-label, 'Unmute')]",
                "//div[contains(@class, 'participants')]",
                "//canvas",  # Видео элемент
                "//div[contains(@class, 'meeting')]",
                "//div[contains(@class, 'zoom')]",
            ]
            
            in_meeting = False
            found_indicators = 0
            for indicator in meeting_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements:
                        logger.info(f"Найден индикатор встречи: {indicator} ({len(elements)} элементов)")
                        found_indicators += 1
                        in_meeting = True
                except:
                    pass
            
            # Дополнительная проверка - ищем сообщения об ошибке
            error_indicators = [
                "//div[contains(text(), 'Meeting not found')]",
                "//div[contains(text(), 'Invalid meeting ID')]",
                "//div[contains(text(), 'Meeting has ended')]",
                "//div[contains(text(), 'Please wait for the host')]",
                "//div[contains(text(), 'Waiting for host')]",
            ]
            
            has_error = False
            for indicator in error_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements:
                        logger.warning(f"Найдено сообщение об ошибке: {indicator}")
                        has_error = True
                        break
                except:
                    pass
            
            # Проверяем URL - должны быть в активной встрече Zoom
            url_check = "zoom.us" in current_url and ("/j/" in current_url or "/meeting/" in current_url)
            
            # Итоговая проверка
            connection_success = (
                (in_meeting and found_indicators >= 2) or 
                (join_clicked and url_check and not has_error)
            )
            
            if connection_success:
                logger.info(f"✅ Подключились к Zoom: {meeting_url}")
                self._disable_zoom_media()
                return True
            else:
                logger.warning("⚠️ Не удалось подтвердить присоединение к встрече")
                logger.info(f"Результат проверки: индикаторы={found_indicators}, ошибки={has_error}, URL={url_check}")
                try:
                    screenshot_path = f"/tmp/meetingbot_zoom_fail_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.warning(f"Скриншот ошибки сохранен: {screenshot_path}")
                    self._send_screenshot_to_admin(screenshot_path, meeting_url)
                except Exception as err:
                    logger.error(f"Ошибка сохранения скриншота: {err}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при присоединении к Zoom: {e}")
            return False
    
    def _disable_zoom_media(self):
        """Отключить камеру и микрофон в Zoom"""
        try:
            time.sleep(3)  # Ждем загрузки элементов управления
            
            # Отключаем микрофон
            mic_selectors = [
                "button[aria-label*='Mute' i]",
                "button[aria-label*='Unmute' i]",
                "button[data-tooltip*='Mute' i]",
                "button[data-tooltip*='Unmute' i]",
                ".zm-btn--mute",
                ".zm-btn--unmute"
            ]
            
            for selector in mic_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            aria_label = el.get_attribute('aria-label') or ''
                            if 'unmute' in aria_label.lower() or 'mute' in aria_label.lower():
                                el.click()
                                logger.info("Микрофон отключен в Zoom")
                                time.sleep(1)
                                break
                except Exception as e:
                    logger.debug(f"Попытка отключить микрофон через {selector}: {e}")
            
            # Отключаем камеру
            camera_selectors = [
                "button[aria-label*='Stop Video' i]",
                "button[aria-label*='Start Video' i]",
                "button[data-tooltip*='Stop Video' i]",
                "button[data-tooltip*='Start Video' i]",
                ".zm-btn--video",
                ".zm-btn--stop-video"
            ]
            
            for selector in camera_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        if el.is_displayed():
                            aria_label = el.get_attribute('aria-label') or ''
                            if 'start video' in aria_label.lower() or 'stop video' in aria_label.lower():
                                el.click()
                                logger.info("Камера отключена в Zoom")
                                time.sleep(1)
                                break
                except Exception as e:
                    logger.debug(f"Попытка отключить камеру через {selector}: {e}")
                    
        except Exception as e:
            logger.debug(f"Ошибка при отключении медиа в Zoom: {e}")
    
    def join_yandex_telemost(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Яндекс Телемост"""
        try:
            logger.info(f"Открываем Яндекс Телемост: {meeting_url}")
            self.driver.get(meeting_url)
            self.meeting_url = meeting_url
            time.sleep(5)
            
            # Вводим имя
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for inp in name_inputs:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(name)
                        logger.info(f"Введено имя: {name}")
                        time.sleep(0.5)
                        break
            except Exception as e:
                logger.debug(f"Не удалось ввести имя: {e}")
            
            # Отключаем камеру и микрофон
            try:
                controls = self.driver.find_elements(By.TAG_NAME, "button")
                for control in controls:
                    aria_label = (control.get_attribute("aria-label") or '').lower()
                    title = (control.get_attribute("title") or '').lower()
                    if any(word in aria_label or word in title for word in ['камера', 'camera', 'микрофон', 'microphone']):
                        control.click()
                        time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Не удалось отключить медиа: {e}")
            
            # Ищем кнопку входа
            join_clicked = False
            join_words = ['войти', 'присоединиться', 'join', 'enter']
            
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                text = btn.text.lower()
                if any(word in text for word in join_words) and btn.is_displayed():
                    try:
                        btn.click()
                        logger.info(f"Нажата кнопка: {btn.text}")
                        join_clicked = True
                        time.sleep(3)
                        break
                    except:
                        pass
            
            if join_clicked or 'telemost.yandex' in self.driver.current_url:
                logger.info(f"✅ Подключились к Яндекс Телемост: {meeting_url}")
                return True
            else:
                logger.warning("⚠️ Не удалось найти кнопку входа")
                try:
                    screenshot_path = f"/tmp/meetingbot_yandex_fail_{int(time.time())}.png"
                    self.driver.save_screenshot(screenshot_path)
                    logger.warning(f"Скриншот ошибки сохранен: {screenshot_path}")
                    self._send_screenshot_to_admin(screenshot_path, meeting_url)
                except Exception as err:
                    logger.error(f"Ошибка сохранения скриншота: {err}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при присоединении к Яндекс Телемост: {e}")
            return False
    
    def join_contour_talk(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Контур.Толк"""
        try:
            logger.info(f"Открываем Контур.Толк: {meeting_url}")
            self.driver.get(meeting_url)
            self.meeting_url = meeting_url
            time.sleep(5)
            # Вводим имя если требуется
            try:
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='name']")
                for inp in name_inputs:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(name)
                        logger.info(f"Введено имя: {name}")
                        break
            except Exception as e:
                logger.debug(f"Поле имени не найдено: {e}")
            # Ищем кнопку подключения
            join_patterns = [
                ('xpath', "//button[contains(., 'Подключиться')]") ,
                ('xpath', "//button[contains(., 'Войти')]") ,
                ('xpath', "//button[contains(., 'Join')]") ,
            ]
            for method, selector in join_patterns:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed():
                            btn.click()
                            logger.info("Нажата кнопка подключения")
                            time.sleep(3)
                            return True
                except:
                    pass
            logger.warning("⚠️ Не удалось подключиться к Контур.Толк")
            try:
                screenshot_path = f"/tmp/meetingbot_contour_fail_{int(time.time())}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.warning(f"Скриншот ошибки сохранен: {screenshot_path}")
                self._send_screenshot_to_admin(screenshot_path, meeting_url)
            except Exception as err:
                logger.error(f"Ошибка сохранения скриншота: {err}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при присоединении к Контур.Толк: {e}")
            return False
    def _verify_real_meeting_connection(self) -> bool:
        """Проверить, что бот действительно подключен к встрече"""
        try:
            if not self.driver:
                logger.warning("Драйвер не инициализирован")
                return False
            
            current_url = self.driver.current_url
            logger.info(f"Проверка реального подключения. URL: {current_url}")
            
            # Проверяем URL - должны быть в активной встрече
            meeting_platforms = ['meet.google.com', 'zoom.us', 'telemost.yandex', 'talk.contour.ru']
            in_meeting_platform = any(platform in current_url for platform in meeting_platforms)
            
            if not in_meeting_platform:
                logger.warning("Не находимся на платформе встречи")
                return False
            
            # Ищем индикаторы активной встречи
            meeting_indicators = [
                # Google Meet
                "video[src*='blob:']",  # Видео поток
                "audio[src*='blob:']",  # Аудио поток
                "div[jsname='BOHaEe']",  # Кнопки управления
                "div[data-is-muted]",  # Индикаторы состояния
                
                # Zoom
                "canvas",  # Видео элемент
                "div[class*='meeting-client']",  # Клиент встречи
                "button[aria-label*='Mute']",  # Кнопки управления
                
                # Общие
                "video",  # Любое видео
                "audio",  # Любой аудио
                "div[class*='participant']",  # Участники
                "div[class*='meeting']",  # Элементы встречи
            ]
            
            found_indicators = 0
            for indicator in meeting_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        found_indicators += 1
                        logger.info(f"Найден индикатор встречи: {indicator} ({len(elements)} элементов)")
                except Exception as e:
                    logger.debug(f"Ошибка поиска индикатора {indicator}: {e}")
            
            # Проверяем, что есть активные медиа элементы
            has_active_media = False
            try:
                # Проверяем наличие активных видео/аудио потоков
                media_elements = self.driver.find_elements(By.CSS_SELECTOR, "video, audio")
                for element in media_elements:
                    try:
                        # Проверяем, что элемент активен
                        if element.get_attribute('src') or element.get_attribute('currentSrc'):
                            has_active_media = True
                            logger.info("Найден активный медиа элемент")
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Ошибка проверки медиа элементов: {e}")
            
            # Проверяем, что нет сообщений об ошибке или ожидании
            error_indicators = [
                "//div[contains(text(), 'Waiting for host')]",
                "//div[contains(text(), 'Meeting not started')]",
                "//div[contains(text(), 'Please wait')]",
                "//div[contains(text(), 'Ожидание')]",
                "//div[contains(text(), 'Встреча не началась')]",
                "//div[contains(text(), 'Пожалуйста, подождите')]",
            ]
            
            has_error = False
            for indicator in error_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, indicator)
                    if elements:
                        has_error = True
                        logger.warning(f"Найдено сообщение об ошибке: {indicator}")
                        break
                except:
                    continue
            
            # Итоговая проверка
            is_real_meeting = (
                in_meeting_platform and 
                found_indicators >= 2 and 
                not has_error and
                (has_active_media or found_indicators >= 3)  # Либо есть активные медиа, либо много индикаторов
            )
            
            logger.info(f"Результат проверки: платформа={in_meeting_platform}, индикаторы={found_indicators}, медиа={has_active_media}, ошибки={has_error}")
            logger.info(f"Реальное подключение: {is_real_meeting}")
            
            return is_real_meeting
            
        except Exception as e:
            logger.error(f"Ошибка проверки реального подключения: {e}")
            return False
    
    def _send_imitation_alert(self, meeting_url: str):
        """Отправить уведомление об имитации подключения"""
        import requests
        ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')
        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        
        if not (ADMIN_CHAT_ID and TELEGRAM_BOT_TOKEN):
            logger.warning("ADMIN_CHAT_ID или TELEGRAM_BOT_TOKEN не заданы для отправки уведомления")
            return
        
        try:
            msg = f"🚨 **Meeting Bot: Имитация подключения!**\n\n"
            msg += f"🔗 URL: {meeting_url}\n"
            msg += f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            msg += "❌ Бот не смог реально подключиться к встрече.\n"
            msg += "Возможные причины:\n"
            msg += "• Требуется авторизация\n"
            msg += "• Встреча еще не началась\n"
            msg += "• Неверная ссылка\n"
            msg += "• Проблемы с cookies"
            
            url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            resp = requests.post(url_api, data={
                'chat_id': ADMIN_CHAT_ID,
                'text': msg,
                'parse_mode': 'Markdown'
            })
            
            if resp.status_code == 200:
                logger.info("Уведомление об имитации отправлено админу")
            else:
                logger.error(f"Ошибка отправки уведомления: {resp.text}")
                
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления об имитации: {e}")
    
    def _send_screenshot_to_admin(self, screenshot_path, meeting_url):
        """Отправить скриншот ошибки админу в Telegram"""
        import requests
        ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')
        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if not (ADMIN_CHAT_ID and TELEGRAM_BOT_TOKEN):
            logger.warning("ADMIN_CHAT_ID или TELEGRAM_BOT_TOKEN не заданы для отправки скриншота")
            return
        try:
            with open(screenshot_path, 'rb') as img:
                files = {'photo': img}
                caption = f"❌ Meeting Bot не смог подключиться к встрече!\nURL: {meeting_url}"
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                resp = requests.post(url, data={
                    'chat_id': ADMIN_CHAT_ID,
                    'caption': caption
                }, files=files)
                if resp.status_code == 200:
                    logger.info("Скриншот ошибки отправлен админу в Telegram")
                else:
                    logger.error(f"Ошибка отправки скриншота админу: {resp.text}")
        except Exception as e:
            logger.error(f"Ошибка отправки скриншота админу: {e}")
            return False
    
    def start_recording(self):
        """Начать запись аудио через ffmpeg на всю встречу"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.audio_file = os.path.join(RECORD_DIR, f"meeting_{timestamp}.wav")
            
            # Пытаемся разные источники аудио для Linux VPS
            # Убираем ограничение по времени - записываем до остановки
            audio_sources = [
                ['ffmpeg', '-f', 'alsa', '-i', 'hw:0,0', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
                ['ffmpeg', '-f', 'alsa', '-i', 'hw:0,1', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
                ['ffmpeg', '-f', 'alsa', '-i', 'plughw:0,0', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
                ['ffmpeg', '-f', 'alsa', '-i', 'plughw:0,1', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
                ['ffmpeg', '-f', 'pulse', '-i', 'default', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
                ['ffmpeg', '-f', 'alsa', '-i', 'default', '-ac', '2', '-ar', '16000', '-y', self.audio_file],
            ]
            
            for cmd in audio_sources:
                try:
                    self.recording_process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    # Проверяем, что процесс запустился
                    time.sleep(1)
                    if self.recording_process.poll() is None:
                        self.recording = True
                        self.start_time = datetime.now()
                        self.meeting_active = True
                        logger.info(f"✅ Начата запись аудио на всю встречу: {self.audio_file}")
                        logger.info(f"Команда: {' '.join(cmd)}")
                        
                        # Запускаем мониторинг встречи
                        self.start_meeting_monitoring()
                        return True
                    else:
                        logger.debug(f"Команда не сработала: {' '.join(cmd)}")
                except Exception as e:
                    logger.debug(f"Ошибка запуска {cmd}: {e}")
            
            logger.error("❌ Не удалось запустить запись аудио ни одним способом")
            return False
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при начале записи: {e}")
            return False
    
    def start_meeting_monitoring(self):
        """Запустить мониторинг состояния встречи"""
        try:
            import threading
            self.monitoring_task = threading.Thread(target=self._monitor_meeting, daemon=True)
            self.monitoring_task.start()
            logger.info("🔍 Мониторинг встречи запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска мониторинга: {e}")
    
    def _monitor_meeting(self):
        """Мониторить состояние встречи в фоновом режиме"""
        try:
            while self.recording and self.meeting_active:
                time.sleep(30)  # Проверяем каждые 30 секунд
                
                if not self.driver:
                    logger.info("🔍 Драйвер не найден - встреча завершена")
                    self.meeting_active = False
                    break
                
                try:
                    current_url = self.driver.current_url
                    
                    # Проверяем, не покинули ли встречу
                    if "meet.google.com" not in current_url and "zoom.us" not in current_url:
                        logger.info("🔍 Покинули встречу - останавливаем запись")
                        self.meeting_active = False
                        break
                    
                    # Проверяем, не появились ли сообщения о завершении встречи
                    try:
                        end_indicators = [
                            "//div[contains(text(), 'Everyone left')]",
                            "//div[contains(text(), 'Meeting ended')]",
                            "//div[contains(text(), 'Встреча завершена')]",
                            "//div[contains(text(), 'Все покинули')]",
                        ]
                        
                        for indicator in end_indicators:
                            elements = self.driver.find_elements(By.XPATH, indicator)
                            if elements:
                                logger.info("🔍 Обнаружено завершение встречи")
                                self.meeting_active = False
                                break
                        
                        if not self.meeting_active:
                            break
                            
                    except Exception as e:
                        logger.debug(f"Ошибка проверки индикаторов: {e}")
                        
                except Exception as e:
                    logger.debug(f"Ошибка мониторинга: {e}")
                    # Если не можем проверить состояние, считаем что встреча активна
                    continue
            
            # Если мониторинг обнаружил завершение встречи, останавливаем запись
            if not self.meeting_active and self.recording:
                logger.info("🔍 Автоматическая остановка записи - встреча завершена")
                self.stop_recording()
                
        except Exception as e:
            logger.error(f"Ошибка в мониторинге встречи: {e}")
    
    def stop_recording(self):
        """Остановить запись"""
        try:
            self.meeting_active = False  # Останавливаем мониторинг
            
            if self.recording and self.recording_process:
                self.recording_process.terminate()
                try:
                    self.recording_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.recording_process.kill()
                    self.recording_process.wait()
                
                self.recording = False
                logger.info("⏹️ Запись остановлена")
                
                # Проверяем, что файл создан
                if os.path.exists(self.audio_file):
                    size = os.path.getsize(self.audio_file)
                    logger.info(f"Размер записанного файла: {size} байт")
                    return True
                else:
                    logger.error("Файл записи не найден")
                    return False
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при остановке записи: {e}")
            return False
    
    def transcribe_audio_whisper(self):
        """Транскрибировать аудио с помощью Faster Whisper"""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                logger.error("❌ Аудио файл не найден")
                return None
            
            if not self.whisper_model:
                logger.error("❌ Whisper модель не загружена")
                return None
            
            file_size = os.path.getsize(self.audio_file)
            logger.info(f"🎙️ Начинаем транскрипцию файла: {self.audio_file} ({file_size} байт)")
            
            if file_size < 1000:
                logger.warning("⚠️ Файл слишком маленький, возможно запись не удалась")
                return "Ошибка: файл записи слишком мал, возможно аудио не было записано"
            
            # Транскрибируем
            segments, info = self.whisper_model.transcribe(
                self.audio_file,
                language="ru",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            logger.info(f"Обнаружен язык: {info.language} (вероятность: {info.language_probability:.2f})")
            
            # Собираем текст
            full_text = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    timestamp = f"[{self._format_timestamp(segment.start)} --> {self._format_timestamp(segment.end)}]"
                    full_text.append(f"{timestamp}\n{text}\n")
                    self.transcript.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": text
                    })
            
            if full_text:
                result = "\n".join(full_text)
                logger.info(f"✅ Транскрипция завершена. Сегментов: {len(self.transcript)}")
                return result
            else:
                logger.warning("⚠️ Транскрипт пуст - речь не обнаружена")
                return "Транскрипт пуст: речь не обнаружена в записи"
                
        except Exception as e:
            logger.error(f"❌ Ошибка при транскрипции: {e}")
            return f"Ошибка транскрипции: {str(e)}"
    
    def _format_timestamp(self, seconds: float) -> str:
        """Форматировать временную метку"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def save_to_github(self, content: str, filename: str):
        """Сохранить транскрипт в GitHub"""
        try:
            if not self.repo:
                logger.warning("⚠️ GitHub репозиторий не настроен")
                return False
            
            path = f"transcripts/{filename}"
            
            try:
                # Проверяем существует ли файл
                file = self.repo.get_contents(path)
                # Обновляем существующий файл
                self.repo.update_file(
                    path,
                    f"Update transcript {filename}",
                    content,
                    file.sha,
                    branch="main"
                )
                logger.info(f"✅ Файл обновлен в GitHub: {path}")
            except:
                # Создаем новый файл
                self.repo.create_file(
                    path,
                    f"Add transcript {filename}",
                    content,
                    branch="main"
                )
                logger.info(f"✅ Файл создан в GitHub: {path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении в GitHub: {e}")
            return False
    
    def get_meeting_info(self) -> str:
        """Получить информацию о встрече"""
        try:
            info = []
            info.append(f"🔗 URL: {self.meeting_url}")
            info.append(f"⏱️ Начало: {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'N/A'}")
            
            if self.recording:
                duration = (datetime.now() - self.start_time).total_seconds() / 60
                info.append(f"⏳ Длительность: {duration:.1f} мин")
            
            if self.audio_file and os.path.exists(self.audio_file):
                size_mb = os.path.getsize(self.audio_file) / (1024 * 1024)
                info.append(f"💾 Размер записи: {size_mb:.2f} МБ")
            
            return "\n".join(info)
        except Exception as e:
            return f"Ошибка получения информации: {e}"
    
    def leave_meeting(self):
        """Покинуть встречу"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            logger.info("👋 Покинули встречу")
        except Exception as e:
            logger.error(f"❌ Ошибка при выходе из встречи: {e}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.meeting_active = False  # Останавливаем мониторинг
        self.leave_meeting()
        if self.recording:
            self.stop_recording()
        # Не удаляем аудио файл - он нужен для транскрипции


# Глобальные переменные для хранения активных ботов
active_bots: Dict[int, MeetingBot] = {}


# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("📊 Статус", callback_data='status')],
        [InlineKeyboardButton("❓ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🤖 *Meeting Bot v2.2* - Автоматическое участие во встречах\n\n"
        "✅ *ИСПРАВЛЕНО: Запись на всю встречу (НЕ 3 минуты!)*\n"
        "✅ *ИСПРАВЛЕНО: Улучшено присоединение к встречам*\n\n"
        "📝 *Поддерживаемые платформы:*\n"
        "• Google Meet\n"
        "• Zoom\n"
        "• Яндекс Телемост\n"
        "• Контур.Толк\n\n"
        "📤 *Как использовать:*\n"
        "Просто отправьте ссылку на встречу, и бот:\n"
        "1️⃣ Присоединится к встрече\n"
        "2️⃣ Запишет аудио НА ВСЮ ВСТРЕЧУ\n"
        "3️⃣ Создаст транскрипт\n"
        "4️⃣ Отправит результат вам\n\n"
        "Отправьте ссылку для начала работы! 🚀"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = (
        "📖 *Инструкция по использованию*\n\n"
        "*Шаг 1:* Отправьте ссылку на встречу\n"
        "Пример: `https://meet.google.com/abc-defg-hij`\n\n"
        "*Шаг 2:* Дождитесь подключения бота\n"
        "Бот автоматически присоединится и начнет запись\n\n"
        "*Шаг 3:* Управляйте встречей\n"
        "• ⏹️ Остановить запись\n"
        "• 🚪 Покинуть встречу\n"
        "• 📊 Проверить статус\n\n"
        "*Шаг 4:* Получите транскрипт\n"
        "После остановки записи бот создаст и отправит транскрипт\n\n"
        "*Поддерживаемые форматы ссылок:*\n"
        "• `meet.google.com/xxx`\n"
        "• `zoom.us/j/xxx`\n"
        "• `telemost.yandex.ru/xxx`\n"
        "• `talk.contour.ru/xxx`\n\n"
        "*Команды:*\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/status - Текущий статус"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    user_id = update.effective_user.id
    bot = active_bots.get(user_id)
    
    if bot and bot.recording:
        info = bot.get_meeting_info()
        status_text = f"🟢 *Статус: Активен*\n\n{info}"
    else:
        status_text = "🔴 *Статус: Неактивен*\n\nНет активных встреч"
    
    await update.message.reply_text(status_text, parse_mode='Markdown')


async def handle_meeting_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик URL встречи"""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Проверяем, есть ли уже активный бот
    if user_id in active_bots:
        await update.message.reply_text(
            "⚠️ У вас уже есть активная встреча!\n"
            "Сначала завершите текущую встречу."
        )
        return
    
    # Определяем тип встречи
    bot = MeetingBot()
    meeting_type = bot.detect_meeting_type(url)
    
    if meeting_type == 'unknown':
        await update.message.reply_text(
            "❌ Не удалось определить тип встречи.\n\n"
            "Поддерживаемые платформы:\n"
            "• Google Meet (meet.google.com)\n"
            "• Zoom (zoom.us)\n"
            "• Яндекс Телемост (telemost.yandex.ru)\n"
            "• Контур.Толк (talk.contour.ru)"
        )
        return
    
    # Отправляем сообщение о начале подключения
    status_msg = await update.message.reply_text("🎯 **Встреча обнаружена!**\n\n🔗 **URL:** " + url + "\n\n🚀 **Начинаю обработку...**")
    
    try:
        # Настраиваем драйвер
        await status_msg.edit_text("🎯 **Встреча обнаружена!**\n\n🔗 **URL:** " + url + "\n\n🚀 **Начинаю обработку...**\n⏳ Инициализация браузера...")
        bot.setup_driver(headless=True)  # Headless режим для сервера
        
        # Подключаемся к встрече
        meeting_names = {
            'google_meet': 'Google Meet',
            'zoom': 'Zoom',
            'yandex': 'Яндекс Телемост',
            'contour': 'Контур.Толк'
        }
        
        await status_msg.edit_text("🎯 **Встреча обнаружена!**\n\n🔗 **URL:** " + url + "\n\n🚀 **Начинаю обработку...**\n⏳ Подключаюсь к " + meeting_names.get(meeting_type, 'встрече') + "...")
        
        success = False
        if meeting_type == 'google_meet':
            success = bot.join_google_meet(url)
        elif meeting_type == 'zoom':
            success = bot.join_zoom_meeting(url)
        elif meeting_type == 'yandex':
            success = bot.join_yandex_telemost(url)
        elif meeting_type == 'contour':
            success = bot.join_contour_talk(url)
        
        if success:
            # Проверяем реальное подключение к встрече
            in_real_meeting = bot._verify_real_meeting_connection()
            
            if in_real_meeting:
                await status_msg.edit_text("🎯 **Встреча обнаружена!**\n\n🔗 **URL:** " + url + "\n\n🚀 **Начинаю обработку...**\n✅ Успешно подключился к встрече!")
                
                # Начинаем запись
                await update.message.reply_text("🎙️ Записываю аудио встречи...")
                
                if bot.start_recording():
                    # Сохраняем бота в активные
                    active_bots[user_id] = bot
                    
                    # Отправляем информацию и кнопки управления
                    info = bot.get_meeting_info()
                    keyboard = [
                        [InlineKeyboardButton("⏹️ Остановить и транскрибировать", callback_data='stop_and_transcribe')],
                        [InlineKeyboardButton("🚪 Покинуть встречу", callback_data='leave_meeting')],
                        [InlineKeyboardButton("📊 Статус", callback_data='status')]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(info, reply_markup=reply_markup)
                    
                    # Запускаем мониторинг встречи
                    bot.start_meeting_monitoring()
                else:
                    await update.message.reply_text("❌ Не удалось начать запись аудио!")
                    bot.cleanup()
            else:
                # Не в реальной встрече — отправляем админу уведомление и не начинаем запись
                await status_msg.edit_text("❌ Бот не смог реально подключиться к встрече!\n\nВозможна имитация. Запись не начата.")
                bot._send_imitation_alert(url)
                bot.cleanup()
        else:
            error_text = (
                "❌ Не удалось подключиться к встрече.\n\n"
                "Возможные причины:\n"
                "• Встреча требует авторизации\n"
                "• Неверная ссылка\n"
                "• Встреча еще не началась\n"
            )
            await status_msg.edit_text(error_text)
            bot.cleanup()
    
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке встречи: {e}")
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")
        if 'bot' in locals():
            bot.cleanup()


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    bot = active_bots.get(user_id)
    
    if query.data == 'stop_and_transcribe':
        if not bot:
            await query.edit_message_text("❌ Нет активной встречи")
            return
        
        # Останавливаем запись
        bot.stop_recording()
        
        # Создаем транскрипт
        await query.edit_message_text("🎙️ Создаю транскрипт...")
        transcript = bot.transcribe_audio_whisper()
        
        if transcript:
            # Создаем отчет
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"transcript_{timestamp}.txt"
            
            report = f"📝 Транскрипт встречи\n"
            report += f"📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"🔗 URL: {bot.meeting_url}\n"
            report += f"⏱️ Длительность: {bot.get_meeting_info()}\n\n"
            report += "=" * 50 + "\n\n"
            report += transcript
            
            # Сохраняем в GitHub
            if bot.save_to_github(report, filename):
                await query.message.reply_text(
                    f"✅ Транскрипт сохранен в GitHub: `{filename}`",
                    parse_mode='Markdown'
                )
            
            # Отправляем файл пользователю
            try:
                # Сохраняем во временный файл
                temp_file = os.path.join(RECORD_DIR, filename)
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                # Отправляем документ
                with open(temp_file, 'rb') as f:
                    await query.message.reply_document(
                        document=f,
                        filename=filename,
                        caption="📝 Транскрипт встречи готов!"
                    )
                
                # Удаляем временный файл
                os.remove(temp_file)
                
            except Exception as e:
                logger.error(f"Ошибка отправки файла: {e}")
                # Отправляем как текст, если файл слишком большой
                if len(report) < 4000:
                    await query.message.reply_text(f"```\n{report}\n```", parse_mode='Markdown')
                else:
                    # Разбиваем на части
                    parts = [report[i:i+4000] for i in range(0, len(report), 4000)]
                    for i, part in enumerate(parts, 1):
                        await query.message.reply_text(
                            f"📝 Часть {i}/{len(parts)}:\n```\n{part}\n```",
                            parse_mode='Markdown'
                        )
        else:
            await query.message.reply_text(f"❌ {transcript or 'Не удалось создать транскрипт'}")
        
        # Очищаем ресурсы
        bot.cleanup()
        if user_id in active_bots:
            del active_bots[user_id]
        
        await query.message.reply_text("✅ Встреча завершена. Отправьте новую ссылку для следующей встречи.")
    
    elif query.data == 'leave_meeting':
        if not bot:
            await query.edit_message_text("❌ Нет активной встречи")
            return
        
        bot.cleanup()
        if user_id in active_bots:
            del active_bots[user_id]
        
        await query.edit_message_text("👋 Покинул встречу. Запись остановлена.")
    
    elif query.data == 'status':
        if bot and bot.recording:
            info = bot.get_meeting_info()
            await query.message.reply_text(f"🟢 *Статус: Активен*\n\n{info}", parse_mode='Markdown')
        else:
            await query.message.reply_text("🔴 *Статус: Неактивен*\n\nНет активных встреч", parse_mode='Markdown')
    
    elif query.data == 'help':
        await help_command(query, context)


def main():
    """Главная функция"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
        sys.exit(1)
    
    logger.info("🤖 Запуск Meeting Bot v2.2...")
    logger.info("✅ ИСПРАВЛЕНО: Запись на всю встречу (НЕ 3 минуты!)")
    logger.info("✅ ИСПРАВЛЕНО: Улучшено присоединение к встречам")
    logger.info(f"📁 Директория записей: {RECORD_DIR}")
    logger.info(f"🎤 Модель Whisper: {WHISPER_MODEL}")
    logger.info(f"⏱️ Таймаут встречи: {MEETING_TIMEOUT_MIN} минут")
    
    # Проверяем наличие необходимых инструментов
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        logger.info("✅ ffmpeg найден")
    except:
        logger.error("❌ ffmpeg не найден! Установите: apt-get install ffmpeg")
    
    try:
        subprocess.run(['google-chrome', '--version'], capture_output=True, check=True)
        logger.info("✅ Google Chrome найден")
    except:
        logger.warning("⚠️ Google Chrome не найден, проверяю Chromium...")
        try:
            subprocess.run(['chromium', '--version'], capture_output=True, check=True)
            logger.info("✅ Chromium найден")
        except:
            logger.error("❌ Chrome/Chromium не найден!")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_meeting_url))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Запускаем бота
    logger.info("✅ Meeting Bot запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        # Отправка уведомления админу в Telegram
        import requests
        ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')
        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
        if ADMIN_CHAT_ID and TELEGRAM_BOT_TOKEN:
            msg = f"❌ Meeting Bot упал!\n\nОшибка: {e}"
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            try:
                requests.post(url, data={
                    'chat_id': ADMIN_CHAT_ID,
                    'text': msg,
                    'parse_mode': 'Markdown'
                })
            except Exception as err:
                logger.error(f"Ошибка отправки Telegram уведомления админу: {err}")
        sys.exit(1)