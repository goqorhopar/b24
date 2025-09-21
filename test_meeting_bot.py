#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы бота встреч
"""

import os
import sys
import logging
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from meeting_link_processor import MeetingLinkProcessor
from speech_transcriber import SpeechTranscriber
from meeting_analyzer import MeetingAnalyzer
from aggressive_meeting_automation import AggressiveMeetingAutomation

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_meeting_processor():
    """Тест основного процессора встреч"""
    print("🧪 Тестирование MeetingLinkProcessor...")
    
    try:
        # Создание процессора (компоненты инициализируются внутри)
        processor = MeetingLinkProcessor()
        
        print("✅ MeetingLinkProcessor инициализирован успешно")
        
        # Тест обработки ссылки на встречу
        test_url = "https://zoom.us/j/123456789"
        chat_id = 12345
        initiator_name = "Test User"
        
        print(f"🔗 Тестирование обработки ссылки: {test_url}")
        result = processor.process_meeting_link(test_url, chat_id, initiator_name)
        
        if result.get('success'):
            print("✅ Обработка ссылки прошла успешно")
            print(f"📊 Результат: {result.get('message')}")
        else:
            print(f"❌ Ошибка обработки: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def test_speech_transcriber():
    """Тест транскрипции речи"""
    print("\n🧪 Тестирование SpeechTranscriber...")
    
    try:
        transcriber = SpeechTranscriber()
        print("✅ SpeechTranscriber инициализирован успешно")
        
        # Проверяем доступность модели
        if transcriber.model is not None:
            print("✅ Модель Whisper загружена")
        else:
            print("⚠️ Модель Whisper не загружена")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании транскрипции: {e}")

def test_meeting_analyzer():
    """Тест анализатора встреч"""
    print("\n🧪 Тестирование MeetingAnalyzer...")
    
    try:
        analyzer = MeetingAnalyzer()
        print("✅ MeetingAnalyzer инициализирован успешно")
        
        # Тест анализа с чек-листом
        test_transcript = """
        Добро пожаловать на нашу встречу. Сегодня мы обсудим новый проект.
        Бюджет составляет 100000 рублей. Срок реализации - 3 месяца.
        Клиент заинтересован в наших услугах.
        """
        
        print("📝 Тестирование анализа с чек-листом...")
        result = analyzer.analyze_meeting_with_checklist(
            test_transcript, 
            checklist_type='sales_meeting'
        )
        
        if result:
            score = result.get('score', 0)
            print(f"✅ Анализ завершен. Оценка: {score}/100")
        else:
            print("❌ Анализ не выполнен")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании анализа: {e}")

def test_meeting_automation():
    """Тест автоматизации встреч"""
    print("\n🧪 Тестирование AggressiveMeetingAutomation...")
    
    try:
        automation = AggressiveMeetingAutomation()
        print("✅ AggressiveMeetingAutomation инициализирован успешно")
        
        # Проверяем доступность WebDriver
        try:
            automation.setup_chrome_driver()
            print("✅ Chrome WebDriver настроен")
        except Exception as e:
            print(f"⚠️ Ошибка настройки WebDriver: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании автоматизации: {e}")

def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования бота встреч")
    print("=" * 50)
    
    # Проверяем переменные окружения
    print("🔧 Проверка переменных окружения...")
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'GEMINI_API_KEY',
        'BITRIX_WEBHOOK_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Отсутствуют переменные окружения: {', '.join(missing_vars)}")
        print("Создайте файл .env на основе .env.example")
    else:
        print("✅ Все необходимые переменные окружения настроены")
    
    # Запуск тестов
    test_speech_transcriber()
    test_meeting_analyzer()
    test_meeting_automation()
    test_meeting_processor()
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    main()
