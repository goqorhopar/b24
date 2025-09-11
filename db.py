import sqlite3
import threading
import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

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

                # Таблица для статистики опционально
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS processed_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        success INTEGER,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Индексы
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_chat_id ON sessions(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_chat_id ON operation_logs(chat_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_created_at ON operation_logs(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_ops_created_at ON processed_operations(created_at)')

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


def get_session(chat_id: int) -> Optional[Dict[str, Any]]:
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


def get_operation_logs(chat_id: int, limit: int = 10) -> List[Dict[str, Any]]:
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


def get_stats() -> Dict[str, Any]:
    """Получение статистики использования"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()

                # Общее количество сессий
                cursor.execute('SELECT COUNT(*) FROM sessions')
                total_sessions = cursor.fetchone()[0] or 0

                # Активные сессии — определяем как сессии, обновлённые за последние 24 часа
                since = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('SELECT COUNT(*) FROM sessions WHERE updated_at >= ?', (since,))
                active_sessions = cursor.fetchone()[0] or 0

                # Операции за 24 часа
                cursor.execute('SELECT COUNT(*) FROM operation_logs WHERE created_at >= ?', (since,))
                operations_24h = cursor.fetchone()[0] or 0

                # Успешные операции за 24 часа
                cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE created_at >= ? AND status = 'success'", (since,))
                successful_ops_24h = cursor.fetchone()[0] or 0

                success_rate = (successful_ops_24h / operations_24h * 100) if operations_24h > 0 else 0.0

                return {
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'operations_24h': operations_24h,
                    'successful_ops_24h': successful_ops_24h,
                    'success_rate_24h': success_rate
                }

    except sqlite3.Error as e:
        log.error(f"Ошибка получения статистики: {e}")
        return {}
    except Exception as e:
        log.error(f"Неожиданная ошибка получения статистики: {e}")
        return {}


def cleanup_old_sessions(days: int = 90) -> int:
    """Удаление старых сессий старше days дней. Возвращает количество удалённых записей."""
    try:
        cutoff = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM sessions WHERE updated_at < ?', (cutoff,))
                deleted = cursor.rowcount
                conn.commit()
                log.info(f"Удалено {deleted} устаревших сессий")
                return deleted
    except sqlite3.Error as e:
        log.error(f"Ошибка при очистке старых сессий: {e}")
        return 0
    except Exception as e:
        log.error(f"Неожиданная ошибка при очистке: {e}")
        return 0
