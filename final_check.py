#!/usr/bin/env python3
"""
Финальная проверка всех компонентов бота
"""

import os
import sys
import importlib
from dotenv import load_dotenv

def check_imports():
    """Проверяем импорты всех модулей"""
    print("🔍 Проверяем импорты модулей...")
    
    modules = [
        'main',
        'config', 
        'bitrix',
        'gemini_client',
        'speech_transcriber',
        'meeting_analyzer',
        'platform_detector',
        'meeting_link_processor',
        'aggressive_meeting_automation',
        'db'
    ]
    
    failed_imports = []
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed_imports.append(module)
    
    return len(failed_imports) == 0

def check_env():
    """Проверяем переменные окружения"""
    print("\n🔧 Проверяем переменные окружения...")
    
    load_dotenv()
    
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GEMINI_API_KEY', 
        'BITRIX_WEBHOOK_URL',
        'ADMIN_CHAT_ID'
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value[:10]}...")
        else:
            print(f"  ❌ {var}: НЕ НАЙДЕН")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def check_files():
    """Проверяем наличие ключевых файлов"""
    print("\n📁 Проверяем ключевые файлы...")
    
    required_files = [
        'main.py',
        'start_bot_fixed.py',
        'config.py',
        'bitrix.py',
        'gemini_client.py',
        'speech_transcriber.py',
        'meeting_analyzer.py',
        'platform_detector.py',
        'meeting_link_processor.py',
        'aggressive_meeting_automation.py',
        'requirements.txt',
        '.env'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file}: НЕ НАЙДЕН")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_platform():
    """Проверяем платформу"""
    print("\n💻 Проверяем платформу...")
    
    if sys.platform == "linux":
        print("  ✅ Linux - бот будет работать корректно")
        return True
    else:
        print(f"  ⚠️  {sys.platform} - бот должен работать на Linux сервере")
        return False

def main():
    """Основная функция проверки"""
    print("🤖 ФИНАЛЬНАЯ ПРОВЕРКА БОТА")
    print("=" * 50)
    
    checks = [
        ("Импорты модулей", check_imports),
        ("Переменные окружения", check_env),
        ("Ключевые файлы", check_files),
        ("Платформа", check_platform)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  ❌ Ошибка проверки {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("✅ Бот готов к работе на сервере")
        print("\n📋 Следующие шаги:")
        print("1. Загрузите файлы на Linux сервер")
        print("2. Запустите: ./quick_start_server.sh")
        print("3. Протестируйте в Telegram: @TranscriptionleadBot")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ!")
        print("🔧 Исправьте ошибки перед запуском на сервере")
    
    return all_passed

if __name__ == "__main__":
    main()
