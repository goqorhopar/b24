"""
Модуль автоматизации онлайн-встреч
Поддерживает Zoom, Google Meet, Teams, Контур.Толк
"""
import os
import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pyautogui
import cv2
import numpy as np
from urllib.parse import urlparse
import re

log = logging.getLogger(__name__)

class MeetingPlatform:
    """Базовый класс для платформы встречи"""
    
    def __init__(self, driver):
        self.driver = driver
        self.platform_name = self.__class__.__name__
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        """Присоединиться к встрече"""
        raise NotImplementedError
    
    def leave_meeting(self) -> bool:
        """Покинуть встречу"""
        raise NotImplementedError
    
    def is_in_meeting(self) -> bool:
        """Проверить, находимся ли мы в встрече"""
        raise NotImplementedError
    
    def mute_microphone(self) -> bool:
        """Отключить микрофон"""
        raise NotImplementedError
    
    def turn_off_camera(self) -> bool:
        """Отключить камеру"""
        raise NotImplementedError

class ZoomMeeting(MeetingPlatform):
    """Автоматизация для Zoom"""
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        try:
            log.info(f"Присоединение к Zoom встрече: {meeting_url}")
            self.driver.get(meeting_url)
            
            # Ожидание загрузки страницы Zoom
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Закрытие всплывающих окон если есть
            self._close_popups()
            
            # Ввод имени (если требуется)
            try:
                name_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "input-name"))
                )
                name_input.clear()
                name_input.send_keys(display_name)
            except TimeoutException:
                log.info("Поле для имени не найдено, продолжаем")
            
            # Нажатие кнопки присоединения
            join_button_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Join']"),
                (By.CSS_SELECTOR, "button.preview-join-button"),
                (By.CSS_SELECTOR, "button.join-button"),
                (By.XPATH, "//button[contains(text(), 'Join')]")
            ]
            
            for selector in join_button_selectors:
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
            time.sleep(5)
            
            # Отключение камеры и микрофона
            self.mute_microphone()
            self.turn_off_camera()
            
            return self.is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Zoom: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        try:
            # Поиск кнопки выхода
            leave_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Leave']"),
                (By.CSS_SELECTOR, "button.leave-button"),
                (By.XPATH, "//button[contains(text(), 'Leave')]")
            ]
            
            for selector in leave_selectors:
                try:
                    leave_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    leave_button.click()
                    
                    # Подтверждение выхода
                    confirm_selectors = [
                        (By.CSS_SELECTOR, "button[aria-label*='End']"),
                        (By.XPATH, "//button[contains(text(), 'End Meeting')]")
                    ]
                    
                    for confirm_selector in confirm_selectors:
                        try:
                            confirm_button = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable(confirm_selector)
                            )
                            confirm_button.click()
                            break
                        except TimeoutException:
                            continue
                    
                    log.info("Выход из Zoom встречи выполнен")
                    return True
                    
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при выходе из Zoom: {e}")
            return False
    
    def is_in_meeting(self) -> bool:
        try:
            # Проверка наличия элементов характерных для Zoom встречи
            meeting_indicators = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='Stop Video']"),
                (By.CSS_SELECTOR, ".zoom-meeting")
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
    
    def mute_microphone(self) -> bool:
        try:
            mute_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='Unmute']"),
                (By.CSS_SELECTOR, ".footer-button__mute")
            ]
            
            for selector in mute_selectors:
                try:
                    mute_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    mute_button.click()
                    log.info("Микрофон отключен в Zoom")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении микрофона в Zoom: {e}")
            return False
    
    def turn_off_camera(self) -> bool:
        try:
            video_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Stop Video']"),
                (By.CSS_SELECTOR, "button[aria-label*='Start Video']"),
                (By.CSS_SELECTOR, ".footer-button__video")
            ]
            
            for selector in video_selectors:
                try:
                    video_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    video_button.click()
                    log.info("Камера отключена в Zoom")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении камеры в Zoom: {e}")
            return False
    
    def _close_popups(self):
        """Закрытие всплывающих окон"""
        try:
            # Закрытие окна загрузки приложения
            close_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Close']"),
                (By.CSS_SELECTOR, ".close-button"),
                (By.XPATH, "//button[contains(text(), 'Cancel')]")
            ]
            
            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(selector)
                    )
                    close_button.click()
                    time.sleep(1)
                except TimeoutException:
                    continue
                    
        except Exception as e:
            log.debug(f"Ошибка при закрытии попапов: {e}")

class GoogleMeetMeeting(MeetingPlatform):
    """Автоматизация для Google Meet"""
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        try:
            log.info(f"Присоединение к Google Meet: {meeting_url}")
            self.driver.get(meeting_url)
            
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Закрытие всплывающих окон
            self._close_popups()
            
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
            
            time.sleep(5)
            
            # Отключение камеры и микрофона
            self.mute_microphone()
            self.turn_off_camera()
            
            return self.is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Google Meet: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        try:
            # Поиск кнопки выхода
            leave_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Leave call']"),
                (By.CSS_SELECTOR, "button[aria-label*='End call']"),
                (By.XPATH, "//button[contains(@aria-label, 'Leave')]")
            ]
            
            for selector in leave_selectors:
                try:
                    leave_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    leave_button.click()
                    log.info("Выход из Google Meet выполнен")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при выходе из Google Meet: {e}")
            return False
    
    def is_in_meeting(self) -> bool:
        try:
            meeting_indicators = [
                (By.CSS_SELECTOR, "button[aria-label*='microphone']"),
                (By.CSS_SELECTOR, "button[aria-label*='camera']"),
                (By.CSS_SELECTOR, "[data-is-meeting='true']")
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
    
    def mute_microphone(self) -> bool:
        try:
            mute_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='microphone']"),
                (By.CSS_SELECTOR, "button[aria-label*='mute']")
            ]
            
            for selector in mute_selectors:
                try:
                    mute_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    mute_button.click()
                    log.info("Микрофон отключен в Google Meet")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении микрофона в Google Meet: {e}")
            return False
    
    def turn_off_camera(self) -> bool:
        try:
            video_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='camera']"),
                (By.CSS_SELECTOR, "button[aria-label*='video']")
            ]
            
            for selector in video_selectors:
                try:
                    video_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    video_button.click()
                    log.info("Камера отключена в Google Meet")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении камеры в Google Meet: {e}")
            return False
    
    def _close_popups(self):
        """Закрытие всплывающих окон"""
        try:
            # Закрытие предложений по использованию приложения
            close_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Close']"),
                (By.CSS_SELECTOR, ".dismiss-button")
            ]
            
            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(selector)
                    )
                    close_button.click()
                    time.sleep(1)
                except TimeoutException:
                    continue
                    
        except Exception as e:
            log.debug(f"Ошибка при закрытии попапов: {e}")

class TeamsMeeting(MeetingPlatform):
    """Автоматизация для Microsoft Teams"""
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        try:
            log.info(f"Присоединение к Teams: {meeting_url}")
            self.driver.get(meeting_url)
            
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Закрытие всплывающих окон
            self._close_popups()
            
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
            
            time.sleep(5)
            
            # Отключение камеры и микрофона
            self.mute_microphone()
            self.turn_off_camera()
            
            return self.is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Teams: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        try:
            # Поиск кнопки выхода
            leave_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Leave']"),
                (By.CSS_SELECTOR, "button[aria-label*='Hang up']"),
                (By.XPATH, "//button[contains(@aria-label, 'Leave')]")
            ]
            
            for selector in leave_selectors:
                try:
                    leave_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    leave_button.click()
                    log.info("Выход из Teams выполнен")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при выходе из Teams: {e}")
            return False
    
    def is_in_meeting(self) -> bool:
        try:
            meeting_indicators = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='Camera']"),
                (By.CSS_SELECTOR, ".meeting-controls")
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
    
    def mute_microphone(self) -> bool:
        try:
            mute_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Mute']"),
                (By.CSS_SELECTOR, "button[aria-label*='microphone']")
            ]
            
            for selector in mute_selectors:
                try:
                    mute_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    mute_button.click()
                    log.info("Микрофон отключен в Teams")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении микрофона в Teams: {e}")
            return False
    
    def turn_off_camera(self) -> bool:
        try:
            video_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Camera']"),
                (By.CSS_SELECTOR, "button[aria-label*='video']")
            ]
            
            for selector in video_selectors:
                try:
                    video_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    video_button.click()
                    log.info("Камера отключена в Teams")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении камеры в Teams: {e}")
            return False
    
    def _close_popups(self):
        """Закрытие всплывающих окон"""
        try:
            # Закрытие предложений по использованию приложения
            close_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Close']"),
                (By.CSS_SELECTOR, ".dismiss-button")
            ]
            
            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(selector)
                    )
                    close_button.click()
                    time.sleep(1)
                except TimeoutException:
                    continue
                    
        except Exception as e:
            log.debug(f"Ошибка при закрытии попапов: {e}")

class KonturTalkMeeting(MeetingPlatform):
    """Автоматизация для Контур.Толк"""
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        try:
            log.info(f"Присоединение к Контур.Толк: {meeting_url}")
            self.driver.get(meeting_url)
            
            # Ожидание загрузки страницы
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Закрытие всплывающих окон
            self._close_popups()
            
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
            
            time.sleep(5)
            
            # Отключение камеры и микрофона
            self.mute_microphone()
            self.turn_off_camera()
            
            return self.is_in_meeting()
            
        except Exception as e:
            log.error(f"Ошибка при присоединении к Контур.Толк: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        try:
            # Поиск кнопки выхода
            leave_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Выйти']"),
                (By.CSS_SELECTOR, "button[aria-label*='Покинуть']"),
                (By.XPATH, "//button[contains(text(), 'Выйти')]"),
                (By.XPATH, "//button[contains(text(), 'Покинуть')]")
            ]
            
            for selector in leave_selectors:
                try:
                    leave_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    leave_button.click()
                    log.info("Выход из Контур.Толк выполнен")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при выходе из Контур.Толк: {e}")
            return False
    
    def is_in_meeting(self) -> bool:
        try:
            meeting_indicators = [
                (By.CSS_SELECTOR, "button[aria-label*='Микрофон']"),
                (By.CSS_SELECTOR, "button[aria-label*='Камера']"),
                (By.CSS_SELECTOR, ".meeting-controls")
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
    
    def mute_microphone(self) -> bool:
        try:
            mute_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Микрофон']"),
                (By.CSS_SELECTOR, "button[aria-label*='Выключить микрофон']")
            ]
            
            for selector in mute_selectors:
                try:
                    mute_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    mute_button.click()
                    log.info("Микрофон отключен в Контур.Толк")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении микрофона в Контур.Толк: {e}")
            return False
    
    def turn_off_camera(self) -> bool:
        try:
            video_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Камера']"),
                (By.CSS_SELECTOR, "button[aria-label*='Выключить камеру']")
            ]
            
            for selector in video_selectors:
                try:
                    video_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    video_button.click()
                    log.info("Камера отключена в Контур.Толк")
                    return True
                except TimeoutException:
                    continue
            
            return False
            
        except Exception as e:
            log.error(f"Ошибка при отключении камеры в Контур.Толк: {e}")
            return False
    
    def _close_popups(self):
        """Закрытие всплывающих окон"""
        try:
            # Закрытие предложений по использованию приложения
            close_selectors = [
                (By.CSS_SELECTOR, "button[aria-label*='Закрыть']"),
                (By.CSS_SELECTOR, ".close-button")
            ]
            
            for selector in close_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable(selector)
                    )
                    close_button.click()
                    time.sleep(1)
                except TimeoutException:
                    continue
                    
        except Exception as e:
            log.debug(f"Ошибка при закрытии попапов: {e}")

class MeetingAutomation:
    """Основной класс автоматизации встреч"""
    
    def __init__(self, headless: bool = True):
        self.driver = None
        self.current_platform = None
        self.headless = headless
        self.meeting_platforms = {
            'zoom': ZoomMeeting,
            'google': GoogleMeetMeeting,
            'meet': GoogleMeetMeeting,
            'teams': TeamsMeeting,
            'microsoft': TeamsMeeting,
            'kontur': KonturTalkMeeting,
            'talk': KonturTalkMeeting
        }
    
    def setup_driver(self):
        """Настройка WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Разрешения для аудио и видео
        chrome_options.add_argument('--use-fake-ui-for-media-stream')
        chrome_options.add_argument('--allow-file-access-from-files')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            log.info("WebDriver успешно настроен")
            return True
        except Exception as e:
            log.error(f"Ошибка при настройке WebDriver: {e}")
            return False
    
    def detect_platform(self, meeting_url: str) -> Optional[str]:
        """Определение платформы встречи по URL"""
        url_lower = meeting_url.lower()
        
        for platform_key in self.meeting_platforms.keys():
            if platform_key in url_lower:
                log.info(f"Обнаружена платформа: {platform_key}")
                return platform_key
        
        # Дополнительная проверка по доменам
        parsed_url = urlparse(meeting_url)
        domain = parsed_url.netloc.lower()
        
        if 'zoom.us' in domain:
            return 'zoom'
        elif 'meet.google.com' in domain:
            return 'google'
        elif 'teams.microsoft.com' in domain:
            return 'teams'
        elif 'talk.kontur.ru' in domain:
            return 'kontur'
        
        log.warning(f"Не удалось определить платформу для URL: {meeting_url}")
        return None
    
    def join_meeting(self, meeting_url: str, display_name: str = "AI Assistant") -> bool:
        """Присоединиться к встрече"""
        if not self.driver:
            if not self.setup_driver():
                return False
        
        platform_key = self.detect_platform(meeting_url)
        if not platform_key:
            log.error("Не удалось определить платформу встречи")
            return False
        
        platform_class = self.meeting_platforms.get(platform_key)
        if not platform_class:
            log.error(f"Неизвестная платформа: {platform_key}")
            return False
        
        self.current_platform = platform_class(self.driver)
        
        try:
            result = self.current_platform.join_meeting(meeting_url, display_name)
            if result:
                log.info(f"Успешно присоединились к встрече на платформе {platform_key}")
            else:
                log.error(f"Не удалось присоединиться к встрече на платформе {platform_key}")
            return result
        except Exception as e:
            log.error(f"Ошибка при присоединении к встрече: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        """Покинуть встречу"""
        if not self.current_platform:
            log.warning("Нет активной встречи")
            return False
        
        try:
            result = self.current_platform.leave_meeting()
            if result:
                log.info("Успешно покинули встречу")
                self.current_platform = None
            else:
                log.error("Не удалось покинуть встречу")
            return result
        except Exception as e:
            log.error(f"Ошибка при выходе из встречи: {e}")
            return False
    
    def is_in_meeting(self) -> bool:
        """Проверить, находимся ли мы в встрече"""
        if not self.current_platform:
            return False
        
        try:
            return self.current_platform.is_in_meeting()
        except Exception as e:
            log.error(f"Ошибка при проверке статуса встречи: {e}")
            return False
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.driver:
            try:
                self.driver.quit()
                log.info("WebDriver закрыт")
            except Exception as e:
                log.error(f"Ошибка при закрытии WebDriver: {e}")
            finally:
                self.driver = None
                self.current_platform = None

# Функция для создания экземпляра автоматизации
def create_meeting_automation(headless: bool = True) -> MeetingAutomation:
    """Создать экземпляр автоматизации встреч"""
    return MeetingAutomation(headless=headless)
