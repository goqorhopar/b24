"""
Тестовый скрипт для проверки работоспособности серверного бота
"""
import os
import sys
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def test_imports():
    """Тест импорта всех модулей"""
    log.info("🔍 Тестирование импорта модулей...")
    
    try:
        from server_config import config
        log.info("✅ server_config импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта server_config: {e}")
        return False
    
    try:
        from server_meeting_bot import server_bot
        log.info("✅ server_meeting_bot импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта server_meeting_bot: {e}")
        return False
    
    try:
        from gemini_client import analyze_transcript_structured
        log.info("✅ gemini_client импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта gemini_client: {e}")
        return False
    
    try:
        from bitrix import update_lead_comprehensive
        log.info("✅ bitrix импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта bitrix: {e}")
        return False
    
    try:
        from speech_transcriber import SpeechTranscriber
        log.info("✅ speech_transcriber импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта speech_transcriber: {e}")
        return False
    
    try:
        from audio_capture import MeetingAudioRecorder
        log.info("✅ audio_capture импортирован")
    except Exception as e:
        log.error(f"❌ Ошибка импорта audio_capture: {e}")
        return False
    
    return True

def test_config():
    """Тест конфигурации"""
    log.info("🔧 Тестирование конфигурации...")
    
    try:
        from server_config import config
        
        # Проверка основных настроек
        log.info(f"MEETING_DISPLAY_NAME: {config.MEETING_DISPLAY_NAME}")
        log.info(f"MEETING_HEADLESS: {config.MEETING_HEADLESS}")
        log.info(f"WHISPER_MODEL: {config.WHISPER_MODEL}")
        log.info(f"GEMINI_MODEL: {config.GEMINI_MODEL}")
        
        # Валидация
        validation = config.validate()
        if validation['valid']:
            log.info("✅ Конфигурация валидна")
        else:
            log.warning(f"⚠️ Отсутствуют переменные: {validation['missing_vars']}")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка конфигурации: {e}")
        return False

def test_meeting_bot():
    """Тест инициализации Meeting Bot"""
    log.info("🤖 Тестирование Meeting Bot...")
    
    try:
        from server_meeting_bot import server_bot
        
        # Проверка инициализации
        log.info(f"Display name: {server_bot.display_name}")
        log.info(f"Audio recorder: {server_bot.audio_recorder is not None}")
        log.info(f"Speech transcriber: {server_bot.speech_transcriber is not None}")
        
        # Тест определения платформы
        test_urls = [
            "https://zoom.us/j/123456789",
            "https://meet.google.com/abc-defg-hij",
            "https://teams.microsoft.com/l/meetup-join/...",
            "https://talk.kontur.ru/meeting/123",
            "https://telemost.yandex.ru/123456"
        ]
        
        for url in test_urls:
            platform = server_bot.detect_platform(url)
            log.info(f"URL: {url} -> Platform: {platform}")
        
        log.info("✅ Meeting Bot инициализирован корректно")
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка Meeting Bot: {e}")
        return False

def test_audio_system():
    """Тест аудиосистемы"""
    log.info("🎙️ Тестирование аудиосистемы...")
    
    try:
        from audio_capture import MeetingAudioRecorder
        
        recorder = MeetingAudioRecorder()
        devices_info = recorder.get_audio_devices_info()
        
        log.info(f"Input devices: {len(devices_info['input'])}")
        log.info(f"Output devices: {len(devices_info['output'])}")
        log.info(f"Loopback devices: {len(devices_info['loopback'])}")
        
        if devices_info['input']:
            log.info("✅ Аудиоустройства найдены")
        else:
            log.warning("⚠️ Аудиоустройства не найдены")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка аудиосистемы: {e}")
        return False

def test_whisper():
    """Тест Whisper"""
    log.info("🎤 Тестирование Whisper...")
    
    try:
        from speech_transcriber import SpeechTranscriber
        
        transcriber = SpeechTranscriber(model_name="tiny")  # Быстрая модель для теста
        model_info = transcriber.get_model_info()
        
        log.info(f"Model: {model_info['model_name']}")
        log.info(f"Device: {model_info['device']}")
        log.info(f"Language: {model_info['language']}")
        
        log.info("✅ Whisper инициализирован")
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка Whisper: {e}")
        return False

def test_gemini():
    """Тест Gemini AI"""
    log.info("🧠 Тестирование Gemini AI...")
    
    try:
        from gemini_client import test_gemini_connection
        
        if test_gemini_connection():
            log.info("✅ Gemini AI подключен")
            return True
        else:
            log.warning("⚠️ Gemini AI не подключен (проверьте API ключ)")
            return False
            
    except Exception as e:
        log.error(f"❌ Ошибка Gemini AI: {e}")
        return False

def test_bitrix():
    """Тест Bitrix24"""
    log.info("📋 Тестирование Bitrix24...")
    
    try:
        from bitrix import test_bitrix_connection
        
        if test_bitrix_connection():
            log.info("✅ Bitrix24 подключен")
            return True
        else:
            log.warning("⚠️ Bitrix24 не подключен (проверьте webhook URL)")
            return False
            
    except Exception as e:
        log.error(f"❌ Ошибка Bitrix24: {e}")
        return False

def test_telegram():
    """Тест Telegram Bot"""
    log.info("📱 Тестирование Telegram Bot...")
    
    try:
        import requests
        from server_config import config
        
        if not config.TELEGRAM_BOT_TOKEN:
            log.warning("⚠️ TELEGRAM_BOT_TOKEN не настроен")
            return False
        
        # Тест API
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                log.info(f"Bot: @{bot_info.get('username', 'Unknown')}")
                log.info(f"Name: {bot_info.get('first_name', 'Unknown')}")
                log.info("✅ Telegram Bot подключен")
                return True
        
        log.error("❌ Ошибка Telegram API")
        return False
        
    except Exception as e:
        log.error(f"❌ Ошибка Telegram Bot: {e}")
        return False

def main():
    """Основная функция тестирования"""
    log.info("🚀 Начинаю тестирование Meeting Bot Server")
    log.info("=" * 50)
    
    tests = [
        ("Импорт модулей", test_imports),
        ("Конфигурация", test_config),
        ("Meeting Bot", test_meeting_bot),
        ("Аудиосистема", test_audio_system),
        ("Whisper", test_whisper),
        ("Gemini AI", test_gemini),
        ("Bitrix24", test_bitrix),
        ("Telegram Bot", test_telegram),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        log.info(f"\n📋 Тест: {test_name}")
        log.info("-" * 30)
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            log.error(f"❌ Критическая ошибка в тесте {test_name}: {e}")
            results[test_name] = False
    
    # Итоговый отчет
    log.info("\n" + "=" * 50)
    log.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    log.info("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        log.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    log.info(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        log.info("🎉 Все тесты пройдены! Бот готов к работе.")
        return True
    else:
        log.warning(f"⚠️ {total - passed} тестов провалено. Проверьте конфигурацию.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
