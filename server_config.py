"""
Конфигурация для серверного развертывания бота
"""
import os
from typing import Dict, Any

class ServerConfig:
    """Конфигурация для серверного режима"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:3000')
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_MODEL_FALLBACK = os.getenv('GEMINI_MODEL_FALLBACK', 'gemini-1.5-flash')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
    GEMINI_TOP_P = float(os.getenv('GEMINI_TOP_P', '0.2'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '1200'))
    GEMINI_INPUT_MAX_CHARS = int(os.getenv('GEMINI_INPUT_MAX_CHARS', '15000'))
    
    # Bitrix24
    BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
    BITRIX_RESPONSIBLE_ID = int(os.getenv('BITRIX_RESPONSIBLE_ID', '1'))
    BITRIX_CREATED_BY_ID = int(os.getenv('BITRIX_CREATED_BY_ID', '1'))
    BITRIX_TASK_DEADLINE_DAYS = int(os.getenv('BITRIX_TASK_DEADLINE_DAYS', '3'))
    
    # Application
    PORT = int(os.getenv('PORT', '3000'))
    DB_PATH = os.getenv('DB_PATH', 'bot_state.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    NODE_ENV = os.getenv('NODE_ENV', 'production')
    
    # Request settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))
    RETRY_JITTER = float(os.getenv('RETRY_JITTER', '0.5'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_COMMENT_LENGTH = int(os.getenv('MAX_COMMENT_LENGTH', '8000'))
    
    # Admin
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', '7537953397')
    
    # Meeting Automation - Server Settings
    MEETING_DISPLAY_NAME = os.getenv('MEETING_DISPLAY_NAME', 'Асистент Григория')
    MEETING_HEADLESS = os.getenv('MEETING_HEADLESS', 'true').lower() == 'true'
    MEETING_AUTO_LEAVE = os.getenv('MEETING_AUTO_LEAVE', 'true').lower() == 'true'
    MEETING_DURATION_MINUTES = int(os.getenv('MEETING_DURATION_MINUTES', '60'))
    
    # Audio Recording
    AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))
    AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', '1'))
    AUDIO_CHUNK_SIZE = int(os.getenv('AUDIO_CHUNK_SIZE', '1024'))
    AUDIO_RECORDING_METHOD = os.getenv('AUDIO_RECORDING_METHOD', 'auto')  # auto, system, screen, browser
    
    # Speech Recognition
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
    WHISPER_LANGUAGE = os.getenv('WHISPER_LANGUAGE', 'ru')
    WHISPER_DEVICE = os.getenv('WHISPER_DEVICE', 'auto')  # auto, cpu, cuda
    
    # Chrome/WebDriver Settings
    CHROME_HEADLESS = os.getenv('CHROME_HEADLESS', 'true').lower() == 'true'
    CHROME_WINDOW_SIZE = os.getenv('CHROME_WINDOW_SIZE', '1920,1080')
    CHROME_USER_AGENT = os.getenv('CHROME_USER_AGENT', 
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Server Performance
    MAX_CONCURRENT_MEETINGS = int(os.getenv('MAX_CONCURRENT_MEETINGS', '3'))
    MEETING_TIMEOUT_SECONDS = int(os.getenv('MEETING_TIMEOUT_SECONDS', '3600'))  # 1 час
    CLEANUP_INTERVAL_MINUTES = int(os.getenv('CLEANUP_INTERVAL_MINUTES', '30'))
    
    # File Management
    TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/meeting_bot')
    MAX_TEMP_FILES = int(os.getenv('MAX_TEMP_FILES', '10'))
    TEMP_FILE_RETENTION_HOURS = int(os.getenv('TEMP_FILE_RETENTION_HOURS', '24'))
    
    # Security
    ALLOWED_CHAT_IDS = os.getenv('ALLOWED_CHAT_IDS', '').split(',') if os.getenv('ALLOWED_CHAT_IDS') else []
    BLOCKED_CHAT_IDS = os.getenv('BLOCKED_CHAT_IDS', '').split(',') if os.getenv('BLOCKED_CHAT_IDS') else []
    
    # Monitoring
    ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
    METRICS_PORT = int(os.getenv('METRICS_PORT', '9090'))
    
    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Проверка обязательных переменных окружения"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        return {
            'valid': len(missing_vars) == 0,
            'missing_vars': missing_vars
        }

    @classmethod
    def runtime_summary(cls) -> Dict[str, Any]:
        """Сводка ключевых настроек для логирования при старте"""
        return {
            'NODE_ENV': cls.NODE_ENV,
            'PORT': cls.PORT,
            'LOG_LEVEL': cls.LOG_LEVEL,
            'MEETING_DISPLAY_NAME': cls.MEETING_DISPLAY_NAME,
            'MEETING_HEADLESS': cls.MEETING_HEADLESS,
            'MEETING_DURATION_MINUTES': cls.MEETING_DURATION_MINUTES,
            'WHISPER_MODEL': cls.WHISPER_MODEL,
            'AUDIO_RECORDING_METHOD': cls.AUDIO_RECORDING_METHOD,
            'MAX_CONCURRENT_MEETINGS': cls.MAX_CONCURRENT_MEETINGS,
            'GEMINI_MODEL': cls.GEMINI_MODEL,
            'BITRIX_WEBHOOK_URL': bool(cls.BITRIX_WEBHOOK_URL),
            'ADMIN_CHAT_ID': cls.ADMIN_CHAT_ID
        }

    @classmethod
    def get_chrome_options(cls) -> Dict[str, Any]:
        """Получить настройки Chrome для WebDriver"""
        return {
            'headless': cls.CHROME_HEADLESS,
            'window_size': cls.CHROME_WINDOW_SIZE,
            'user_agent': cls.CHROME_USER_AGENT,
            'disable_images': True,
            'disable_notifications': True,
            'disable_popups': True,
            'enable_media_stream': True
        }

    @classmethod
    def get_audio_settings(cls) -> Dict[str, Any]:
        """Получить настройки аудио"""
        return {
            'sample_rate': cls.AUDIO_SAMPLE_RATE,
            'channels': cls.AUDIO_CHANNELS,
            'chunk_size': cls.AUDIO_CHUNK_SIZE,
            'recording_method': cls.AUDIO_RECORDING_METHOD
        }

    @classmethod
    def get_whisper_settings(cls) -> Dict[str, Any]:
        """Получить настройки Whisper"""
        return {
            'model': cls.WHISPER_MODEL,
            'language': cls.WHISPER_LANGUAGE,
            'device': cls.WHISPER_DEVICE
        }

    @classmethod
    def is_chat_allowed(cls, chat_id: str) -> bool:
        """Проверить, разрешен ли чат"""
        chat_id_str = str(chat_id)
        
        # Проверка заблокированных
        if chat_id_str in cls.BLOCKED_CHAT_IDS:
            return False
        
        # Если есть список разрешенных, проверяем его
        if cls.ALLOWED_CHAT_IDS:
            return chat_id_str in cls.ALLOWED_CHAT_IDS
        
        # По умолчанию разрешены все
        return True

class DevelopmentConfig(ServerConfig):
    """Конфигурация для разработки"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    NODE_ENV = 'development'
    MEETING_HEADLESS = False  # Для разработки показываем браузер
    CHROME_HEADLESS = False

class ProductionConfig(ServerConfig):
    """Конфигурация для продакшена"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    NODE_ENV = 'production'
    MEETING_HEADLESS = True
    CHROME_HEADLESS = True

class TestingConfig(ServerConfig):
    """Конфигурация для тестирования"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    NODE_ENV = 'test'
    DB_PATH = 'test_bot_state.db'
    MEETING_HEADLESS = True
    CHROME_HEADLESS = True

def get_config() -> ServerConfig:
    """Получение конфигурации в зависимости от окружения"""
    env = os.getenv('NODE_ENV', 'production').lower()
    
    if env == 'development':
        return DevelopmentConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return ProductionConfig()

# Экспорт конфигурации
config = get_config()
