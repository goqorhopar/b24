#!/usr/bin/env python3
"""
Быстрый скрипт авторизации - упрощенная версия
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def quick_auth():
    """Быстрая авторизация на основных платформах"""
    print("🚀 Быстрая авторизация Meeting Bot")
    print("=" * 40)
    print("⚠️ ВАЖНО: Браузер НЕ будет закрываться автоматически!")
    print("=" * 40)
    
    input("Нажмите Enter для запуска браузера...")
    
    # Настройка драйвера
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # КРИТИЧНО: Не закрывать браузер автоматически
    options.add_experimental_option("detach", True)
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Браузер запущен!")
        
        platforms = [
            {
                "name": "Google Meet",
                "url": "https://accounts.google.com/signin",
                "success_url": "myaccount.google.com"
            },
            {
                "name": "Zoom", 
                "url": "https://zoom.us/signin",
                "success_url": "zoom.us/profile"
            },
            {
                "name": "Яндекс Телемост",
                "url": "https://passport.yandex.ru/auth", 
                "success_url": "yandex.ru"
            },
            {
                "name": "Контур.Толк",
                "url": "https://login.contour.ru/",
                "success_url": "contour.ru"
            }
        ]
        
        for i, platform in enumerate(platforms, 1):
            print(f"\n{i}. 🔐 Авторизация в {platform['name']}")
            print(f"   URL: {platform['url']}")
            
            try:
                driver.get(platform['url'])
                print("   📝 Выполните вход в аккаунт...")
                print("   ⏳ Ожидание авторизации...")
                
                # Ждем успешного входа (до 5 минут)
                WebDriverWait(driver, 300).until(
                    lambda d: platform['success_url'] in d.current_url
                )
                
                print(f"   ✅ {platform['name']} - авторизация успешна")
                
                # Сохраняем cookies после каждой платформы
                save_cookies(driver, f"cookies_{platform['name'].lower().replace(' ', '_')}.json")
                
            except Exception as e:
                print(f"   ❌ {platform['name']} - ошибка: {e}")
                continue
        
        # Финальное сохранение
        save_cookies(driver, "selenium_cookies.json")
        save_storage(driver, "storage.json")
        
        print("\n" + "=" * 40)
        print("✅ Авторизация завершена!")
        print("📁 Файлы сохранены:")
        print("   - selenium_cookies.json")
        print("   - storage.json")
        print("\n🚀 Теперь бот может автоматически входить на встречи!")
        print("\n⚠️ Браузер остается открытым для проверки!")
        print("💡 Закройте его вручную когда закончите проверку.")
        
        # Ждем подтверждения пользователя
        input("\nНажмите Enter когда закончите проверку...")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        print("\n👋 Скрипт завершен. Браузер остается открытым.")
        # НЕ закрываем браузер автоматически
        # if driver:
        #     driver.quit()

def save_cookies(driver, filename):
    """Сохранить cookies"""
    try:
        import json
        cookies = driver.get_cookies()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        print(f"   💾 Cookies сохранены: {filename}")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения cookies: {e}")

def save_storage(driver, filename):
    """Сохранить storage данные"""
    try:
        import json
        session_storage = driver.execute_script("return window.sessionStorage;")
        local_storage = driver.execute_script("return window.localStorage;")
        
        storage_data = {
            "sessionStorage": session_storage,
            "localStorage": local_storage,
            "timestamp": time.time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, indent=2, ensure_ascii=False)
        print(f"   💾 Storage сохранен: {filename}")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения storage: {e}")

if __name__ == "__main__":
    quick_auth()
