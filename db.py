import sqlite3
import threading
import logging
import os
import json
from typing import Optional, Dict, Any, List

log = logging.getLogger(__name__)

DB_PATH = os.getenv('DB_PATH', 'bot_state.db')
_db_lock = threading.Lock()

def init_db():
    """Инициализация базы данных"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        chat_id INTEGER PRIMARY KEY,
                        state TEXT NOT NULL,
                        transcript TEXT,
                        data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER NOT NULL,
                        operation TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_chat_id ON sessions(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_chat_id ON operation_logs(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at)')
                
                conn.commit()
                log.info("База данных инициализирована успешно")
                
    except sqlite3.Error as e:
        log.error(f"Ошибка инициализации базы данных: {e}")
        raise

def set_session(chat_id: int, state: str, transcript: Optional[str] = None, data: Optional[Dict] = None):
    """Сохранение состояния сессии"""
    try:
        data_json = json.dumps(data) if data else None
        
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions 
                    (chat_id, state, transcript, data, updated_at) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (chat_id, state, transcript, data_json))
                
                conn.commit()
                log.debug(f"Сессия сохранена для chat_id {chat_id}: state={state}")
                
    except Exception as e:
        log.error(f"Ошибка сохранения сессии: {e}")
        raise

def get_session(chat_id: int) -> Optional[Dict[str, Any]]:
    """Получение состояния сессии"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT state, transcript, data, created_at, updated_at 
                    FROM sessions 
                    WHERE chat_id = ?
                ''', (chat_id,))
                
                row = cursor.fetchone()
                
                if row:
                    data = json.loads(row[2]) if row[2] else {}
                    return {
                        'state': row[0],
                        'transcript': row[1],
                        'data': data,
                        'created_at': row[3],
                        'updated_at': row[4]
                    }
                return None
                    
    except Exception as e:
        log.error(f"Ошибка получения сессии: {e}")
        return None

def clear_session(chat_id: int):
    """Удаление сессии"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE chat_id = ?', (chat_id,))
                conn.commit()
                log.debug(f"Сессия удалена для chat_id {chat_id}")
                    
    except Exception as e:
        log.error(f"Ошибка удаления сессии: {e}")
        raise

def log_operation(chat_id: int, operation: str, status: str, details: Optional[Any] = None):
    """Логирование операций"""
    try:
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else str(details)
        
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO operation_logs 
                    (chat_id, operation, status, details) 
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, operation, status, details_str))
                
                conn.commit()
                log.debug(f"Операция залогирована: chat_id={chat_id}, operation={operation}")
                
    except Exception as e:
        log.error(f"Ошибка логирования операции: {e}")

def get_operation_logs(chat_id: int, limit: int = 10) -> List[Dict]:
    """Получение логов операций"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT operation, status, details, created_at 
                    FROM operation_logs 
                    WHERE chat_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (chat_id, limit))
                
                return [
                    {
                        'operation': row[0],
                        'status': row[1],
                        'details': row[2],
                        'created_at': row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
    except Exception as e:
        log.error(f"Ошибка получения логов: {e}")
        return []

def get_stats() -> Dict[str, Any]:
    """Получение статистики"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM sessions')
                total_sessions = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM sessions WHERE state != 'COMPLETED'")
                active_sessions = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM operation_logs WHERE created_at > datetime("now", "-24 hours")')
                operations_24h = cursor.fetchone()[0]
                
                cursor.execute('''
                    SELECT COUNT(*) FROM operation_logs 
                    WHERE created_at > datetime("now", "-24 hours") AND status = "SUCCESS"
                ''')
                successful_ops_24h = cursor.fetchone()[0]
                
                return {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'operations_24h': operations_24h,
                    'successful_ops_24h': successful_ops_24h,
                    'success_rate_24h': (successful_ops_24h / operations_24h * 100) if operations_24h > 0 else 0
                }
                
    except Exception as e:
        log.error(f"Ошибка получения статистики: {e}")
        return {}

def cleanup_old_sessions(days_old: int = 7) -> int:
    """Очистка старых сессий"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute(f'''
                    DELETE FROM sessions 
                    WHERE updated_at < datetime("now", "-{days_old} days")
                ''')
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                log.info(f"Очищено {deleted_count} устаревших сессий")
                return deleted_count
                
    except Exception as e:
        log.error(f"Ошибка очистки сессий: {e}")
        return 0

# Автоматическая инициализация
if __name__ != '__main__':
    try:
        init_db()
    except Exception as e:
        log.critical(f"Критическая ошибка инициализации БД: {e}")
