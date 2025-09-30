#!/usr/bin/env python3
"""
Скрипт установки и настройки авторизации для Meeting Bot
"""

import os
import sys
import subprocess
import json

def check_dependencies():
    """Проверить установленные зависимости"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        'selenium',
        'playwright', 
        'python-telegram-bot',
        'faster-whisper',
        'PyGithub',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Отсутствуют пакеты: {', '.join(missing_packages)}")
        return False
    else:
        print("\n✅ Все зависимости установлены")
        return True

def install_dependencies():
    """Установить зависимости"""
    print("📦 Установка зависимостей...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки: {e}")
        return False

def check_chrome():
    """Проверить наличие Chrome/Chromium"""
    print("🌐 Проверка браузера...")
    
    chrome_paths = [
        'google-chrome',
        'chromium',
        'chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium'
    ]
    
    for path in chrome_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"   ✅ Найден: {path}")
                return True
        except FileNotFoundError:
            continue
    
    print("   ❌ Chrome/Chromium не найден")
    print("   💡 Установите: sudo apt-get install google-chrome-stable")
    return False

def check_auth_files():
    """Проверить файлы авторизации"""
    print("📁 Проверка файлов авторизации...")
    
    auth_files = [
        'cookies.json',
        'selenium_cookies.json', 
        'storage.json'
    ]
    
    found_files = []
    for file in auth_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
            found_files.append(file)
        else:
            print(f"   ❌ {file}")
    
    if found_files:
        print(f"\n✅ Найдено файлов авторизации: {len(found_files)}/{len(auth_files)}")
        return True
    else:
        print("\n⚠️ Файлы авторизации не найдены")
        return False

def run_auth_setup():
    """Запустить настройку авторизации"""
    print("🔐 Запуск настройки авторизации...")
    
    try:
        subprocess.run([sys.executable, 'auth_platforms.py'])
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска авторизации: {e}")
        return False

def test_auth():
    """Тестировать авторизацию"""
    print("🧪 Тестирование авторизации...")
    
    try:
        result = subprocess.run([sys.executable, 'test_auth.py'], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Ошибки:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False

def main():
    """Главная функция установки"""
    print("🚀 Установка и настройка авторизации Meeting Bot")
    print("=" * 50)
    
    # Проверяем зависимости
    if not check_dependencies():
        print("\n📦 Устанавливаем зависимости...")
        if not install_dependencies():
            print("❌ Не удалось установить зависимости")
            return 1
    
    # Проверяем браузер
    if not check_chrome():
        print("\n⚠️ Установите Chrome/Chromium для продолжения")
        return 1
    
    # Проверяем файлы авторизации
    auth_files_exist = check_auth_files()
    
    if not auth_files_exist:
        print("\n🔐 Требуется настройка авторизации")
        choice = input("Запустить настройку авторизации? (y/n): ").lower().strip()
        
        if choice in ['y', 'yes', 'да', 'д']:
            if not run_auth_setup():
                print("❌ Ошибка настройки авторизации")
                return 1
        else:
            print("⚠️ Пропущена настройка авторизации")
    
    # Тестируем авторизацию
    print("\n🧪 Тестирование...")
    if test_auth():
        print("\n🎉 Установка завершена успешно!")
        print("\n📋 Следующие шаги:")
        print("1. Запустите бота: python meeting-bot.py")
        print("2. Отправьте ссылку на встречу")
        print("3. Бот автоматически использует сохраненную авторизацию")
    else:
        print("\n⚠️ Тестирование не пройдено")
        print("Проверьте настройку авторизации")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
