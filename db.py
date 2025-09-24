#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import logging
import os
from config import config

log = logging.getLogger("db")

def init_db():
    """
    Инициализация базы данных
    """
    try:
        db_path = "bot_state.db"
        
        # Создание подключения к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создание таблицы для состояний пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT DEFAULT 'idle',
                meeting_url TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создание таблицы для логов встреч
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meeting_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                meeting_url TEXT,
                platform TEXT,
                analysis_result TEXT,
                lead_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        log.info("База данных инициализирована успешно")
        
    except Exception as e:
        log.error(f"Ошибка инициализации базы данных: {e}")

def save_user_state(user_id: int, state: str, meeting_url: str = None, platform: str = None):
    """
    Сохранение состояния пользователя
    """
    try:
        conn = sqlite3.connect("bot_state.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_states 
            (user_id, state, meeting_url, platform, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, state, meeting_url, platform))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        log.error(f"Ошибка сохранения состояния пользователя {user_id}: {e}")

def get_user_state(user_id: int) -> dict:
    """
    Получение состояния пользователя
    """
    try:
        conn = sqlite3.connect("bot_state.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT state, meeting_url, platform 
            FROM user_states 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "state": result[0],
                "meeting_url": result[1],
                "platform": result[2]
            }
        else:
            return {"state": "idle"}
            
    except Exception as e:
        log.error(f"Ошибка получения состояния пользователя {user_id}: {e}")
        return {"state": "idle"}

def log_meeting(user_id: int, meeting_url: str, platform: str, analysis_result: str, lead_id: int = None):
    """
    Логирование встречи
    """
    try:
        conn = sqlite3.connect("bot_state.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meeting_logs 
            (user_id, meeting_url, platform, analysis_result, lead_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, meeting_url, platform, analysis_result, lead_id))
        
        conn.commit()
        conn.close()
        
        log.info(f"Встреча пользователя {user_id} записана в лог")
        
    except Exception as e:
        log.error(f"Ошибка логирования встречи: {e}")