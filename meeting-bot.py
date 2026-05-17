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
import subprocess
import tempfile
import re
import time
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Selenium для автоматизации браузера
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

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
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'goqorhopar/b24')
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'medium')
RECORD_DIR = os.getenv('RECORD_DIR', '/opt/meeting-bot/recordings')
MEETING_TIMEOUT_MIN = int(os.getenv('MEETING_TIMEOUT_MIN', '180'))  # 3 часа по умолчанию
CHROME_PROFILE_DIR = os.getenv('CHROME_PROFILE_DIR', '/opt/meeting-bot/chrome-profile')

# Директории
Path(RECORD_DIR).mkdir(parents=True, exist_ok=True)
Path(CHROME_PROFILE_DIR).mkdir(parents=True, exist_ok=True)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, bot_token: str, message: str, parse_mode: str = 'Markdown') -> bool:
    """Централизованная функция отправки сообщений в Telegram"""
    if not (chat_id and bot_token):
        logger.warning("TELEGRAM_BOT_TOKEN или chat_id не заданы")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = requests.post(url, data={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode
        }, timeout=10)
        
        if resp.status_code == 200:
            logger.info("Telegram сообщение отправлено")
            return True
        else:
            logger.error(f"Ошибка отправки Telegram сообщения: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Исключение при отправке Telegram сообщения: {e}")
        return False


def send_telegram_photo(chat_id: str, bot_token: str, photo_path: str, caption: str = "") -> bool:
    """Централизованная функция отправки фото в Telegram"""
    if not (chat_id and bot_token):
        logger.warning("TELEGRAM_BOT_TOKEN или chat_id не заданы")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        with open(photo_path, 'rb') as img:
            resp = requests.post(url, data={
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }, files={'photo': img}, timeout=30)
        
        if resp.status_code == 200:
            logger.info("Telegram фото отправлено")
            return True
        else:
            logger.error(f"Ошибка отправки Telegram фото: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Исключение при отправке Telegram фото: {e}")
        return False


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
        self._temp_profile_dir = None
        
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
            
        # КРИТИЧНЫЕ настройки для предотвращения падения Chrome
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-domain-reliability')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-web-resources')
        options.add_argument('--enable-features=NetworkService,NetworkServiceLogging')
        options.add_argument('--force-color-profile=srgb')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--safebrowsing-disable-auto-update')
        options.add_argument('--enable-automation')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')

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

        # Создаем уникальную директорию профиля для предотвращения конфликтов
        temp_profile_dir = tempfile.mkdtemp(prefix='meetingbot_chrome_')
        options.add_argument(f'--user-data-dir={temp_profile_dir}')
        
        # Дополнительные флаги для предотвращения ошибок JSON
        options.add_argument('--disable-logging')
        options.add_argument('--disable-gpu-logging')
        options.add_argument('--disable-dev-tools')
        options.add_argument('--disable-extensions-file-access-check')
        options.add_argument('--disable-extensions-http-throttling')
        options.add_argument('--disable-extensions-except')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-background-mode')
        options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-domain-reliability')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-web-resources')
        options.add_argument('--safebrowsing-disable-auto-update')
        options.add_argument('--enable-automation')
        options.add_argument('--password-store=basic')
        options.add_argument('--use-mock-keychain')
        
        # Копируем существующий профиль если он есть (только безопасные файлы)
        if os.path.exists(CHROME_PROFILE_DIR):
            try:
                # Копируем только безопасные файлы профиля
                safe_files = ['Default/Preferences', 'Default/Cookies', 'Default/Login Data']
                for safe_file in safe_files:
                    src = os.path.join(CHROME_PROFILE_DIR, safe_file)
                    dst = os.path.join(temp_profile_dir, safe_file)
                    if os.path.exists(src):
                        # Создаем директорию если нужно
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                logger.info(f"Безопасные файлы профиля скопированы из {CHROME_PROFILE_DIR}")
            except Exception as e:
                logger.warning(f"Не удалось скопировать профиль: {e}")
        
        # Сохраняем путь для последующей очистки
        self._temp_profile_dir = temp_profile_dir

        # Инициализация драйвера с повторными попытками
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Попытка инициализации Chrome {attempt}/{max_attempts}")
                
                # Принудительно убиваем все процессы Chrome перед запуском
                if attempt > 1:
                    try:
                        subprocess.run(['pkill', '-f', 'chrome'], capture_output=True, timeout=5)
                        time.sleep(2)
                    except Exception:
                        pass
                
                self.driver = webdriver.Chrome(options=options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                logger.info(f"Chrome драйвер инициализирован с временным профилем: {temp_profile_dir}")

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
                
                # Если дошли сюда - успешно инициализировали
                break
                
            except Exception as e:
                error_msg = str(e).lower()
                logger.error(f"Ошибка инициализации Chrome (попытка {attempt}): {e}")
                
                # Очищаем драйвер если он был создан
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except Exception:
                        pass
                    self.driver = None
                
                # Если это последняя попытка или не JSON ошибка - выбрасываем исключение
                if attempt == max_attempts or 'json' not in error_msg:
                    logger.error(f"Не удалось инициализировать Chrome после {max_attempts} попыток")
                    raise
                
                # Ждем перед следующей попыткой
                time.sleep(3)

    def safe_get(self, url: str, retries: int = 2) -> bool:
        """Безопасная загрузка URL с перезапуском драйвера при краше вкладки"""
        for attempt in range(1, retries + 1):
            try:
                # Проверяем, что драйвер существует и активен
                if not self.driver:
                    logger.warning("Драйвер не инициализирован, создаем новый")
                    self.setup_driver(headless=True)
                
                self.driver.get(url)
                time.sleep(3)
                return True
                
            except WebDriverException as e:
                msg = str(e).lower()
                if 'tab crashed' in msg or 'disconnected' in msg or 'chrome not reachable' in msg:
                    logger.error(f"Краш вкладки/сессии при загрузке URL: {e}. Попытка {attempt}/{retries}")
                    
                    # Принудительная очистка драйвера
                    try:
                        if self.driver:
                            self.driver.quit()
                    except Exception as cleanup_error:
                        logger.debug(f"Ошибка при закрытии драйвера: {cleanup_error}")
                    finally:
                        self.driver = None
                    
                    # Ждем перед пересозданием
                    time.sleep(2)
                    
                    # Реинициализация драйвера только если это не последняя попытка
                    if attempt < retries:
                        try:
                            self.setup_driver(headless=True)
                            logger.info(f"Драйвер пересоздан, попытка {attempt + 1}")
                        except Exception as setup_error:
                            logger.error(f"Ошибка пересоздания драйвера: {setup_error}")
                            return False
                        continue
                    else:
                        logger.error("Исчерпаны все попытки пересоздания драйвера")
                        return False
                else:
                    logger.error(f"WebDriverException: {e}")
                    return False
                    
            except Exception as e:
                logger.error(f"Ошибка загрузки URL: {e}")
                return False
                
        return False

    def _force_cleanup_driver(self):
        """Принудительная очистка драйвера для предотвращения утечек памяти"""
        try:
            if self.driver:
                # Закрываем все окна
                try:
                    self.driver.quit()
                except Exception:
                    pass
                
                # Принудительно убиваем процесс Chrome если он завис
                try:
                    subprocess.run(['pkill', '-f', 'chrome'], capture_output=True, timeout=5)
                except Exception:
                    pass
                
                self.driver = None
                logger.info("Драйвер принудительно очищен")
            
            # Очищаем временную директорию профиля
            if hasattr(self, '_temp_profile_dir') and self._temp_profile_dir:
                try:
                    if os.path.exists(self._temp_profile_dir):
                        shutil.rmtree(self._temp_profile_dir)
                        logger.info(f"Временная директория профиля очищена: {self._temp_profile_dir}")
                except Exception as cleanup_error:
                    logger.debug(f"Ошибка очистки временной директории: {cleanup_error}")
                finally:
                    self._temp_profile_dir = None
                    
        except Exception as e:
            logger.debug(f"Ошибка принудительной очистки драйвера: {e}")
        
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
    
    def join_google_meet(self, meeting_url: str, name: str = "Meeting Bot") -> bool:
        """Присоединиться к Google Meet с улучшенной логикой и диагностикой"""
        try:
            logger.info(f"[Google Meet] Открываем: {meeting_url}")
            self.meeting_url = meeting_url
            
            # Загружаем страницу с повторными попытками
            if not self.safe_get(meeting_url, retries=2):
                logger.error("[Google Meet] Не удалось загрузить страницу")
                return False

            # УВЕЛИЧЕНО время ожидания загрузки
            logger.info("[Google Meet] Ожидание загрузки страницы...")
            time.sleep(12)  # Было 8, стало 12
            
            # Диагностика 1: Проверяем текущий URL
            current_url = self.driver.current_url
            logger.info(f"[Google Meet] Текущий URL: {current_url}")
            
            # Проверка авторизации
            if "accounts.google.com" in current_url:
                logger.warning("[Google Meet] Требуется авторизация Google")
                self._capture_and_notify("googlemeet_auth_required")
                return False
            
            # Диагностика 2: Сохраняем скриншот начального состояния
            try:
                self.driver.save_screenshot("/tmp/meet_step1_loaded.png")
                logger.info("[Google Meet] Скриншот 1: страница загружена")
            except:
                pass
            
            # Заполняем имя
            name_filled = False
            try:
                logger.info("[Google Meet] Ищем поле ввода имени...")
                name_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                logger.info(f"[Google Meet] Найдено полей ввода: {len(name_inputs)}")
                
                for inp in name_inputs:
                    try:
                        if not inp.is_displayed():
                            continue
                        placeholder = (inp.get_attribute('placeholder') or '').lower()
                        aria_label = (inp.get_attribute('aria-label') or '').lower()
                        logger.info(f"[Google Meet] Поле: placeholder='{placeholder}', aria-label='{aria_label}'")
                        
                        if 'name' in placeholder or 'имя' in placeholder or 'name' in aria_label:
                            inp.clear()
                            inp.send_keys(name)
                            logger.info(f"[Google Meet] ✅ Введено имя: {name}")
                            name_filled = True
                            time.sleep(1)
                            break
                    except Exception as e:
                        logger.debug(f"[Google Meet] Ошибка при работе с полем: {e}")
                
                if not name_filled:
                    logger.info("[Google Meet] Поле имени не найдено (возможно, не требуется)")
            except Exception as e:
                logger.debug(f"[Google Meet] Не удалось ввести имя: {e}")

            # Диагностика 3: Сохраняем скриншот после ввода имени
            try:
                self.driver.save_screenshot("/tmp/meet_step2_name.png")
                logger.info("[Google Meet] Скриншот 2: после ввода имени")
            except:
                pass
            
            # Отключаем медиа ДО входа
            logger.info("[Google Meet] Попытка отключить медиа до входа...")
            self._disable_media_before_join()
            
            # Ищем кнопку Join
            logger.info("[Google Meet] Ищем кнопку присоединения...")
            join_clicked = False
            
            join_patterns = [
                ('css', "button[aria-label*='Join now' i]"),
                ('css', "button[aria-label*='Ask to join' i]"),
                ('css', "button[jsname='Qx7uuf']"),
                ('xpath', "//button[contains(translate(., 'JOIN', 'join'), 'join')]"),
                ('xpath', "//button[contains(., 'Join now')]"),
                ('xpath', "//button[contains(., 'Ask to join')]"),
                ('xpath', "//button[contains(., 'Присоединиться')]"),
                ('xpath', "//span[contains(translate(., 'JOIN', 'join'), 'join')]/parent::button"),
            ]
            
            for method, selector in join_patterns:
                try:
                    if method == 'css':
                        buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                    
                    logger.info(f"[Google Meet] Селектор {selector}: найдено {len(buttons)} кнопок")
                    
                    for btn in buttons:
                        try:
                            if btn.is_displayed() and btn.is_enabled():
                                btn_text = btn.text or btn.get_attribute('aria-label') or 'unknown'
                                logger.info(f"[Google Meet] Пытаюсь нажать кнопку: '{btn_text}'")
                                btn.click()
                                logger.info(f"[Google Meet] ✅ Нажата кнопка: '{btn_text}'")
                                join_clicked = True
                                time.sleep(10)  # УВЕЛИЧЕНО с 8 до 10
                                break
                        except Exception as e:
                            logger.debug(f"[Google Meet] Не удалось нажать кнопку: {e}")
                    
                    if join_clicked:
                        break
                except Exception as e:
                    logger.debug(f"[Google Meet] Ошибка с селектором {selector}: {e}")
            
            if not join_clicked:
                logger.warning("[Google Meet] ⚠️ Не удалось найти кнопку Join стандартными методами")
                # Последняя попытка - поиск по тексту
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"[Google Meet] Проверяю все кнопки на странице: {len(all_buttons)}")
                for btn in all_buttons:
                    try:
                        text = (btn.text or '').lower()
                        aria = (btn.get_attribute('aria-label') or '').lower()
                        if any(word in text or word in aria for word in ['join', 'присоединиться', 'войти']):
                            if btn.is_displayed() and btn.is_enabled():
                                logger.info(f"[Google Meet] Найдена кнопка по тексту: '{btn.text or aria}'")
                                btn.click()
                                join_clicked = True
                                time.sleep(10)
                                break
                    except:
                        pass
            
            # Диагностика 4: Сохраняем скриншот после нажатия Join
            try:
                self.driver.save_screenshot("/tmp/meet_step3_clicked.png")
                logger.info("[Google Meet] Скриншот 3: после нажатия Join")
            except:
                pass
            
            # ОЖИДАЕМ ЗАГРУЗКУ ВСТРЕЧИ
            logger.info("[Google Meet] Ожидание загрузки встречи...")
            time.sleep(12)  # УВЕЛИЧЕНО с 8 до 12
            
            # Диагностика 5: Финальный URL и скриншот
            final_url = self.driver.current_url
            logger.info(f"[Google Meet] Финальный URL: {final_url}")
            
            try:
                self.driver.save_screenshot("/tmp/meet_step4_final.png")
                logger.info("[Google Meet] Скриншот 4: финальное состояние")
            except:
                pass
            
            # УПРОЩЕННАЯ ПРОВЕРКА
            logger.info("[Google Meet] Проверка подключения...")
            
            # 1. Проверка URL
            if "meet.google.com" not in final_url:
                logger.error("[Google Meet] ❌ URL не содержит meet.google.com")
                self._capture_and_notify("googlemeet_wrong_url")
                return False
            
            # 2. Проверка наличия элементов (минимум 1)
            indicators = [
                "div[jsname='BOHaEe']",
                "div[data-is-muted]",
                "button[aria-label*='camera']",
                "button[aria-label*='microphone']",
                "video",
                "canvas",
            ]
            
            found_count = 0
            for selector in indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        found_count += 1
                        logger.info(f"[Google Meet] ✅ Найден индикатор: {selector} ({len(elements)} шт.)")
                except:
                    pass
            
            logger.info(f"[Google Meet] Всего найдено индикаторов: {found_count}")
            
            # 3. Проверка ошибок
            errors = [
                "Unable to join",
                "Meeting not found",
                "Access denied",
                "Не удалось присоединиться",
            ]
            
            has_error = False
            for error_text in errors:
                try:
                    if self.driver.find_elements(By.XPATH, f"//div[contains(text(), '{error_text}')]"):
                        logger.error(f"[Google Meet] ❌ Найдена ошибка: {error_text}")
                        has_error = True
                        break
                except:
                    pass
            
            # РЕШЕНИЕ: достаточно правильного URL + хотя бы 1 индикатор + нет ошибок
            if found_count >= 1 and not has_error:
                logger.info("[Google Meet] ✅ УСПЕШНО подключились к встрече!")
                # Отключаем медиа в активной встрече
                self._disable_media_in_meeting()
                return True
            else:
                logger.warning(f"[Google Meet] ⚠️ Не удалось подтвердить подключение. Индикаторы: {found_count}, Ошибки: {has_error}")
                self._capture_and_notify("googlemeet_verification_failed")
                return False
                
        except Exception as e:
            logger.error(f"[Google Meet] ❌ Критическая ошибка: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._capture_and_notify("googlemeet_exception")
            return False
    
    def _disable_media_before_join(self):
        """Отключить камеру и микрофон ДО входа в встречу (на экране предпросмотра)"""
        try:
            logger.info("[Media] Поиск кнопок камеры/микрофона на предпросмотре...")
            
            # Ищем все видимые кнопки с aria-label
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label]")
            logger.info(f"[Media] Найдено кнопок с aria-label: {len(buttons)}")
            
            for btn in buttons:
                try:
                    if not btn.is_displayed():
                        continue
                        
                    aria_label = (btn.get_attribute('aria-label') or '').lower()
                    
                    # Камера
                    if 'camera' in aria_label or 'видео' in aria_label:
                        if 'turn off' in aria_label or 'выключить' in aria_label:
                            btn.click()
                            logger.info(f"[Media] ✅ Камера отключена: {aria_label}")
                            time.sleep(0.5)
                    
                    # Микрофон
                    if 'microphone' in aria_label or 'mic' in aria_label or 'микрофон' in aria_label:
                        if 'turn off' in aria_label or 'выключить' in aria_label or 'mute' in aria_label:
                            btn.click()
                            logger.info(f"[Media] ✅ Микрофон отключен: {aria_label}")
                            time.sleep(0.5)
                except Exception as e:
                    logger.debug(f"[Media] Ошибка с кнопкой: {e}")
        except Exception as e:
            logger.debug(f"[Media] Ошибка отключения медиа до входа: {e}")
    
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
                # Попробуем разные варианты URL для входа
                original_url = meeting_url
                
                # Вариант 1: Стандартный веб-клиент
                if '?' in meeting_url:
                    web_url = meeting_url + '&web=1&un=0'
                else:
                    web_url = meeting_url + '?web=1&un=0'
                
                # Вариант 2: Прямая ссылка на встречу
                meeting_id = meeting_url.split('/j/')[1].split('?')[0]
                direct_url = f"https://us05web.zoom.us/j/{meeting_id}"
                
                # Вариант 3: С параметрами для принудительного веб-входа
                force_web_url = f"https://us05web.zoom.us/j/{meeting_id}?web=1&un=0&pwd="
                if 'pwd=' in original_url:
                    pwd = original_url.split('pwd=')[1]
                    force_web_url += pwd
                
                logger.info(f"Попробуем URL: {web_url}")
                meeting_url = web_url
            
            self.meeting_url = meeting_url
            if not self.safe_get(meeting_url, retries=2):
                return False
            time.sleep(5)
            
            # Обрабатываем cookie-баннер
            try:
                cookie_accept = self.driver.find_element(By.XPATH, "//button[contains(text(), 'ACCEPT COOKIES') or contains(text(), 'Accept')]")
                if cookie_accept.is_displayed():
                    cookie_accept.click()
                    logger.info("Приняты cookies")
                    time.sleep(2)
            except Exception as e:
                logger.debug(f"Cookie-баннер не найден: {e}")
            
            # Закрываем всплывающие окна
            try:
                close_buttons = self.driver.find_elements(By.XPATH, "//button[@aria-label='Close'] | //button[contains(@class, 'close')] | //*[contains(@class, 'close')]")
                for btn in close_buttons:
                    if btn.is_displayed():
                        btn.click()
                        logger.info("Закрыто всплывающее окно")
                        time.sleep(1)
            except Exception as e:
                logger.debug(f"Всплывающие окна не найдены: {e}")
            
            # Ищем кнопку "Join from Browser" / "Launch Meeting"
            try:
                web_join_selectors = [
                    "//a[contains(text(), 'Join from Browser')]",
                    "//button[contains(text(), 'Join from Browser')]",
                    "//a[contains(text(), 'Launch Meeting')]",
                    "//button[contains(text(), 'Launch Meeting')]",
                    "//a[contains(text(), 'browser')]",
                    "//button[contains(text(), 'browser')]",
                    "//a[contains(@href, 'web')]",
                    "//button[contains(@class, 'web')]"
                ]
                
                for selector in web_join_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for btn in elements:
                            if btn.is_displayed() and btn.is_enabled():
                                btn.click()
                                logger.info(f"Нажата кнопка входа через браузер: {selector}")
                                time.sleep(5)
                                break
                        else:
                            continue
                        break
                    except Exception as e:
                        logger.debug(f"Селектор {selector} не сработал: {e}")
            except Exception as e:
                logger.debug(f"Кнопка входа через браузер не найдена: {e}")
            
            # Если не удалось найти кнопку входа через браузер, попробуем альтернативный способ
            try:
                # Проверяем, не пытается ли Zoom открыть десктопное приложение
                current_url = self.driver.current_url
                if 'zoom.us/j/' in current_url and 'web=1' not in current_url:
                    # Перезагружаем страницу с параметром web=1
                    if '?' in current_url:
                        new_url = current_url + '&web=1&un=0'
                    else:
                        new_url = current_url + '?web=1&un=0'
                    
                    logger.info(f"Перезагружаем с веб-клиентом: {new_url}")
                    self.driver.get(new_url)
                    time.sleep(5)
                    
                    # Снова обрабатываем cookie-баннер
                    try:
                        cookie_accept = self.driver.find_element(By.XPATH, "//button[contains(text(), 'ACCEPT COOKIES') or contains(text(), 'Accept')]")
                        if cookie_accept.is_displayed():
                            cookie_accept.click()
                            logger.info("Приняты cookies (повторно)")
                            time.sleep(2)
                    except:
                        pass
                
                # Проверяем, попали ли мы на страницу успеха (#success)
                elif '#success' in current_url:
                    logger.info("Попали на страницу успеха, ищем кнопку входа в встречу")
                    
                    # Ищем кнопки для входа в встречу после успешной авторизации
                    meeting_join_selectors = [
                        "//button[contains(text(), 'Join Meeting')]",
                        "//a[contains(text(), 'Join Meeting')]",
                        "//button[contains(text(), 'Enter Meeting')]",
                        "//a[contains(text(), 'Enter Meeting')]",
                        "//button[contains(text(), 'Join')]",
                        "//a[contains(text(), 'Join')]",
                        "//button[contains(@class, 'join')]",
                        "//a[contains(@class, 'join')]",
                        "//button[contains(@id, 'join')]",
                        "//a[contains(@id, 'join')]",
                    ]
                    
                    button_found = False
                    for selector in meeting_join_selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            for btn in elements:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn.click()
                                    logger.info(f"Нажата кнопка входа в встречу: {selector}")
                                    time.sleep(5)
                                    button_found = True
                                    break
                            if button_found:
                                break
                        except Exception as e:
                            logger.debug(f"Селектор {selector} не сработал: {e}")
                    
                    # Если не нашли кнопку, попробуем разные URL
                    if not button_found and '#success' in self.driver.current_url:
                        # Извлекаем ID встречи из URL
                        meeting_id = None
                        if '/j/' in current_url:
                            meeting_id = current_url.split('/j/')[1].split('?')[0]
                        
                        if meeting_id:
                            # Попробуем разные варианты URL
                            urls_to_try = [
                                f"https://us05web.zoom.us/j/{meeting_id}?web=1&un=0",
                                f"https://zoom.us/j/{meeting_id}?web=1&un=0",
                                f"https://us05web.zoom.us/j/{meeting_id}",
                                f"https://zoom.us/j/{meeting_id}",
                            ]
                            
                            # Добавляем пароль если есть
                            if 'pwd=' in current_url:
                                pwd = current_url.split('pwd=')[1].split('&')[0]
                                for i, url in enumerate(urls_to_try):
                                    if '?' in url:
                                        urls_to_try[i] = url + f"&pwd={pwd}"
                                    else:
                                        urls_to_try[i] = url + f"?pwd={pwd}"
                            
                            for url in urls_to_try:
                                logger.info(f"Пробуем альтернативный URL: {url}")
                                self.driver.get(url)
                                time.sleep(5)
                                
                                # Проверяем, попали ли мы в встречу
                                if '#success' not in self.driver.current_url and '/wc/' not in self.driver.current_url:
                                    logger.info("Успешно перешли в встречу!")
                                    break
                        else:
                            # Fallback - перезагружаем без #success
                            clean_url = current_url.split('#')[0]
                            logger.info(f"Перезагружаем без #success: {clean_url}")
                            self.driver.get(clean_url)
                            time.sleep(5)
                        
            except Exception as e:
                logger.debug(f"Альтернативный способ не сработал: {e}")
            
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
                "//button[contains(@aria-label, 'Turn off')]",
                "//button[contains(@aria-label, 'Turn on')]",
                "//div[contains(@class, 'participants')]",
                "//canvas",  # Видео элемент
                "//div[contains(@class, 'meeting')]",
                "//div[contains(@class, 'zoom')]",
                "//div[contains(@class, 'webinar')]",
                "//div[contains(@id, 'meeting')]",
                "//div[contains(@id, 'zoom')]",
                "//video",  # HTML5 видео элемент
                "//audio",  # HTML5 аудио элемент
                "//div[contains(@class, 'controls')]",
                "//div[contains(@class, 'toolbar')]",
                "//button[contains(@class, 'zm-btn')]",
                "//div[contains(@class, 'footer')]",
                "//div[contains(@class, 'main')]",
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
                "//div[contains(text(), 'Please download and install')]",
                "//div[contains(text(), 'Did not open Zoom')]",
                "//div[contains(text(), 'Zoom Workplace app')]",
                "//div[contains(text(), 'Download Now')]",
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
            url_check = (
                "zoom.us" in current_url and 
                ("/j/" in current_url or "/meeting/" in current_url or "/web/" in current_url) and
                "web=1" in current_url and  # Должны быть в веб-клиенте
                "#success" not in current_url and  # НЕ должны быть на странице успеха
                "/wc/" not in current_url  # НЕ должны быть на странице веб-клиента (это не сама встреча)
            )
            
            # Строгая проверка - должны быть активные медиа элементы
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
            
            # УПРОЩЕННАЯ проверка - достаточно платформы и хотя бы 1 индикатора
            connection_success = (
                in_meeting and found_indicators >= 1 and not has_error
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
            
            # Если Chrome упал, попробуем перезапустить драйвер
            if "tab crashed" in str(e) or "chrome not reachable" in str(e).lower():
                logger.warning("Chrome упал, пытаемся перезапустить драйвер...")
                try:
                    if self.driver:
                        self.driver.quit()
                    time.sleep(5)
                    if self.setup_driver(headless=True):
                        logger.info("Драйвер перезапущен, повторяем попытку...")
                        return self.join_zoom_meeting(meeting_url, name)
                except Exception as restart_error:
                    logger.error(f"Не удалось перезапустить драйвер: {restart_error}")
            
            self._capture_and_notify("zoom")
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
            self.meeting_url = meeting_url
            if not self.safe_get(meeting_url, retries=2):
                return False
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
            self._capture_and_notify("yandex")
            return False
    
    def join_contour_talk(self, meeting_url: str, name: str = "Meeting Bot"):
        """Присоединиться к Контур.Толк"""
        try:
            logger.info(f"Открываем Контур.Толк: {meeting_url}")
            self.meeting_url = meeting_url
            if not self.safe_get(meeting_url, retries=2):
                return False
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
            self._capture_and_notify("contour")
            return False
    def _verify_real_meeting_connection(self) -> bool:
        """УПРОЩЕННАЯ проверка - только для дополнительной валидации"""
        try:
            if not self.driver:
                return False
            
            url = self.driver.current_url.lower()
            platforms = ['meet.google.com', 'zoom.us', 'telemost.yandex', 'talk.contour.ru']
            return any(p in url for p in platforms)
        except:
            return False
    
    def _send_imitation_alert(self, meeting_url: str):
        """Отправить уведомление об имитации подключения"""
        send_telegram_message(
            chat_id=ADMIN_CHAT_ID,
            bot_token=TELEGRAM_BOT_TOKEN,
            message=(
                f"🚨 **Meeting Bot: Имитация подключения!**\n\n"
                f"🔗 URL: {meeting_url}\n"
                f"⏰ Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"❌ Бот не смог реально подключиться к встрече.\n"
                f"Возможные причины:\n"
                f"• Требуется авторизация\n"
                f"• Встреча еще не началась\n"
                f"• Неверная ссылка\n"
                f"• Проблемы с cookies"
            )
        )
    
    def _send_screenshot_to_admin(self, screenshot_path, meeting_url):
        """Отправить скриншот ошибки админу в Telegram"""
        caption = f"❌ Meeting Bot не смог подключиться к встрече!\nURL: {meeting_url}"
        send_telegram_photo(
            chat_id=ADMIN_CHAT_ID,
            bot_token=TELEGRAM_BOT_TOKEN,
            photo_path=screenshot_path,
            caption=caption
        )

    def _capture_and_notify(self, platform_tag: str):
        try:
            screenshot_path = f"/tmp/meetingbot_{platform_tag}_fail_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.warning(f"Скриншот ошибки сохранен: {screenshot_path}")
            self._send_screenshot_to_admin(screenshot_path, self.meeting_url or "")
        except Exception as err:
            logger.error(f"Ошибка сохранения скриншота: {err}")
    
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
            self._force_cleanup_driver()
            logger.info("👋 Покинули встречу")
        except Exception as e:
            logger.error(f"❌ Ошибка при выходе из встречи: {e}")
    
    def cleanup(self):
        """Очистка ресурсов"""
        self.meeting_active = False  # Останавливаем мониторинг
        if self.recording:
            self.stop_recording()
        self._force_cleanup_driver()
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
        "🤖 *Meeting Bot v3.0* - Автоматическое участие во встречах\n\n"
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
        
        if success:  # Проверка уже в join_* методах
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
    
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке встречи: {e}")
        await status_msg.edit_text(f"❌ Произошла ошибка: {str(e)}")
        if 'bot' in locals():
            bot.cleanup()
    
    if not success:
        error_text = (
            "❌ Не удалось подключиться к встрече.\n\n"
            "Возможные причины:\n"
            "• Встреча требует авторизации\n"
            "• Неверная ссылка\n"
            "• Встреча еще не началась\n"
        )
        await status_msg.edit_text(error_text)
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
    
    logger.info("🤖 Запуск Meeting Bot v3.0...")
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
        send_telegram_message(
            chat_id=ADMIN_CHAT_ID,
            bot_token=TELEGRAM_BOT_TOKEN,
            message=f"❌ Meeting Bot упал!\n\nОшибка: {e}"
        )
        sys.exit(1)