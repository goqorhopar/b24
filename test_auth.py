#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы авторизации
"""

import os
import sys
from load_auth_data import get_auth_loader

def test_auth_files():
    """Тест наличия файлов авторизации"""
    print("🧪 Тестирование файлов авторизации...")
    
    auth_loader = get_auth_loader()
    files_status = auth_loader.check_auth_files_exist()
    
    print("\n📁 Статус файлов:")
    for file_type, exists in files_status.items():
        status = "✅" if exists else "❌"
        print(f"   {status} {file_type}")
    
    auth_status = auth_loader.get_auth_status()
    print(f"\n📊 Общий статус: {auth_status}")
    
    return all(files_status.values())

def test_cookies_loading():
    """Тест загрузки cookies"""
    print("\n🍪 Тестирование загрузки cookies...")
    
    auth_loader = get_auth_loader()
    
    # Тест Playwright cookies
    playwright_cookies = auth_loader.load_playwright_cookies()
    if playwright_cookies:
        print(f"   ✅ Playwright cookies: {len(playwright_cookies)} записей")
    else:
        print("   ❌ Playwright cookies не загружены")
    
    # Тест Selenium cookies
    selenium_cookies = auth_loader.load_selenium_cookies()
    if selenium_cookies:
        print(f"   ✅ Selenium cookies: {len(selenium_cookies)} записей")
    else:
        print("   ❌ Selenium cookies не загружены")
    
    # Тест storage данных
    storage_data = auth_loader.load_storage_data()
    if storage_data:
        print("   ✅ Storage данные загружены")
        if 'sessionStorage' in storage_data:
            print(f"      - sessionStorage: {len(storage_data['sessionStorage'])} записей")
        if 'localStorage' in storage_data:
            print(f"      - localStorage: {len(storage_data['localStorage'])} записей")
    else:
        print("   ❌ Storage данные не загружены")
    
    return bool(playwright_cookies or selenium_cookies or storage_data)

def test_selenium_integration():
    """Тест интеграции с Selenium"""
    print("\n🌐 Тестирование интеграции с Selenium...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        # Настройка драйвера
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        
        # Тест применения авторизации
        auth_loader = get_auth_loader()
        success = auth_loader.setup_authenticated_driver(driver)
        
        if success:
            print("   ✅ Авторизация успешно применена к Selenium драйверу")
        else:
            print("   ⚠️ Авторизация не применена (возможно, файлы отсутствуют)")
        
        driver.quit()
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка тестирования Selenium: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("Запуск тестирования авторизации Meeting Bot")
    print("=" * 50)
    
    tests = [
        ("Файлы авторизации", test_auth_files),
        ("Загрузка данных", test_cookies_loading),
        ("Интеграция Selenium", test_selenium_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Результаты тестирования:")
    
    passed = 0
    for test_name, result in results:
        status = "ПРОЙДЕН" if result else "ПРОВАЛЕН"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nИтого: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        print("Все тесты пройдены! Авторизация настроена корректно.")
        return 0
    else:
        print("Некоторые тесты провалены. Проверьте настройку авторизации.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
