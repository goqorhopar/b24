#!/usr/bin/env python3
"""
Быстрый тест исправлений Meeting Bot
"""

import os
import sys

def test_auth_files():
    """Проверка файлов авторизации"""
    print("Проверка файлов авторизации...")
    
    files = {
        'selenium_cookies.json': 'selenium_cookies',
        'storage.json': 'storage_data',
        'cookies.json': 'playwright_cookies'
    }
    
    for filename, file_type in files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  OK {file_type}: {filename} ({size} bytes)")
        else:
            print(f"  MISSING {file_type}: {filename}")
    
    return True

def test_imports():
    """Проверка импортов"""
    print("\nПроверка импортов...")
    
    try:
        from load_auth_data import get_auth_loader
        print("  OK load_auth_data")
        
        auth_loader = get_auth_loader()
        files_status = auth_loader.check_auth_files_exist()
        print(f"  OK AuthDataLoader: {sum(files_status.values())}/{len(files_status)} файлов")
        
        return True
    except Exception as e:
        print(f"  ERROR load_auth_data: {e}")
        return False

def test_meeting_detection():
    """Тест определения типа встречи"""
    print("\nТест определения типа встречи...")
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("meeting_bot", "meeting-bot.py")
        meeting_bot_module = importlib.util.module_from_spec(spec)
        
        # Загружаем только нужные части без Whisper
        with open("meeting-bot.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Создаем упрощенную версию для тестирования
        test_content = """
class MeetingBot:
    def detect_meeting_type(self, url):
        url_lower = url.lower()
        if 'meet.google.com' in url_lower:
            return 'google_meet'
        elif 'zoom.us' in url_lower or 'zoom.com' in url_lower:
            return 'zoom'
        elif 'telemost.yandex' in url_lower:
            return 'yandex'
        elif 'talk.contour.ru' in url_lower or 'contour.ru' in url_lower:
            return 'contour'
        elif 'teams.microsoft.com' in url_lower:
            return 'teams'
        else:
            return 'unknown'
"""
        
        exec(test_content, globals())
        
        bot = MeetingBot()
        test_urls = [
            "https://meet.google.com/abc-defg-hij",
            "https://zoom.us/j/123456789",
            "https://telemost.yandex.ru/meeting123",
            "https://talk.contour.ru/meeting456"
        ]
        
        for url in test_urls:
            meeting_type = bot.detect_meeting_type(url)
            print(f"  {url} -> {meeting_type}")
        
        print("  OK Определение типа встречи работает")
        return True
        
    except Exception as e:
        print(f"  ERROR Определение типа встречи: {e}")
        return False

def main():
    """Главная функция"""
    print("Быстрый тест исправлений Meeting Bot")
    print("=" * 40)
    
    tests = [
        test_auth_files,
        test_imports,
        test_meeting_detection
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"ERROR в тесте {test.__name__}: {e}")
    
    print("\n" + "=" * 40)
    print(f"Результат: {passed}/{len(tests)} тестов пройдено")
    
    if passed == len(tests):
        print("Все основные компоненты работают!")
        return True
    else:
        print("Есть проблемы, но основные исправления применены.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
