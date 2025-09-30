#!/usr/bin/env python3
"""
Простой скрипт авторизации - браузер НЕ закрывается автоматически
"""

import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Настройка драйвера с максимальной стабильностью"""
    options = Options()
    
    # Базовые настройки
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # КРИТИЧНО: Не закрывать браузер автоматически
    options.add_experimental_option("detach", True)
    
    # Настройки для стабильности
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-first-run')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--disable-default-apps')
    
    # User agent
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Увеличиваем таймауты
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(60)
    
    return driver

def save_cookies(driver, filename):
    """Сохранить cookies"""
    try:
        cookies = driver.get_cookies()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print(f"✅ Cookies сохранены: {filename}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения cookies: {e}")
        return False

def save_storage(driver, filename):
    """Сохранить storage данные"""
    try:
        session_storage = driver.execute_script("return window.sessionStorage;")
        local_storage = driver.execute_script("return window.localStorage;")
        
        storage_data = {
            "sessionStorage": session_storage,
            "localStorage": local_storage,
            "timestamp": time.time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Storage сохранен: {filename}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения storage: {e}")
        return False

def auth_platform(driver, name, url, success_indicators):
    """Авторизация на одной платформе"""
    print(f"\n🔐 Авторизация в {name}...")
    print(f"   URL: {url}")
    
    try:
        driver.get(url)
        print(f"   📝 Выполните вход в {name}")
        print(f"   ⏳ Ожидание авторизации...")
        print(f"   💡 После входа нажмите Enter в консоли")
        
        # Ждем ввода пользователя
        input(f"   ✅ Нажмите Enter когда авторизация в {name} завершена...")
        
        # Сохраняем данные
        save_cookies(driver, f"cookies_{name.lower().replace(' ', '_')}.json")
        save_storage(driver, f"storage_{name.lower().replace(' ', '_')}.json")
        
        print(f"   ✅ {name} - авторизация завершена")
        return True
        
    except Exception as e:
        print(f"   ❌ {name} - ошибка: {e}")
        return False

def main():
    """Главная функция"""
    print("🚀 Простая авторизация Meeting Bot")
    print("=" * 50)
    print("⚠️ ВАЖНО: Браузер НЕ будет закрываться автоматически!")
    print("⚠️ Вы должны будете закрыть его вручную в конце.")
    print("=" * 50)
    
    input("Нажмите Enter для запуска браузера...")
    
    driver = None
    try:
        # Запускаем браузер
        print("🔧 Запуск браузера...")
        driver = setup_driver()
        print("✅ Браузер запущен!")
        
        # Платформы для авторизации
        platforms = [
            {
                "name": "Google Meet",
                "url": "https://accounts.google.com/signin",
                "success_indicators": ["myaccount.google.com", "google.com"]
            },
            {
                "name": "Zoom",
                "url": "https://zoom.us/signin", 
                "success_indicators": ["zoom.us/profile", "zoom.us/dashboard"]
            },
            {
                "name": "Яндекс Телемост",
                "url": "https://passport.yandex.ru/auth",
                "success_indicators": ["yandex.ru"]
            },
            {
                "name": "Контур.Толк",
                "url": "https://login.contour.ru/",
                "success_indicators": ["contour.ru"]
            },
            {
                "name": "Microsoft Teams",
                "url": "https://teams.microsoft.com/",
                "success_indicators": ["teams.microsoft.com"]
            }
        ]
        
        success_count = 0
        
        # Авторизация на каждой платформе
        for platform in platforms:
            if auth_platform(driver, platform["name"], platform["url"], platform["success_indicators"]):
                success_count += 1
        
        # Финальное сохранение
        print("\n💾 Сохранение финальных данных...")
        save_cookies(driver, "selenium_cookies.json")
        save_storage(driver, "storage.json")
        
        print("\n" + "=" * 50)
        print(f"🎉 Авторизация завершена!")
        print(f"📊 Успешно: {success_count}/{len(platforms)} платформ")
        print("📁 Файлы сохранены:")
        print("   - selenium_cookies.json")
        print("   - storage.json")
        print("\n⚠️ Браузер остается открытым!")
        print("💡 Закройте его вручную когда закончите проверку.")
        print("=" * 50)
        
        # НЕ закрываем браузер - оставляем открытым
        print("\n🔧 Браузер остается открытым для проверки авторизации.")
        print("💡 Проверьте, что вы авторизованы на всех нужных платформах.")
        print("💡 Закройте браузер вручную когда закончите.")
        
        # Ждем подтверждения пользователя
        input("\nНажмите Enter когда закончите проверку...")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        print("\n👋 Скрипт завершен. Браузер остается открытым.")
        # НЕ закрываем браузер автоматически
        # if driver:
        #     driver.quit()

if __name__ == "__main__":
    main()
