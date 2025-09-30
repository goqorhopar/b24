#!/usr/bin/env python3
"""
Простой тест авторизации без эмодзи
"""

import os
from load_auth_data import get_auth_loader

def test_auth():
    """Простой тест авторизации"""
    print("Тестирование авторизации Meeting Bot")
    print("=" * 40)
    
    auth_loader = get_auth_loader()
    
    # Проверяем файлы
    files_status = auth_loader.check_auth_files_exist()
    print("\nФайлы авторизации:")
    for file_type, exists in files_status.items():
        status = "OK" if exists else "НЕТ"
        print(f"   {file_type}: {status}")
    
    # Проверяем статус
    auth_status = auth_loader.get_auth_status()
    print(f"\nСтатус авторизации: {auth_status}")
    
    # Проверяем загрузку cookies
    selenium_cookies = auth_loader.load_selenium_cookies()
    if selenium_cookies:
        print(f"Cookies загружены: {len(selenium_cookies)} записей")
    else:
        print("Cookies не загружены")
    
    # Проверяем storage
    storage_data = auth_loader.load_storage_data()
    if storage_data:
        print("Storage данные загружены")
    else:
        print("Storage данные не загружены")
    
    print("\n" + "=" * 40)
    if all(files_status.values()):
        print("РЕЗУЛЬТАТ: Авторизация настроена корректно!")
        print("Бот сможет автоматически входить на все платформы.")
    else:
        print("РЕЗУЛЬТАТ: Авторизация не настроена.")
        print("Запустите: python simple_auth.py")
    
    return all(files_status.values())

if __name__ == "__main__":
    test_auth()
