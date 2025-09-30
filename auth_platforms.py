#!/usr/bin/env python3
"""
Скрипт авторизации на всех платформах для Meeting Bot
Сохраняет cookies и sessionStorage для автоматического входа
"""

import os
import json
import time
from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Пути для сохранения данных
COOKIES_PATH = "cookies.json"
SELENIUM_COOKIES_PATH = "selenium_cookies.json"
STORAGE_PATH = "storage.json"

class PlatformAuth:
    def __init__(self):
        self.playwright_cookies = {}
        self.selenium_cookies = {}
        self.storage_data = {}
        
    def save_playwright_cookies(self, context):
        """Сохранить cookies из Playwright"""
        try:
            # Получаем cookies
            cookies = context.cookies()
            self.playwright_cookies = cookies
            
            # Сохраняем в файл
            with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Playwright cookies сохранены в {COOKIES_PATH}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения Playwright cookies: {e}")
            return False
    
    def save_selenium_cookies(self, driver):
        """Сохранить cookies из Selenium"""
        try:
            # Получаем cookies
            cookies = driver.get_cookies()
            self.selenium_cookies = cookies
            
            # Сохраняем в файл
            with open(SELENIUM_COOKIES_PATH, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Selenium cookies сохранены в {SELENIUM_COOKIES_PATH}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения Selenium cookies: {e}")
            return False
    
    def save_storage_data(self, driver):
        """Сохранить sessionStorage и localStorage"""
        try:
            # Получаем sessionStorage
            session_storage = driver.execute_script("return window.sessionStorage;")
            
            # Получаем localStorage
            local_storage = driver.execute_script("return window.localStorage;")
            
            storage_data = {
                "sessionStorage": session_storage,
                "localStorage": local_storage,
                "timestamp": time.time()
            }
            
            self.storage_data = storage_data
            
            # Сохраняем в файл
            with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Storage данные сохранены в {STORAGE_PATH}")
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения storage: {e}")
            return False
    
    def setup_selenium_driver(self):
        """Настройка Selenium драйвера"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Критичные настройки для предотвращения закрытия браузера
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--disable-default-apps')
        
        # Настройки для стабильности
        options.add_experimental_option("detach", True)  # Не закрывать браузер автоматически
        options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Увеличиваем таймауты
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(60)
        
        return driver
    
    def auth_google_meet(self, driver):
        """Авторизация в Google Meet"""
        print("\n🔵 Авторизация в Google Meet...")
        try:
            driver.get("https://accounts.google.com/signin")
            print("📝 Выполните вход в Google аккаунт")
            print("   - Введите email и пароль")
            print("   - Пройдите двухфакторную аутентификацию если требуется")
            print("   - Дождитесь полной загрузки главной страницы Google")
            
            # Ждем успешного входа
            WebDriverWait(driver, 300).until(
                lambda d: "myaccount.google.com" in d.current_url or 
                         "accounts.google.com/b/0" in d.current_url or
                         "google.com" in d.current_url
            )
            
            # Переходим в Google Meet для проверки
            driver.get("https://meet.google.com/")
            time.sleep(3)
            
            print("✅ Google Meet авторизация завершена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации Google Meet: {e}")
            return False
    
    def auth_zoom(self, driver):
        """Авторизация в Zoom"""
        print("\n🟡 Авторизация в Zoom...")
        try:
            driver.get("https://zoom.us/signin")
            print("📝 Выполните вход в Zoom")
            print("   - Введите email и пароль")
            print("   - Пройдите двухфакторную аутентификацию если требуется")
            print("   - Дождитесь загрузки главной страницы Zoom")
            
            # Ждем успешного входа
            WebDriverWait(driver, 300).until(
                lambda d: "zoom.us/profile" in d.current_url or 
                         "zoom.us/meeting" in d.current_url or
                         "zoom.us/dashboard" in d.current_url
            )
            
            print("✅ Zoom авторизация завершена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации Zoom: {e}")
            return False
    
    def auth_yandex_telemost(self, driver):
        """Авторизация в Яндекс Телемост"""
        print("\n🟠 Авторизация в Яндекс Телемост...")
        try:
            driver.get("https://passport.yandex.ru/auth")
            print("📝 Выполните вход в Яндекс")
            print("   - Введите логин и пароль")
            print("   - Пройдите двухфакторную аутентификацию если требуется")
            print("   - Дождитесь загрузки главной страницы Яндекс")
            
            # Ждем успешного входа
            WebDriverWait(driver, 300).until(
                lambda d: "yandex.ru" in d.current_url and "passport.yandex.ru" not in d.current_url
            )
            
            # Переходим в Телемост для проверки
            driver.get("https://telemost.yandex.ru/")
            time.sleep(3)
            
            print("✅ Яндекс Телемост авторизация завершена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации Яндекс: {e}")
            return False
    
    def auth_contour_talk(self, driver):
        """Авторизация в Контур.Толк"""
        print("\n🟢 Авторизация в Контур.Толк...")
        try:
            driver.get("https://login.contour.ru/")
            print("📝 Выполните вход в Контур")
            print("   - Введите email и пароль")
            print("   - Пройдите двухфакторную аутентификацию если требуется")
            print("   - Дождитесь загрузки главной страницы Контур")
            
            # Ждем успешного входа
            WebDriverWait(driver, 300).until(
                lambda d: "contour.ru" in d.current_url and "login.contour.ru" not in d.current_url
            )
            
            # Переходим в Толк для проверки
            driver.get("https://talk.contour.ru/")
            time.sleep(3)
            
            print("✅ Контур.Толк авторизация завершена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации Контур: {e}")
            return False
    
    def auth_microsoft_teams(self, driver):
        """Авторизация в Microsoft Teams"""
        print("\n🔵 Авторизация в Microsoft Teams...")
        try:
            driver.get("https://teams.microsoft.com/")
            print("📝 Выполните вход в Microsoft Teams")
            print("   - Введите email и пароль")
            print("   - Пройдите двухфакторную аутентификацию если требуется")
            print("   - Дождитесь загрузки главной страницы Teams")
            
            # Ждем успешного входа
            WebDriverWait(driver, 300).until(
                lambda d: "teams.microsoft.com" in d.current_url and "login" not in d.current_url
            )
            
            print("✅ Microsoft Teams авторизация завершена")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка авторизации Teams: {e}")
            return False
    
    def run_authorization(self):
        """Запуск полной авторизации на всех платформах"""
        print("🚀 Запуск авторизации на всех платформах для Meeting Bot")
        print("=" * 60)
        print("⚠️ ВАЖНО: Браузер будет открыт и НЕ будет закрываться автоматически!")
        print("⚠️ Вы должны будете закрыть его вручную после завершения авторизации.")
        print("=" * 60)
        
        input("Нажмите Enter для продолжения...")
        
        driver = None
        try:
            # Настраиваем драйвер
            print("🔧 Настройка браузера...")
            driver = self.setup_selenium_driver()
            print("✅ Браузер запущен и готов к работе")
            
            # Авторизация на каждой платформе
            platforms = [
                ("Google Meet", self.auth_google_meet),
                ("Zoom", self.auth_zoom),
                ("Яндекс Телемост", self.auth_yandex_telemost),
                ("Контур.Толк", self.auth_contour_talk),
                ("Microsoft Teams", self.auth_microsoft_teams)
            ]
            
            success_count = 0
            for platform_name, auth_func in platforms:
                try:
                    if auth_func(driver):
                        success_count += 1
                        # Сохраняем cookies после каждой успешной авторизации
                        self.save_selenium_cookies(driver)
                        self.save_storage_data(driver)
                    else:
                        print(f"⚠️ Пропущена авторизация {platform_name}")
                except Exception as e:
                    print(f"❌ Критическая ошибка в {platform_name}: {e}")
                    continue
            
            print("\n" + "=" * 60)
            print(f"📊 Результат авторизации: {success_count}/{len(platforms)} платформ")
            
            if success_count > 0:
                print("\n✅ Авторизация завершена!")
                print(f"📁 Файлы сохранены:")
                print(f"   - {COOKIES_PATH} (Playwright cookies)")
                print(f"   - {SELENIUM_COOKIES_PATH} (Selenium cookies)")
                print(f"   - {STORAGE_PATH} (Storage данные)")
                print("\n📋 Инструкция для сервера:")
                print("1. Скопируйте все файлы на сервер")
                print("2. Убедитесь, что файлы находятся в рабочей директории бота")
                print("3. Бот будет автоматически использовать сохраненные данные")
            else:
                print("❌ Не удалось авторизоваться ни на одной платформе")
                
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
        finally:
            print("\n" + "=" * 60)
            print("🔧 Авторизация завершена!")
            print("⚠️ Браузер остается открытым для проверки.")
            print("💡 Закройте браузер вручную когда закончите проверку.")
            print("=" * 60)
            
            # НЕ закрываем браузер автоматически
            # if driver:
            #     driver.quit()
    
    def test_authorization(self):
        """Тестирование сохраненных данных авторизации"""
        print("🧪 Тестирование сохраненных данных авторизации...")
        
        if not os.path.exists(SELENIUM_COOKIES_PATH):
            print("❌ Файл cookies не найден")
            return False
        
        driver = None
        try:
            driver = self.setup_selenium_driver()
            
            # Загружаем cookies
            with open(SELENIUM_COOKIES_PATH, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Тестируем на Google Meet
            driver.get("https://meet.google.com/")
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass
            
            driver.refresh()
            time.sleep(5)
            
            # Проверяем, авторизованы ли мы
            if "accounts.google.com" not in driver.current_url:
                print("✅ Google Meet: авторизация работает")
            else:
                print("❌ Google Meet: требуется повторная авторизация")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False
        finally:
            if driver:
                driver.quit()

def main():
    """Главная функция"""
    auth = PlatformAuth()
    
    print("Выберите действие:")
    print("1. Полная авторизация на всех платформах")
    print("2. Тестирование сохраненных данных")
    print("3. Выход")
    
    choice = input("\nВведите номер (1-3): ").strip()
    
    if choice == "1":
        auth.run_authorization()
    elif choice == "2":
        auth.test_authorization()
    elif choice == "3":
        print("👋 До свидания!")
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
