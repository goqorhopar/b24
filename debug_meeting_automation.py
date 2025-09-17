#!/usr/bin/env python3
"""
Скрипт для отладки автоматизации встреч
"""
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def setup_chrome_driver():
    """Настройка Chrome WebDriver с максимальной отладкой"""
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
        
        driver = webdriver.Chrome(options=chrome_options)
        log.info("✅ Chrome WebDriver настроен успешно")
        return driver
        
    except Exception as e:
        log.error(f"❌ Ошибка настройки Chrome WebDriver: {e}")
        return None

def debug_zoom_meeting(url):
    """Отладка присоединения к Zoom встрече"""
    driver = setup_chrome_driver()
    if not driver:
        return False
    
    try:
        log.info(f"🚀 Отладка Zoom встречи: {url}")
        driver.get(url)
        
        # Ждем загрузки страницы
        time.sleep(15)
        
        # Логируем текущий URL
        current_url = driver.current_url
        log.info(f"📍 Текущий URL: {current_url}")
        
        # Получаем HTML страницы
        page_source = driver.page_source
        log.info(f"📄 Размер HTML: {len(page_source)} символов")
        
        # Сохраняем HTML для анализа
        with open('/tmp/zoom_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        log.info("💾 HTML страницы сохранен в /tmp/zoom_page.html")
        
        # Ищем все кнопки на странице
        buttons = driver.find_elements(By.TAG_NAME, "button")
        log.info(f"🔍 Найдено кнопок: {len(buttons)}")
        
        for i, button in enumerate(buttons):
            try:
                text = button.text.strip()
                if text:
                    log.info(f"  Кнопка {i+1}: '{text}'")
            except:
                pass
        
        # Ищем все ссылки
        links = driver.find_elements(By.TAG_NAME, "a")
        log.info(f"🔗 Найдено ссылок: {len(links)}")
        
        for i, link in enumerate(links):
            try:
                text = link.text.strip()
                href = link.get_attribute('href')
                if text and ('join' in text.lower() or 'launch' in text.lower() or 'присоединиться' in text.lower()):
                    log.info(f"  Ссылка {i+1}: '{text}' -> {href}")
            except:
                pass
        
        # Ищем все input поля
        inputs = driver.find_elements(By.TAG_NAME, "input")
        log.info(f"📝 Найдено input полей: {len(inputs)}")
        
        for i, inp in enumerate(inputs):
            try:
                placeholder = inp.get_attribute('placeholder')
                input_type = inp.get_attribute('type')
                if placeholder:
                    log.info(f"  Input {i+1}: type='{input_type}', placeholder='{placeholder}'")
            except:
                pass
        
        # Пытаемся найти элементы по различным селекторам
        selectors_to_try = [
            "button",
            "a",
            "[class*='join']",
            "[class*='launch']",
            "[id*='join']",
            "[id*='launch']",
            "[onclick*='join']",
            "[onclick*='launch']"
        ]
        
        for selector in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    log.info(f"🎯 Селектор '{selector}': найдено {len(elements)} элементов")
                    for i, elem in enumerate(elements[:5]):  # Показываем только первые 5
                        try:
                            text = elem.text.strip()
                            tag = elem.tag_name
                            if text:
                                log.info(f"    {i+1}. <{tag}>: '{text}'")
                        except:
                            pass
            except Exception as e:
                log.error(f"❌ Ошибка с селектором '{selector}': {e}")
        
        # Ждем еще немного и проверяем, изменился ли URL
        time.sleep(5)
        final_url = driver.current_url
        if final_url != current_url:
            log.info(f"🔄 URL изменился: {final_url}")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка отладки: {e}")
        return False
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Использование: python debug_meeting_automation.py <URL_встречи>")
        sys.exit(1)
    
    url = sys.argv[1]
    debug_zoom_meeting(url)
