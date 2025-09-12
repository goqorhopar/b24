"""
Конфигурация для разных окружений
"""
import os
from typing import Dict, Any

class Config:
    """Базовая конфигурация"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    RENDER_EXTERNAL_URL = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:3000')
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.1'))
    GEMINI_TOP_P = float(os.getenv('GEMINI_TOP_P', '0.2'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '1200'))
    
    # Bitrix24
    BITRIX_WEBHOOK_URL = os.getenv('BITRIX_WEBHOOK_URL')
    BITRIX_RESPONSIBLE_ID = int(os.getenv('BITRIX_RESPONSIBLE_ID', '1'))
    BITRIX_CREATED_BY_ID = int(os.getenv('BITRIX_CREATED_BY_ID', '1'))
    BITRIX_TASK_DEADLINE_DAYS = int(os.getenv('BITRIX_TASK_DEADLINE_DAYS', '3'))
    
    # Application
    PORT = int(os.getenv('PORT', '3000'))
    DB_PATH = os.getenv('DB_PATH', 'bot_state.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    NODE_ENV = os.getenv('NODE_ENV', 'development')
    
    # Request settings
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '2'))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    MAX_COMMENT_LENGTH = int(os.getenv('MAX_COMMENT_LENGTH', '8000'))
    
    # Admin
    ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
    
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

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    NODE_ENV = 'development'

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    LOG_LEVEL = 'INFO'
    NODE_ENV = 'production'

class TestingConfig(Config):
    """Конфигурация для тестирования"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    NODE_ENV = 'test'
    DB_PATH = 'test_bot_state.db'

def get_config() -> Config:
    """Получение конфигурации в зависимости от окружения"""
    env = os.getenv('NODE_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Экспорт конфигурации
config = get_config()
