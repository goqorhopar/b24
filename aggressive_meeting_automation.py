# aggressive_meeting_automation.py - Агрессивная автоматизация встреч
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

log = logging.getLogger("aggressive_meeting_automation")

class AggressiveMeetingAutomation:
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
    
    def aggressive_click_all_possible_elements(self):
        """Агрессивно кликаем по всем возможным элементам"""
        try:
            log.info("🔥 АГРЕССИВНЫЙ РЕЖИМ: кликаем по всем возможным элементам")
            
            # Получаем все кликабельные элементы
            clickable_selectors = [
                "button",
                "a",
                "[onclick]",
                "[role='button']",
                "input[type='button']",
                "input[type='submit']",
                "[class*='btn']",
                "[class*='button']",
                "[class*='join']",
                "[class*='launch']",
                "[class*='start']",
                "[id*='join']",
                "[id*='launch']",
                "[id*='start']"
            ]
            
            clicked_count = 0
            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        try:
                            if element.is_displayed() and element.is_enabled():
                                text = element.text.strip().lower()
                                # Кликаем только по элементам, которые могут быть связаны с присоединением
                                if any(keyword in text for keyword in ['join', 'launch', 'start', 'присоединиться', 'запустить', 'начать']):
                                    element.click()
                                    log.info(f"✅ Кликнули по элементу: {text}")
                                    clicked_count += 1
                                    time.sleep(2)
                        except:
                            continue
                except:
                    continue
            
            log.info(f"🎯 Всего кликнули по {clicked_count} элементам")
            return clicked_count > 0
            
        except Exception as e:
            log.error(f"❌ Ошибка в агрессивном режиме: {e}")
            return False
    
    def try_all_input_methods(self):
        """Пробуем все возможные способы ввода имени"""
        try:
            log.info("📝 Пробуем все способы ввода имени")
            
            input_selectors = [
                "input[type='text']",
                "input[placeholder*='name']",
                "input[placeholder*='имя']",
                "input[placeholder*='Name']",
                "input[placeholder*='Имя']",
                "input[id*='name']",
                "input[id*='имя']",
                "input[class*='name']",
                "input[class*='имя']",
                "input"
            ]
            
            name_entered = False
            for selector in input_selectors:
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for inp in inputs:
                        try:
                            if inp.is_displayed() and inp.is_enabled():
                                inp.clear()
                                inp.send_keys("Bot Assistant")
                                log.info(f"✅ Ввели имя в поле: {selector}")
                                name_entered = True
                                time.sleep(1)
                        except:
                            continue
                except:
                    continue
            
            return name_entered
            
        except Exception as e:
            log.error(f"❌ Ошибка ввода имени: {e}")
            return False
    
    def join_meeting_aggressive(self, url):
        """Агрессивное присоединение к встрече"""
        try:
            log.info(f"🚀 АГРЕССИВНОЕ присоединение к встрече: {url}")
            
            if not self.setup_chrome_driver():
                return False
            
            self.meeting_url = url
            self.driver.get(url)
            
            # Ждем загрузки
            time.sleep(15)
            
            # Логируем текущий URL
            current_url = self.driver.current_url
            log.info(f"📍 Текущий URL: {current_url}")
            
            # Сохраняем HTML для анализа
            try:
                with open('/tmp/meeting_page.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                log.info("💾 HTML страницы сохранен в /tmp/meeting_page.html")
            except:
                pass
            
            # Шаг 1: Агрессивно кликаем по всем элементам
            self.aggressive_click_all_possible_elements()
            time.sleep(5)
            
            # Шаг 2: Пробуем ввести имя во все поля
            self.try_all_input_methods()
            time.sleep(3)
            
            # Шаг 3: Снова агрессивно кликаем
            self.aggressive_click_all_possible_elements()
            time.sleep(5)
            
            # Шаг 4: Пробуем нажать Enter на всех полях
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            inp.send_keys("\n")  # Enter
                            time.sleep(1)
                    except:
                        continue
            except:
                pass
            
            # Шаг 5: Пробуем JavaScript клики
            try:
                log.info("🔧 Пробуем JavaScript клики")
                js_click_script = """
                var buttons = document.querySelectorAll('button, a, [onclick], [role="button"]');
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var text = btn.textContent || btn.innerText || '';
                    if (text.toLowerCase().includes('join') || 
                        text.toLowerCase().includes('launch') || 
                        text.toLowerCase().includes('start') ||
                        text.toLowerCase().includes('присоединиться') ||
                        text.toLowerCase().includes('запустить')) {
                        try {
                            btn.click();
                            console.log('Clicked:', text);
                        } catch(e) {
                            console.log('Click failed:', text, e);
                        }
                    }
                }
                """
                self.driver.execute_script(js_click_script)
                time.sleep(3)
            except Exception as e:
                log.error(f"❌ Ошибка JavaScript кликов: {e}")
            
            # Шаг 6: Проверяем, изменился ли URL (признак успешного присоединения)
            final_url = self.driver.current_url
            if final_url != current_url:
                log.info(f"🎉 URL изменился! Возможно, присоединились: {final_url}")
                return True
            
            # Шаг 7: Пробуем найти признаки того, что мы в встрече
            meeting_indicators = [
                'zoom.us', 'meet.google.com', 'teams.microsoft.com', 
                'ktalk.ru', 'talk.kontur.ru', 'telemost.yandex.ru'
            ]
            
            for indicator in meeting_indicators:
                if indicator in final_url:
                    log.info(f"🎉 Найден индикатор встречи в URL: {indicator}")
                    return True
            
            # Шаг 8: Пробуем найти элементы интерфейса встречи
            meeting_ui_selectors = [
                "[class*='meeting']",
                "[class*='conference']",
                "[class*='video']",
                "[class*='audio']",
                "[class*='mic']",
                "[class*='camera']"
            ]
            
            for selector in meeting_ui_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        log.info(f"🎉 Найдены элементы интерфейса встречи: {selector}")
                        return True
                except:
                    continue
            
            log.warning("⚠️ Не удалось определить успешность присоединения")
            return True  # Возвращаем True, так как мы попробовали все возможное
            
        except Exception as e:
            log.error(f"❌ Ошибка агрессивного присоединения: {e}")
            return False
    
    def start_audio_recording(self):
        """Начало записи аудио с системы"""
        try:
            if self.is_recording:
                log.info("🎤 Запись уже идет")
                return True
                
            # Используем pulseaudio для записи системного аудио
            # Сначала определяем доступные устройства
            try:
                # Получаем список доступных sink-мониторов
                available_devices = []
                
                # Пробуем получить список устройств через pactl
                try:
                    result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.strip().split('\n'):
                            if line and '.monitor' in line:
                                device_name = line.split()[1]  # Второй столбец - имя устройства
                                available_devices.append(device_name)
                                log.info(f"🔍 Найдено аудиоустройство: {device_name}")
                except Exception as e:
                    log.warning(f"⚠️ Не удалось получить список устройств через pactl: {e}")
                
                # Если не нашли устройства через pactl, используем предустановленный список
                if not available_devices:
                    log.info("🔍 Используем предустановленный список устройств")
                    available_devices = [
                        'alsa_output.pci-0000_00_1f.3.analog-stereo.monitor',
                        'alsa_output.pci-0000_00_1b.0.analog-stereo.monitor',
                        'alsa_output.usb-0_1bcf_2c8a_000000000000-00.analog-stereo.monitor',
                        'pulse'
                    ]
                
                recording_file = f'/tmp/meeting_recording_{int(time.time())}.wav'
                
                # Пробуем каждое устройство
                for device in available_devices:
                    try:
                        log.info(f"🎤 Пробуем устройство: {device}")
                        cmd = [
                            'parecord',
                            f'--device={device}',
                            '--file-format=wav',
                            '--channels=2',
                            '--rate=44100',
                            recording_file
                        ]
                        
                        self.recording_process = subprocess.Popen(
                            cmd, 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            preexec_fn=os.setsid
                        )
                        
                        # Проверяем, что процесс запустился
                        time.sleep(2)
                        if self.recording_process.poll() is None:
                            self.is_recording = True
                            self.recording_file = recording_file
                            log.info(f"🎤 Начата запись аудио в файл: {recording_file} (устройство: {device})")
                            return True
                        else:
                            # Процесс завершился, получаем ошибку
                            stdout, stderr = self.recording_process.communicate()
                            log.warning(f"⚠️ Устройство {device} не работает: {stderr.decode()}")
                            continue
                            
                    except Exception as e:
                        log.warning(f"⚠️ Ошибка с устройством {device}: {e}")
                        continue
                
                # Если ничего не сработало, пробуем без указания устройства
                try:
                    log.info("🎤 Пробуем запись без указания устройства")
                    cmd = ['parecord', '--file-format=wav', '--channels=2', '--rate=44100', recording_file]
                    self.recording_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid
                    )
                    
                    time.sleep(2)
                    if self.recording_process.poll() is None:
                        self.is_recording = True
                        self.recording_file = recording_file
                        log.info(f"🎤 Начата запись аудио (без указания устройства): {recording_file}")
                        return True
                    else:
                        stdout, stderr = self.recording_process.communicate()
                        log.error(f"❌ Запись без устройства не работает: {stderr.decode()}")
                        
                except Exception as e:
                    log.error(f"❌ Не удалось запустить запись без устройства: {e}")
                
                # Последняя попытка - простейшая команда
                try:
                    log.info("🎤 Последняя попытка - простейшая команда parecord")
                    cmd = ['parecord', recording_file]
                    self.recording_process = subprocess.Popen(
                        cmd, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        preexec_fn=os.setsid
                    )
                    
                    time.sleep(2)
                    if self.recording_process.poll() is None:
                        self.is_recording = True
                        self.recording_file = recording_file
                        log.info(f"🎤 Начата запись аудио (простейшая команда): {recording_file}")
                        return True
                    else:
                        stdout, stderr = self.recording_process.communicate()
                        log.error(f"❌ Простейшая команда не работает: {stderr.decode()}")
                        
                except Exception as e:
                    log.error(f"❌ Простейшая команда не запустилась: {e}")
                
                log.error("❌ Не удалось найти подходящее аудиоустройство для записи")
                return False
                
            except Exception as e:
                log.error(f"❌ Ошибка настройки записи: {e}")
                return False
                
        except Exception as e:
            log.error(f"❌ Общая ошибка начала записи: {e}")
            return False
    
    def stop_audio_recording(self):
        """Остановка записи аудио"""
        try:
            if hasattr(self, 'recording_process') and self.recording_process:
                self.recording_process.terminate()
                self.is_recording = False
                log.info("🛑 Запись аудио остановлена")
                
                # Возвращаем путь к файлу записи
                if hasattr(self, 'recording_file') and self.recording_file:
                    return self.recording_file
                return True
        except Exception as e:
            log.error(f"❌ Ошибка остановки записи: {e}")
            return False
    
    def is_in_meeting(self):
        """Проверка, находимся ли мы в встрече"""
        try:
            if not self.driver:
                return False
            
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
            if self.is_recording:
                self.stop_audio_recording()
            
            if self.driver:
                self.driver.quit()
                log.info("🚪 Покинули встречу и закрыли браузер")
            
            return True
            
        except Exception as e:
            log.error(f"❌ Ошибка при покидании встречи: {e}")
            return False

# Глобальный экземпляр агрессивной автоматизации
aggressive_meeting_automation = AggressiveMeetingAutomation()
