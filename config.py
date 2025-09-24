#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Dict, Any

class Config:
    """Конфигурация приложения"""
    
    # Основные настройки
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Bitrix24
    BITRIX_WEBHOOK_URL = os.getenv("BITRIX_WEBHOOK_URL")
    BITRIX_DOMAIN = os.getenv("BITRIX_DOMAIN")
    BITRIX_USER_ID = os.getenv("BITRIX_USER_ID")
    
    # Webhook настройки
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
    
    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_state.db")
    
    # Сервер
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "3000"))
    
    # Polling
    USE_POLLING = os.getenv("USE_POLLING", "true").lower() == "true"
    POLLING_TIMEOUT = int(os.getenv("POLLING_TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка обязательных параметров"""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "GEMINI_API_KEY", 
            "BITRIX_WEBHOOK_URL"
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing)}")
            return False
        
        return True
    
    @classmethod
    def runtime_summary(cls) -> Dict[str, Any]:
        """Краткая сводка конфигурации для логирования"""
        return {
            "log_level": cls.LOG_LEVEL,
            "debug": cls.DEBUG,
            "host": cls.HOST,
            "port": cls.PORT,
            "use_polling": cls.USE_POLLING,
            "has_telegram_token": bool(cls.TELEGRAM_BOT_TOKEN),
            "has_gemini_key": bool(cls.GEMINI_API_KEY),
            "has_bitrix_webhook": bool(cls.BITRIX_WEBHOOK_URL),
            "database_url": cls.DATABASE_URL
        }

# Глобальный экземпляр конфигурации
config = Config()
