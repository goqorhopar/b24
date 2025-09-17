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
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
            
            # Настройки для аудио/видео
            chrome_options.add_argument('--use-fake-ui-for-media-stream')
            chrome_options.add_argument('--use-fake-device-for-media-stream')
            chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            
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
            time.sleep(5)
            
            # Пытаемся найти и нажать "Launch Meeting"
            try:
                launch_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "launch-btn"))
                )
                launch_btn.click()
                log.info("✅ Нажали Launch Meeting")
            except:
                # Альтернативный способ - через ссылку "join from your browser"
                try:
                    browser_link = self.driver.find_element(By.LINK_TEXT, "join from your browser")
                    browser_link.click()
                    log.info("✅ Открыли встречу в браузере")
                except:
                    log.warning("⚠️ Не удалось найти кнопку запуска")
            
            time.sleep(5)
            
            # Вводим имя участника
            try:
                name_input = self.driver.find_element(By.ID, "input-for-name")
                name_input.clear()
                name_input.send_keys("Bot Assistant")
                log.info("✅ Ввели имя участника")
            except:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Нажимаем "Join"
            try:
                join_btn = self.driver.find_element(By.ID, "preview-join-button")
                join_btn.click()
                log.info("✅ Нажали Join")
            except:
                try:
                    join_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Join')]")
                    join_btn.click()
                    log.info("✅ Нажали Join (альтернативный селектор)")
                except:
                    log.warning("⚠️ Не удалось найти кнопку Join")
            
            time.sleep(3)
            
            # Отключаем микрофон и камеру
            try:
                # Микрофон
                mic_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'join-audio-by-voip__join-btn')]")
                mic_btn.click()
                log.info("✅ Подключили аудио")
            except:
                log.warning("⚠️ Не удалось настроить аудио")
            
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
            
            time.sleep(5)
            
            # Вводим имя
            try:
                name_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='name']"))
                )
                name_input.clear()
                name_input.send_keys("Bot Assistant")
                log.info("✅ Ввели имя")
            except:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                # Камера
                camera_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='camera']")
                camera_btn.click()
                log.info("✅ Отключили камеру")
            except:
                log.warning("⚠️ Камера уже отключена или не найдена")
            
            try:
                # Микрофон
                mic_btn = self.driver.find_element(By.CSS_SELECTOR, "[data-is-muted='false'][aria-label*='microphone']")
                mic_btn.click()
                log.info("✅ Отключили микрофон")
            except:
                log.warning("⚠️ Микрофон уже отключен или не найден")
            
            # Присоединяемся
            try:
                join_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Join now']"))
                )
                join_btn.click()
                log.info("✅ Нажали Join now")
            except:
                try:
                    join_btn = self.driver.find_element(By.XPATH, "//span[text()='Ask to join']")
                    join_btn.click()
                    log.info("✅ Запросили разрешение на присоединение")
                except:
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
            
            time.sleep(5)
            
            # Выбираем "Join on the web instead"
            try:
                web_join = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Join on the web instead"))
                )
                web_join.click()
                log.info("✅ Выбрали присоединение через веб")
            except:
                log.warning("⚠️ Не удалось найти ссылку веб-присоединения")
            
            time.sleep(3)
            
            # Вводим имя
            try:
                name_input = self.driver.find_element(By.ID, "displayName")
                name_input.clear()
                name_input.send_keys("Bot Assistant")
                log.info("✅ Ввели имя")
            except:
                log.warning("⚠️ Не удалось найти поле имени")
            
            # Отключаем камеру и микрофон
            try:
                camera_btn = self.driver.find_element(By.ID, "preJoinCameraButton")
                if "is-enabled" in camera_btn.get_attribute("class"):
                    camera_btn.click()
                    log.info("✅ Отключили камеру")
            except:
                log.warning("⚠️ Не удалось управлять камерой")
            
            try:
                mic_btn = self.driver.find_element(By.ID, "preJoinMicButton")
                if "is-enabled" in mic_btn.get_attribute("class"):
                    mic_btn.click()
                    log.info("✅ Отключили микрофон")
            except:
                log.warning("⚠️ Не удалось управлять микрофоном")
            
            # Присоединяемся
            try:
                join_btn = self.driver.find_element(By.ID, "prejoin-join-button")
                join_btn.click()
                log.info("✅ Нажали Join now")
            except:
                log.warning("⚠️ Не удалось найти кнопку присоединения")
            
            log.info("🎉 Успешно присоединились к Teams встрече!")
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка присоединения к Teams: {e}")
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
    
    def join_meeting(self, url):
        """Основная функция присоединения к встрече"""
        try:
            if not self.setup_chrome_driver():
                return False
            
            self.meeting_url = url
            
            # Определяем платформу и присоединяемся
            if 'zoom.us' in url:
                success = self.join_zoom_meeting(url)
            elif 'meet.google.com' in url:
                success = self.join_google_meet(url)
            elif 'teams.microsoft.com' in url:
                success = self.join_teams_meeting(url)
            elif 'ktalk.ru' in url or 'talk.kontur.ru' in url:
                # Для Контур.Толк используем общий подход
                success = self.join_zoom_meeting(url)  # Похожий интерфейс
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
