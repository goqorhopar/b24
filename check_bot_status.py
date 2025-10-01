#!/usr/bin/env python3
"""
Проверка статуса Meeting Bot
"""

import os
import sys
from datetime import datetime

def check_environment():
    """Проверка переменных окружения"""
    print("Проверка переменных окружения...")
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID',
        'ADMIN_CHAT_ID'
    ]
    
    optional_vars = [
        'GITHUB_TOKEN',
        'GITHUB_REPO',
        'WHISPER_MODEL',
        'RECORD_DIR'
    ]
    
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  OK {var}: настроен")
        else:
            print(f"  ERROR {var}: НЕ НАСТРОЕН (обязательно!)")
            all_ok = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  OK {var}: {value}")
        else:
            print(f"  WARNING {var}: не настроен (опционально)")
    
    return all_ok

def check_auth_files():
    """Проверка файлов авторизации"""
    print("\nПроверка файлов авторизации...")
    
    files = {
        'selenium_cookies.json': 'Selenium cookies',
        'storage.json': 'Storage данные',
        'cookies.json': 'Playwright cookies'
    }
    
    found_files = 0
    total_files = len(files)
    
    for filename, description in files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  OK {description}: {filename} ({size} bytes)")
            found_files += 1
        else:
            print(f"  ERROR {description}: {filename} - НЕ НАЙДЕН")
    
    if found_files == 0:
        print("  WARNING ВНИМАНИЕ: Нет файлов авторизации!")
        print("     Запустите: python simple_auth.py")
        return False
    elif found_files < total_files:
        print(f"  WARNING Частичная авторизация: {found_files}/{total_files} файлов")
        return True
    else:
        print("  OK Полная авторизация настроена")
        return True

def check_dependencies():
    """Проверка зависимостей"""
    print("\nПроверка зависимостей...")
    
    dependencies = [
        'selenium',
        'telegram',
        'faster_whisper',
        'playwright',
        'requests',
        'python-dotenv'
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  OK {dep}")
        except ImportError:
            print(f"  ERROR {dep} - НЕ УСТАНОВЛЕН")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"\n  WARNING Установите недостающие зависимости:")
        print(f"     pip install {' '.join(missing_deps)}")
        return False
    
    return True

def check_system_tools():
    """Проверка системных инструментов"""
    print("\nПроверка системных инструментов...")
    
    import subprocess
    
    tools = {
        'ffmpeg': ['ffmpeg', '-version'],
        'chrome': ['google-chrome', '--version'],
        'chromium': ['chromium', '--version']
    }
    
    found_tools = []
    
    for tool_name, cmd in tools.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  OK {tool_name}")
                found_tools.append(tool_name)
            else:
                print(f"  ERROR {tool_name} - не работает")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print(f"  ERROR {tool_name} - не найден")
    
    if 'ffmpeg' not in found_tools:
        print("  WARNING ffmpeg необходим для записи аудио!")
        return False
    
    if not any(tool in found_tools for tool in ['chrome', 'chromium']):
        print("  WARNING Chrome или Chromium необходим для работы бота!")
        return False
    
    return True

def check_bot_files():
    """Проверка файлов бота"""
    print("\nПроверка файлов бота...")
    
    required_files = [
        'meeting-bot.py',
        'meeting_bot_playwright.py',
        'load_auth_data.py',
        'requirements.txt'
    ]
    
    all_present = True
    
    for filename in required_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  OK {filename} ({size} bytes)")
        else:
            print(f"  ERROR {filename} - НЕ НАЙДЕН")
            all_present = False
    
    return all_present

def generate_status_report():
    """Генерация отчета о статусе"""
    print("\n" + "="*60)
    print("ОТЧЕТ О СТАТУСЕ MEETING BOT")
    print("="*60)
    print(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("Переменные окружения", check_environment),
        ("Файлы авторизации", check_auth_files),
        ("Зависимости Python", check_dependencies),
        ("Системные инструменты", check_system_tools),
        ("Файлы бота", check_bot_files)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ERROR Ошибка проверки {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n" + "="*60)
    print("ИТОГОВЫЙ СТАТУС:")
    print("="*60)
    
    all_passed = True
    for check_name, result in results:
        status = "OK ПРОЙДЕНО" if result else "ERROR ПРОВАЛЕНО"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("   Бот готов к работе!")
        print("\nДля запуска:")
        print("   python meeting-bot.py")
    else:
        print("ЕСТЬ ПРОБЛЕМЫ!")
        print("   Исправьте ошибки перед запуском бота.")
        print("\nРекомендации:")
        if not any(result for name, result in results if "авторизации" in name):
            print("   • Настройте авторизацию: python simple_auth.py")
        if not any(result for name, result in results if "окружения" in name):
            print("   • Настройте переменные окружения в .env файле")
        if not any(result for name, result in results if "зависимости" in name):
            print("   • Установите зависимости: pip install -r requirements.txt")
    
    return all_passed

def main():
    """Главная функция"""
    try:
        return generate_status_report()
    except KeyboardInterrupt:
        print("\n\nПроверка прервана пользователем")
        return False
    except Exception as e:
        print(f"\nERROR Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
