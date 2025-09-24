#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
from typing import Dict, Any, Optional
from config import config

log = logging.getLogger("db")

def init_db():
    """
    Инициализация базы данных
    """
    try:
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создание таблиц
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL DEFAULT 'idle',
                meeting_url TEXT,
                platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                meeting_url TEXT NOT NULL,
                platform TEXT,
                analysis_result TEXT,
                lead_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                meetings_processed INTEGER DEFAULT 0,
                leads_updated INTEGER DEFAULT 0,
                tasks_created INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        log.info("База данных инициализирована успешно")
        
    except Exception as e:
        log.error(f"Ошибка инициализации базы данных: {e}")
        raise

def save_user_state(user_id: int, state: str, meeting_url: str = None, platform: str = None):
    """
    Сохранение состояния пользователя
    """
    try:
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_states 
            (user_id, state, meeting_url, platform, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, state, meeting_url, platform))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        log.error(f"Ошибка сохранения состояния пользователя {user_id}: {e}")

def get_user_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение состояния пользователя
    """
    try:
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT state, meeting_url, platform, created_at, updated_at
            FROM user_states WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "state": result[0],
                "meeting_url": result[1],
                "platform": result[2],
                "created_at": result[3],
                "updated_at": result[4]
            }
        return None
        
    except Exception as e:
        log.error(f"Ошибка получения состояния пользователя {user_id}: {e}")
        return None

def log_meeting(user_id: int, meeting_url: str, platform: str, analysis_result: str = None, lead_id: int = None):
    """
    Логирование встречи
    """
    try:
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meeting_logs 
            (user_id, meeting_url, platform, analysis_result, lead_id)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, meeting_url, platform, analysis_result, lead_id))
        
        conn.commit()
        conn.close()
        
        log.info(f"Встреча пользователя {user_id} записана в лог")
        
    except Exception as e:
        log.error(f"Ошибка логирования встречи: {e}")

def get_meeting_stats() -> Dict[str, Any]:
    """
    Получение статистики встреч
    """
    try:
        db_path = config.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Общее количество встреч
        cursor.execute("SELECT COUNT(*) FROM meeting_logs")
        total_meetings = cursor.fetchone()[0]
        
        # Встречи за последние 7 дней
        cursor.execute("""
            SELECT COUNT(*) FROM meeting_logs 
            WHERE created_at >= datetime('now', '-7 days')
        """)
        recent_meetings = cursor.fetchone()[0]
        
        # Платформы
        cursor.execute("""
            SELECT platform, COUNT(*) FROM meeting_logs 
            GROUP BY platform ORDER BY COUNT(*) DESC
        """)
        platforms = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_meetings": total_meetings,
            "recent_meetings": recent_meetings,
            "platforms": platforms
        }
        
    except Exception as e:
        log.error(f"Ошибка получения статистики: {e}")
        return {
            "total_meetings": 0,
            "recent_meetings": 0,
            "platforms": {}
        }
