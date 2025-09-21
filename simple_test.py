#!/usr/bin/env python3
"""
Простой тест компонентов бота без внешних зависимостей
"""

import os
import sys
import logging

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """Тест импорта всех модулей"""
    print("🧪 Тестирование импорта модулей...")
    
    try:
        # Тест импорта основных модулей
        print("📦 Импорт config...")
        from config import config
        print("✅ config импортирован")
        
        print("📦 Импорт platform_detector...")
        from platform_detector import MeetingPlatformDetector
        print("✅ platform_detector импортирован")
        
        print("📦 Импорт speech_transcriber...")
        from speech_transcriber import SpeechTranscriber
        print("✅ speech_transcriber импортирован")
        
        print("📦 Импорт aggressive_meeting_automation...")
        from aggressive_meeting_automation import AggressiveMeetingAutomation
        print("✅ aggressive_meeting_automation импортирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_platform_detector():
    """Тест детектора платформ"""
    print("\n🧪 Тестирование детектора платформ...")
    
    try:
        from platform_detector import MeetingPlatformDetector
        detector = MeetingPlatformDetector()
        
        # Тестовые URL
        test_urls = [
            "https://zoom.us/j/123456789",
            "https://meet.google.com/abc-defg-hij",
            "https://teams.microsoft.com/l/meetup-join/...",
            "https://kontur-talk.ru/meeting/123"
        ]
        
        for url in test_urls:
            platform = detector.detect_platform_from_url(url)
            if platform:
                print(f"✅ {url} -> {platform['platform_name']}")
            else:
                print(f"❌ {url} -> не определен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка детектора платформ: {e}")
        return False

def test_speech_transcriber():
    """Тест транскрипции (без загрузки модели)"""
    print("\n🧪 Тестирование транскрипции...")
    
    try:
        from speech_transcriber import SpeechTranscriber
        transcriber = SpeechTranscriber()
        
        print("✅ SpeechTranscriber инициализирован")
        print("ℹ️ Модель Whisper не загружена (требует GEMINI_API_KEY)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка транскрипции: {e}")
        return False

def test_meeting_automation():
    """Тест автоматизации встреч"""
    print("\n🧪 Тестирование автоматизации встреч...")
    
    try:
        from aggressive_meeting_automation import AggressiveMeetingAutomation
        automation = AggressiveMeetingAutomation()
        
        print("✅ AggressiveMeetingAutomation инициализирован")
        
        # Тест определения платформы
        test_url = "https://zoom.us/j/123456789"
        platform = automation._detect_platform_from_url(test_url)
        print(f"✅ Платформа определена: {platform}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка автоматизации: {e}")
        return False

def test_file_structure():
    """Тест структуры файлов"""
    print("\n🧪 Тестирование структуры файлов...")
    
    required_files = [
        "main.py",
        "config.py",
        "meeting_link_processor.py",
        "aggressive_meeting_automation.py",
        "speech_transcriber.py",
        "meeting_analyzer.py",
        "gemini_client.py",
        "bitrix.py",
        "bitrix_meeting_integration.py",
        "platform_detector.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - отсутствует")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    else:
        print("\n✅ Все необходимые файлы присутствуют")
        return True

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск простого тестирования бота встреч")
    print("=" * 50)
    
    tests = [
        ("Структура файлов", test_file_structure),
        ("Импорт модулей", test_imports),
        ("Детектор платформ", test_platform_detector),
        ("Транскрипция", test_speech_transcriber),
        ("Автоматизация встреч", test_meeting_automation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - ПРОЙДЕН")
            else:
                print(f"❌ {test_name} - ПРОВАЛЕН")
        except Exception as e:
            print(f"❌ {test_name} - ОШИБКА: {e}")
    
    print("\n" + "=" * 50)
    print(f"🏁 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к настройке.")
        print("\n📋 Следующие шаги:")
        print("1. Создайте файл .env с переменными окружения")
        print("2. Установите зависимости: pip install -r requirements.txt")
        print("3. Запустите бота: python main.py")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте ошибки выше.")

if __name__ == "__main__":
    main()
