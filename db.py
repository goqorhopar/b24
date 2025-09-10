import sqlite3
import threading
import logging
import os
from typing import Optional, Dict

# Настройка логирования
log = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = os.getenv('DB_PATH', 'bot_state.db')

# Thread-safe операции с БД
_db_lock = threading.Lock()

def init_db():
    """Инициализация базы данных"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Создание таблицы сессий
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        chat_id INTEGER PRIMARY KEY,
                        state TEXT NOT NULL,
                        transcript TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Создание таблицы для логов операций
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
                
                # Создание индексов для производительности
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_chat_id ON sessions(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_chat_id ON operation_logs(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at)')
                
                conn.commit()
                log.info("База данных инициализирована успешно")
                
    except sqlite3.Error as e:
        log.error(f"Ошибка инициализации базы данных: {e}")
        raise
    except Exception as e:
        log.error(f"Неожиданная ошибка инициализации БД: {e}")
        raise

def set_session(chat_id: int, state: str, transcript: Optional[str] = None):
    """Сохранение состояния сессии"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions 
                    (chat_id, state, transcript, updated_at) 
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (chat_id, state, transcript))
                
                conn.commit()
                log.debug(f"Сессия сохранена для chat_id {chat_id}: state={state}")
                
    except sqlite3.Error as e:
        log.error(f"Ошибка сохранения сессии для chat_id {chat_id}: {e}")
        raise
    except Exception as e:
        log.error(f"Неожиданная ошибка сохранения сессии: {e}")
        raise

def get_session(chat_id: int) -> Optional[Dict[str, str]]:
    """Получение состояния сессии"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT state, transcript, created_at, updated_at 
                    FROM sessions 
                    WHERE chat_id = ?
                ''', (chat_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return {
                        'state': row[0],
                        'transcript': row[1],
                        'created_at': row[2],
                        'updated_at': row[3]
                    }
                else:
                    log.debug(f"Сессия не найдена для chat_id {chat_id}")
                    return None
                    
    except sqlite3.Error as e:
        log.error(f"Ошибка получения сессии для chat_id {chat_id}: {e}")
        return None
    except Exception as e:
        log.error(f"Неожиданная ошибка получения сессии: {e}")
        return None

def clear_session(chat_id: int):
    """Удаление сессии"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM sessions WHERE chat_id = ?', (chat_id,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                
                if deleted_count > 0:
                    log.debug(f"Сессия удалена для chat_id {chat_id}")
                else:
                    log.debug(f"Сессия не найдена для удаления chat_id {chat_id}")
                    
    except sqlite3.Error as e:
        log.error(f"Ошибка удаления сессии для chat_id {chat_id}: {e}")
        raise
    except Exception as e:
        log.error(f"Неожиданная ошибка удаления сессии: {e}")
        raise

def log_operation(chat_id: int, operation: str, status: str, details: Optional[str] = None):
    """Логирование операций"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO operation_logs 
                    (chat_id, operation, status, details) 
                    VALUES (?, ?, ?, ?)
                ''', (chat_id, operation, status, details))
                
                conn.commit()
                log.debug(f"Операция залогирована: chat_id={chat_id}, operation={operation}, status={status}")
                
    except sqlite3.Error as e:
        log.error(f"Ошибка логирования операции: {e}")
    except Exception as e:
        log.error(f"Неожиданная ошибка логирования: {e}")

def get_operation_logs(chat_id: int, limit: int = 10):
    """Получение логов операций для пользователя"""
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
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'operation': row[0],
                        'status': row[1],
                        'details': row[2],
                        'created_at': row[3]
                    }
                    for row in rows
                ]
                
    except sqlite3.Error as e:
        log.error(f"Ошибка получения логов для chat_id {chat_id}: {e}")
        return []
    except Exception as e:
        log.error(f"Неожиданная ошибка получения логов: {e}")
        return []

def get_stats():
    """Получение статистики использования"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Общее количество сессий
                cursor.execute('SELECT COUNT(*) FROM sessions')
                total_sessions = cursor.fetchone()[0]
                
                # Активные сессии
                cursor.execute("SELECT COUNT(*) FROM sessions WHERE state != 'COMPLETED'")
                active_sessions = cursor.fetchone()[0]
                
                # Количество операций за последние 24 часа
                cursor.execute('''
                    SELECT COUNT(*) FROM operation_logs 
                    WHERE created_at > datetime('now', '-24 hours')
                ''')
                operations_24h = cursor.fetchone()[0]
                
                # Успешные операции за последние 24 часа
                cursor.execute('''
                    SELECT COUNT(*) FROM operation_logs 
                    WHERE created_at > datetime('now', '-24 hours') 
                    AND status = 'SUCCESS'
                ''')
                successful_ops_24h = cursor.fetchone()[0]
                
                return {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'operations_24h': operations_24h,
                    'successful_ops_24h': successful_ops_24h,
                    'success_rate_24h': (successful_ops_24h / operations_24h * 100) if operations_24h > 0 else 0
                }
                
    except sqlite3.Error as e:
        log.error(f"Ошибка получения статистики: {e}")
        return {}
    except Exception as e:
        log.error(f"Неожиданная ошибка получения статистики: {e}")
        return {}

def cleanup_old_sessions(days_old: int = 7):
    """Очистка старых сессий"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Удаление старых сессий
                cursor.execute('''
                    DELETE FROM sessions 
                    WHERE updated_at < datetime('now', '-{} days')
                '''.format(days_old))
                
                deleted_sessions = cursor.rowcount
                
                # Удаление старых логов (оставляем 30 дней)
                cursor.execute('''
                    DELETE FROM operation_logs 
                    WHERE created_at < datetime('now', '-30 days')
                ''')
                
                deleted_logs = cursor.rowcount
                
                conn.commit()
                
                log.info(f"Очистка завершена: удалено {deleted_sessions} сессий и {deleted_logs} логов")
                return deleted_sessions, deleted_logs
                
    except sqlite3.Error as e:
        log.error(f"Ошибка очистки старых данных: {e}")
        return 0, 0
    except Exception as e:
        log.error(f"Неожиданная ошибка очистки: {e}")
        return 0, 0

def vacuum_database():
    """Оптимизация базы данных"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('VACUUM')
                log.info("База данных оптимизирована (VACUUM)")
                
    except sqlite3.Error as e:
        log.error(f"Ошибка оптимизации базы данных: {e}")
    except Exception as e:
        log.error(f"Неожиданная ошибка оптимизации БД: {e}")

# Автоматическая инициализация при импорте модуля
if __name__ != '__main__':
    try:
        init_db()
    except Exception as e:
        log.critical(f"Критическая ошибка инициализации БД при импорте: {e}")
