#!/usr/bin/env python3
"""
Тест бота с ручной загрузкой переменных окружения
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Ручная загрузка переменных окружения
def load_env_manually():
    """Загрузка переменных окружения вручную"""
    env_vars = {
        'TELEGRAM_BOT_TOKEN': '7992998044:AAHUNEIBP9nqIC7fmpHqBKAPcoQM5ltrWuI',
        'GEMINI_API_KEY': 'AIzaSyDQR42zm4pcRMkY9KzKvEmXm7hyR8UzxHI',
        'GEMINI_MODEL': 'gemini-1.5-pro',
        'GEMINI_TEMPERATURE': '0.1',
        'GEMINI_TOP_P': '0.2',
        'GEMINI_MAX_TOKENS': '1200',
        'BITRIX_WEBHOOK_URL': 'https://skill-to-lead.bitrix24.ru/rest/1403/cmf3ncejqif8ny31',
        'BITRIX_RESPONSIBLE_ID': '1',
        'BITRIX_CREATED_BY_ID': '1',
        'BITRIX_TASK_DEADLINE_DAYS': '3',
        'PORT': '3000',
        'DB_PATH': 'bot_state.db',
        'LOG_LEVEL': 'INFO',
        'NODE_ENV': 'production',
        'MAX_RETRIES': '3',
        'RETRY_DELAY': '2',
        'REQUEST_TIMEOUT': '30',
        'MAX_COMMENT_LENGTH': '8000',
        'ADMIN_CHAT_ID': '7537953397',
        'MEETING_DISPLAY_NAME': 'Ассистент Григория Сергеевича',
        'MEETING_HEADLESS': 'true',
        'MEETING_AUTO_LEAVE': 'true',
        'MEETING_DURATION_MINUTES': '60'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
    
    print("✅ Переменные окружения загружены вручную")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_environment():
    """Тест переменных окружения"""
    print("🔧 Тестирование переменных окружения...")
    
    # Проверяем основные переменные
    env_vars = {
        'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'BITRIX_WEBHOOK_URL': os.getenv('BITRIX_WEBHOOK_URL'),
        'ADMIN_CHAT_ID': os.getenv('ADMIN_CHAT_ID'),
        'GEMINI_MODEL': os.getenv('GEMINI_MODEL', 'gemini-1.5-pro'),
        'NODE_ENV': os.getenv('NODE_ENV', 'production')
    }
    
    for var, value in env_vars.items():
        if value:
            # Скрываем чувствительные данные
            if 'TOKEN' in var or 'KEY' in var:
                display_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: не установлена")
    
    return all(env_vars.values())

def test_telegram_connection():
    """Тест подключения к Telegram"""
    print("\n📱 Тестирование подключения к Telegram...")
    
    try:
        import requests
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN не установлен")
            return False
        
        # Проверяем информацию о боте
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_data = bot_info['result']
                print(f"✅ Бот подключен: @{bot_data.get('username', 'N/A')}")
                print(f"   Имя: {bot_data.get('first_name', 'N/A')}")
                print(f"   ID: {bot_data.get('id', 'N/A')}")
                return True
            else:
                print(f"❌ Ошибка API: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        return False

def test_gemini_connection():
    """Тест подключения к Gemini"""
    print("\n🧠 Тестирование подключения к Gemini...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY не установлен")
            return False
        
        # Настройка Gemini
        genai.configure(api_key=api_key)
        
        # Тест простого запроса
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Привет! Это тест подключения.")
        
        if response.text:
            print("✅ Gemini подключен и отвечает")
            print(f"   Ответ: {response.text[:50]}...")
            return True
        else:
            print("❌ Gemini не отвечает")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Gemini: {e}")
        return False

def test_bitrix_connection():
    """Тест подключения к Bitrix24"""
    print("\n🏢 Тестирование подключения к Bitrix24...")
    
    try:
        import requests
        
        webhook_url = os.getenv('BITRIX_WEBHOOK_URL')
        if not webhook_url:
            print("❌ BITRIX_WEBHOOK_URL не установлен")
            return False
        
        # Тест простого запроса к Bitrix24
        test_url = f"{webhook_url}/crm.lead.get"
        params = {'id': '1'}  # Тестовый ID
        
        response = requests.get(test_url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                print("✅ Bitrix24 подключен")
                return True
            elif 'error' in data:
                error = data['error']
                if error.get('error_description') == 'Not found':
                    print("✅ Bitrix24 подключен (тестовый лид не найден - это нормально)")
                    return True
                else:
                    print(f"❌ Ошибка Bitrix24: {error.get('error_description', 'Unknown error')}")
                    return False
            else:
                print("❌ Неожиданный ответ от Bitrix24")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Bitrix24: {e}")
        return False

def test_components():
    """Тест компонентов бота"""
    print("\n🧪 Тестирование компонентов бота...")
    
    try:
        # Тест импорта основных модулей
        from meeting_link_processor import MeetingLinkProcessor
        from speech_transcriber import SpeechTranscriber
        from meeting_analyzer import MeetingAnalyzer
        from aggressive_meeting_automation import AggressiveMeetingAutomation
        
        print("✅ Все модули импортированы успешно")
        
        # Тест инициализации компонентов
        processor = MeetingLinkProcessor()
        print("✅ MeetingLinkProcessor инициализирован")
        
        transcriber = SpeechTranscriber()
        print("✅ SpeechTranscriber инициализирован")
        
        analyzer = MeetingAnalyzer()
        print("✅ MeetingAnalyzer инициализирован")
        
        automation = AggressiveMeetingAutomation()
        print("✅ AggressiveMeetingAutomation инициализирован")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации компонентов: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 Тестирование бота с реальными настройками")
    print("=" * 60)
    print(f"⏰ Время тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Загружаем переменные окружения
    load_env_manually()
    
    tests = [
        ("Переменные окружения", test_environment),
        ("Подключение к Telegram", test_telegram_connection),
        ("Подключение к Gemini", test_gemini_connection),
        ("Подключение к Bitrix24", test_bitrix_connection),
        ("Компоненты бота", test_components)
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
    
    print("\n" + "=" * 60)
    print(f"🏁 Результаты: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("🎉 Все тесты пройдены! Бот готов к запуску на сервере.")
        print("\n🚀 Для запуска используйте:")
        print("   python start_server.py")
        print("   или")
        print("   python main.py")
    else:
        print("⚠️ Некоторые тесты провалены. Проверьте настройки.")
        
        if passed >= 3:  # Если основные тесты пройдены
            print("\n💡 Основные компоненты работают. Можно попробовать запустить бота:")
            print("   python main.py")

if __name__ == "__main__":
    main()
