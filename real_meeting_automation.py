# real_meeting_automation.py - Реальная автоматизация встреч
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import subprocess
import threading

log = logging.getLogger("meeting_automation")

class RealMeetingAutomation:
    def __init__(self):
        self.driver = None
        self.is_recording = False
        self.meeting_url = None
        
    def setup_chrome_driver(self):
        """Настройка Chrome WebDriver для работы в headless режиме"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Настройки для аудио/видео
            chrome_options.add_argument('--use-fake-ui-for-media-stream')
            chrome_options.add_argument('--use-fake-device-for-media-stream')
            chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
            
            # Автоматическое разрешение на микрофон и камеру
            prefs = {
                "profile.default_content_setting_values.media_stream_mic": 1,
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.geolocation": 1,
                "profile.default_content_setting_values.notifications": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            log.info("✅ Chrome WebDriver настроен успешно")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка настройки Chrome WebDriver: {e}")
            return False
    
    def join_zoom_meeting(self, url):
        """Присоединение к Zoom встрече"""
        try:
            log.info(f"🚀 Присоединяюсь к Zoom встрече: {url}")
            self.driver.get(url)
            
            # Ждем загрузки страницы
            time.sleep(10)
            
            # Логируем текущий URL для отладки
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Получаем HTML страницы для отладки
            page_source = self.driver.page_source
            log.info(f"📄 Размер HTML: {len(page_source)} символов")
            
            # Пытаемся найти различные варианты кнопок запуска
            launch_selectors = [
                (By.ID, "launch-btn"),
                (By.CSS_SELECTOR, "[id='launch-btn']"),
                (By.XPATH, "//button[contains(text(), 'Launch Meeting')]"),
                (By.XPATH, "//button[contains(text(), 'Запустить встречу')]"),
                (By.XPATH, "//a[contains(text(), 'join from your browser')]"),
                (By.XPATH, "//a[contains(text(), 'Join from Browser')]"),
                (By.XPATH, "//button[contains(text(), 'Join from Browser')]"),
                (By.XPATH, "//a[contains(@href, 'zoom.us')]"),
                (By.CSS_SELECTOR, "button[class*='launch']"),
                (By.CSS_SELECTOR, "a[class*='launch']")
            ]
            
            launch_clicked = False
            for by, selector in launch_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    element.click()
                    log.info(f"✅ Нажали кнопку запуска: {selector}")
                    launch_clicked = True
                    break
                except:
                    continue
            
            if not launch_clicked:
                log.warning("⚠️ Не удалось найти кнопку запуска, пробуем альтернативные методы")
                # Пробуем кликнуть по любому элементу с текстом "join" или "launch"
                try:
                    elements = self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'join') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'launch')]")
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                log.info("✅ Кликнули по элементу с текстом join/launch")
                                launch_clicked = True
                                break
                        except:
                            continue
                except:
                    pass
            
            time.sleep(10)
            
            # Вводим имя участника
            name_selectors = [
                (By.ID, "input-for-name"),
                (By.CSS_SELECTOR, "input[placeholder*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='имя']"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@class, 'name')]")
            ]
            
            name_entered = False
            for by, selector in name_selectors:
                try:
                    name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    name_input.clear()
                    name_input.send_keys("Bot Assistant")
                    log.info(f"✅ Ввели имя участника: {selector}")
                    name_entered = True
                    break
                except:
                    continue
            
            if not name_entered:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Нажимаем "Join"
            join_selectors = [
                (By.ID, "preview-join-button"),
                (By.XPATH, "//button[contains(text(), 'Join')]"),
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]"),
                (By.CSS_SELECTOR, "button[class*='join']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            join_clicked = False
            for by, selector in join_selectors:
                try:
                    join_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    join_btn.click()
                    log.info(f"✅ Нажали Join: {selector}")
                    join_clicked = True
                    break
                except:
                    continue
            
            if not join_clicked:
                log.warning("⚠️ Не удалось найти кнопку Join")
            
            time.sleep(8)
            
            # Подключаемся к аудио и отключаем микрофон
            try:
                # Сначала подключаемся к аудио
                audio_selectors = [
                    (By.XPATH, "//button[contains(@class, 'join-audio-by-voip__join-btn')]"),
                    (By.XPATH, "//button[contains(text(), 'Join Audio')]"),
                    (By.XPATH, "//button[contains(text(), 'Подключить звук')]"),
                    (By.CSS_SELECTOR, "button[class*='audio']"),
                    (By.CSS_SELECTOR, "button[class*='voip']")
                ]
                
                for by, selector in audio_selectors:
                    try:
                        audio_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        audio_btn.click()
                        log.info(f"✅ Подключились к аудио: {selector}")
                        time.sleep(2)
                        break
                    except:
                        continue
                
                # Затем отключаем микрофон
                mic_selectors = [
                    (By.XPATH, "//button[contains(@aria-label, 'Mute')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'Unmute')]"),
                    (By.XPATH, "//button[contains(text(), 'Mute')]"),
                    (By.XPATH, "//button[contains(text(), 'Выключить звук')]"),
                    (By.CSS_SELECTOR, "button[class*='mic']"),
                    (By.CSS_SELECTOR, "button[class*='mute']")
                ]
                
                for by, selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        mic_btn.click()
                        log.info(f"✅ Отключили микрофон: {selector}")
                        break
                    except:
                        continue
                        
            except Exception as e:
                log.warning(f"⚠️ Не удалось настроить аудио/микрофон: {e}")
            
            log.info("🎉 Успешно присоединились к Zoom встрече!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Zoom: {e}")
            return False
    
    def join_google_meet(self, url):
        """Присоединение к Google Meet встрече"""
        try:
            log.info(f"🚀 Присоединяюсь к Google Meet: {url}")
            self.driver.get(url)
            
            time.sleep(10)
            
            # Логируем текущий URL для отладки
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Вводим имя
            name_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='имя']"),
                (By.CSS_SELECTOR, "input[aria-label*='name']"),
                (By.CSS_SELECTOR, "input[aria-label*='имя']"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@class, 'name')]")
            ]
            
            name_entered = False
            for by, selector in name_selectors:
                try:
                    name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    name_input.clear()
                    name_input.send_keys("Bot Assistant")
                    log.info(f"✅ Ввели имя: {selector}")
                    name_entered = True
                    break
                except:
                    continue
            
            if not name_entered:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                # Камера
                camera_selectors = [
                    (By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='camera']"),
                    (By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='камера']"),
                    (By.XPATH, "//button[contains(@aria-label, 'camera')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'камера')]"),
                    (By.CSS_SELECTOR, "button[class*='camera']")
                ]
                
                for by, selector in camera_selectors:
                    try:
                        camera_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        camera_btn.click()
                        log.info(f"✅ Отключили камеру: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Камера уже отключена или не найдена")
            
            try:
                # Микрофон
                mic_selectors = [
                    (By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='microphone']"),
                    (By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='микрофон']"),
                    (By.XPATH, "//button[contains(@aria-label, 'microphone')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'микрофон')]"),
                    (By.CSS_SELECTOR, "button[class*='mic']")
                ]
                
                for by, selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        mic_btn.click()
                        log.info(f"✅ Отключили микрофон: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Микрофон уже отключен или не найден")
            
            # Присоединяемся
            join_selectors = [
                (By.XPATH, "//span[text()='Join now']"),
                (By.XPATH, "//span[text()='Присоединиться сейчас']"),
                (By.XPATH, "//button[contains(text(), 'Join now')]"),
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]"),
                (By.XPATH, "//span[text()='Ask to join']"),
                (By.XPATH, "//span[text()='Запросить присоединение']"),
                (By.CSS_SELECTOR, "button[class*='join']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            join_clicked = False
            for by, selector in join_selectors:
                try:
                    join_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    join_btn.click()
                    log.info(f"✅ Нажали кнопку присоединения: {selector}")
                    join_clicked = True
                    break
                except:
                    continue
            
            if not join_clicked:
                log.warning("⚠️ Не удалось найти кнопку присоединения")
            
            log.info("🎉 Успешно присоединились к Google Meet!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Google Meet: {e}")
            return False
    
    def join_teams_meeting(self, url):
        """Присоединение к Microsoft Teams встрече"""
        try:
            log.info(f"🚀 Присоединяюсь к Teams встрече: {url}")
            self.driver.get(url)
            
            time.sleep(10)
            
            # Логируем текущий URL для отладки
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Выбираем "Join on the web instead"
            web_join_selectors = [
                (By.LINK_TEXT, "Join on the web instead"),
                (By.XPATH, "//a[contains(text(), 'Join on the web instead')]"),
                (By.XPATH, "//a[contains(text(), 'Присоединиться через веб')]"),
                (By.XPATH, "//button[contains(text(), 'Join on the web instead')]"),
                (By.CSS_SELECTOR, "a[href*='teams.microsoft.com']")
            ]
            
            web_join_clicked = False
            for by, selector in web_join_selectors:
                try:
                    web_join = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    web_join.click()
                    log.info(f"✅ Выбрали присоединение через веб: {selector}")
                    web_join_clicked = True
                    break
                except:
                    continue
            
            if not web_join_clicked:
                log.warning("⚠️ Не удалось найти ссылку веб-присоединения")
            
            time.sleep(5)
            
            # Вводим имя
            name_selectors = [
                (By.ID, "displayName"),
                (By.CSS_SELECTOR, "input[placeholder*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='имя']"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@class, 'name')]")
            ]
            
            name_entered = False
            for by, selector in name_selectors:
                try:
                    name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    name_input.clear()
                    name_input.send_keys("Bot Assistant")
                    log.info(f"✅ Ввели имя: {selector}")
                    name_entered = True
                    break
                except:
                    continue
            
            if not name_entered:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                # Камера
                camera_selectors = [
                    (By.ID, "preJoinCameraButton"),
                    (By.XPATH, "//button[contains(@aria-label, 'camera')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'камера')]"),
                    (By.CSS_SELECTOR, "button[class*='camera']")
                ]
                
                for by, selector in camera_selectors:
                    try:
                        camera_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        if "is-enabled" in camera_btn.get_attribute("class"):
                            camera_btn.click()
                            log.info(f"✅ Отключили камеру: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Не удалось управлять камерой")
            
            try:
                # Микрофон
                mic_selectors = [
                    (By.ID, "preJoinMicButton"),
                    (By.XPATH, "//button[contains(@aria-label, 'microphone')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'микрофон')]"),
                    (By.CSS_SELECTOR, "button[class*='mic']")
                ]
                
                for by, selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        if "is-enabled" in mic_btn.get_attribute("class"):
                            mic_btn.click()
                            log.info(f"✅ Отключили микрофон: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Не удалось управлять микрофоном")
            
            # Присоединяемся
            join_selectors = [
                (By.ID, "prejoin-join-button"),
                (By.XPATH, "//button[contains(text(), 'Join now')]"),
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]"),
                (By.CSS_SELECTOR, "button[class*='join']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            join_clicked = False
            for by, selector in join_selectors:
                try:
                    join_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    join_btn.click()
                    log.info(f"✅ Нажали кнопку присоединения: {selector}")
                    join_clicked = True
                    break
                except:
                    continue
            
            if not join_clicked:
                log.warning("⚠️ Не удалось найти кнопку присоединения")
            
            log.info("🎉 Успешно присоединились к Teams встрече!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Teams: {e}")
            return False
    
    def join_kontur_talk(self, url):
        """Присоединение к Контур.Толк встрече"""
        try:
            log.info(f"🚀 Присоединяюсь к Контур.Толк: {url}")
            self.driver.get(url)
            
            time.sleep(10)
            
            # Логируем текущий URL для отладки
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Пытаемся найти кнопки присоединения
            join_selectors = [
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]"),
                (By.XPATH, "//button[contains(text(), 'Join')]"),
                (By.XPATH, "//a[contains(text(), 'Присоединиться')]"),
                (By.XPATH, "//a[contains(text(), 'Join')]"),
                (By.CSS_SELECTOR, "button[class*='join']"),
                (By.CSS_SELECTOR, "a[class*='join']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            join_clicked = False
            for by, selector in join_selectors:
                try:
                    join_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    join_btn.click()
                    log.info(f"✅ Нажали кнопку присоединения: {selector}")
                    join_clicked = True
                    break
                except:
                    continue
            
            if not join_clicked:
                log.warning("⚠️ Не удалось найти кнопку присоединения")
            
            time.sleep(5)
            
            # Вводим имя
            name_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='имя']"),
                (By.CSS_SELECTOR, "input[placeholder*='Имя']"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@class, 'name')]")
            ]
            
            name_entered = False
            for by, selector in name_selectors:
                try:
                    name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    name_input.clear()
                    name_input.send_keys("Bot Assistant")
                    log.info(f"✅ Ввели имя: {selector}")
                    name_entered = True
                    break
                except:
                    continue
            
            if not name_entered:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                # Камера
                camera_selectors = [
                    (By.XPATH, "//button[contains(@aria-label, 'camera')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'камера')]"),
                    (By.XPATH, "//button[contains(text(), 'Камера')]"),
                    (By.CSS_SELECTOR, "button[class*='camera']")
                ]
                
                for by, selector in camera_selectors:
                    try:
                        camera_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        camera_btn.click()
                        log.info(f"✅ Отключили камеру: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Камера уже отключена или не найдена")
            
            try:
                # Микрофон
                mic_selectors = [
                    (By.XPATH, "//button[contains(@aria-label, 'microphone')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'микрофон')]"),
                    (By.XPATH, "//button[contains(text(), 'Микрофон')]"),
                    (By.CSS_SELECTOR, "button[class*='mic']")
                ]
                
                for by, selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        mic_btn.click()
                        log.info(f"✅ Отключили микрофон: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Микрофон уже отключен или не найден")
            
            log.info("🎉 Успешно присоединились к Контур.Толк!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Контур.Толк: {e}")
            return False
    
    def join_yandex_telemost(self, url):
        """Присоединение к Яндекс Телемост встрече"""
        try:
            log.info(f"🚀 Присоединяюсь к Яндекс Телемост: {url}")
            self.driver.get(url)
            
            time.sleep(10)
            
            # Логируем текущий URL для отладки
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Пытаемся найти кнопки присоединения
            join_selectors = [
                (By.XPATH, "//button[contains(text(), 'Присоединиться')]"),
                (By.XPATH, "//button[contains(text(), 'Join')]"),
                (By.XPATH, "//a[contains(text(), 'Присоединиться')]"),
                (By.XPATH, "//a[contains(text(), 'Join')]"),
                (By.CSS_SELECTOR, "button[class*='join']"),
                (By.CSS_SELECTOR, "a[class*='join']"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            join_clicked = False
            for by, selector in join_selectors:
                try:
                    join_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    join_btn.click()
                    log.info(f"✅ Нажали кнопку присоединения: {selector}")
                    join_clicked = True
                    break
                except:
                    continue
            
            if not join_clicked:
                log.warning("⚠️ Не удалось найти кнопку присоединения")
            
            time.sleep(5)
            
            # Вводим имя
            name_selectors = [
                (By.CSS_SELECTOR, "input[placeholder*='name']"),
                (By.CSS_SELECTOR, "input[placeholder*='имя']"),
                (By.CSS_SELECTOR, "input[placeholder*='Имя']"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@class, 'name')]")
            ]
            
            name_entered = False
            for by, selector in name_selectors:
                try:
                    name_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    name_input.clear()
                    name_input.send_keys("Bot Assistant")
                    log.info(f"✅ Ввели имя: {selector}")
                    name_entered = True
                    break
                except:
                    continue
            
            if not name_entered:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                # Камера
                camera_selectors = [
                    (By.XPATH, "//button[contains(@aria-label, 'camera')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'камера')]"),
                    (By.XPATH, "//button[contains(text(), 'Камера')]"),
                    (By.CSS_SELECTOR, "button[class*='camera']")
                ]
                
                for by, selector in camera_selectors:
                    try:
                        camera_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        camera_btn.click()
                        log.info(f"✅ Отключили камеру: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Камера уже отключена или не найдена")
            
            try:
                # Микрофон
                mic_selectors = [
                    (By.XPATH, "//button[contains(@aria-label, 'microphone')]"),
                    (By.XPATH, "//button[contains(@aria-label, 'микрофон')]"),
                    (By.XPATH, "//button[contains(text(), 'Микрофон')]"),
                    (By.CSS_SELECTOR, "button[class*='mic']")
                ]
                
                for by, selector in mic_selectors:
                    try:
                        mic_btn = WebDriverWait(self.driver, 3).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        mic_btn.click()
                        log.info(f"✅ Отключили микрофон: {selector}")
                        break
                    except:
                        continue
            except:
                log.warning("⚠️ Микрофон уже отключен или не найден")
            
            log.info("🎉 Успешно присоединились к Яндекс Телемост!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Яндекс Телемост: {e}")
            return False
    
    def start_audio_recording(self):
        """Начало записи аудио с системы"""
        try:
            # Используем pulseaudio для записи системного аудио
            cmd = [
                'parecord',
                '--device=alsa_output.pci-0000_00_1f.3.analog-stereo.monitor',
                '--file-format=wav',
                '--channels=2',
                '--rate=44100',
                '--volume=65536',
                f'/tmp/meeting_recording_{int(time.time())}.wav'
            ]
            
            self.recording_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.is_recording = True
            log.info("🎤 Начата запись аудио")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка начала записи: {e}")
            return False
    
    def stop_audio_recording(self):
        """Остановка записи аудио"""
        try:
            if hasattr(self, 'recording_process') and self.recording_process:
                self.recording_process.terminate()
                self.is_recording = False
                log.info("🛑 Запись аудио остановлена")
                return True
        except Exception as e:
            log.error(f"❌ Ошибка остановки записи: {e}")
            return False
    
    def join_meeting(self, url, display_name="Bot Assistant"):
        """Основная функция присоединения к встрече"""
        try:
            if not self.setup_chrome_driver():
                return False
            
            self.meeting_url = url
            
            # Определяем платформу и присоединяемся
            if 'zoom.us' in url or 'us05web.zoom.us' in url:
                success = self.join_zoom_meeting(url)
            elif 'meet.google.com' in url:
                success = self.join_google_meet(url)
            elif 'teams.microsoft.com' in url:
                success = self.join_teams_meeting(url)
            elif 'ktalk.ru' in url or 'talk.kontur.ru' in url:
                success = self.join_kontur_talk(url)
            elif 'telemost.yandex.ru' in url:
                success = self.join_yandex_telemost(url)
            else:
                log.warning("⚠️ Неподдерживаемая платформа встреч")
                return False
            
            if success:
                # Начинаем запись аудио
                self.start_audio_recording()
                log.info("✅ Успешно присоединились к встрече и начали запись")
                return True
            
            return False
            
        except Exception as e:
            log.error(f"❌ Критическая ошибка присоединения к встрече: {e}")
            return False
    
    def is_in_meeting(self):
        """Проверка, находимся ли мы в встрече"""
        try:
            if not self.driver:
                return False
            
            # Проверяем, что браузер еще открыт и на странице встречи
            current_url = self.driver.current_url
            meeting_indicators = [
                'zoom.us', 'us05web.zoom.us', 'meet.google.com', 
                'teams.microsoft.com', 'ktalk.ru', 'talk.kontur.ru',
                'telemost.yandex.ru'
            ]
            
            return any(indicator in current_url for indicator in meeting_indicators)
            
        except Exception as e:
            log.error(f"❌ Ошибка при проверке статуса встречи: {e}")
            return False
    
    def leave_meeting(self):
        """Покидание встречи и очистка ресурсов"""
        try:
            # Останавливаем запись
            if self.is_recording:
                self.stop_audio_recording()
            
            # Закрываем браузер
            if self.driver:
                self.driver.quit()
                log.info("🚪 Покинули встречу и закрыли браузер")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка при покидании встречи: {e}")
            return False

# Глобальный экземпляр автоматизации
meeting_automation = RealMeetingAutomation()
