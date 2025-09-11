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
                
                conn.commit()
    except sqlite3.Error as e:
        log.error(f"Ошибка инициализации БД: {e}")
        raise
    except Exception as e:
        log.error(f"Неожиданная ошибка инициализации БД: {e}")
        raise

def set_session(chat_id: int, state: str, transcript: Optional[str] = None) -> None:
    """Установка или обновление состояния сессии"""
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Проверяем, существует ли сессия
            cursor.execute("SELECT 1 FROM sessions WHERE chat_id = ?", (chat_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Обновляем существующую сессию
                cursor.execute('''
                    UPDATE sessions
                    SET state = ?, transcript = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE chat_id = ?
                ''', (state, transcript, chat_id))
            else:
                # Создаем новую сессию
                cursor.execute('''
                    INSERT INTO sessions (chat_id, state, transcript)
                    VALUES (?, ?, ?)
                ''', (chat_id, state, transcript))
            
            conn.commit()
            log.info(f"Сессия для чата {chat_id} установлена. Состояние: {state}")

def get_session(chat_id: int) -> Optional[Dict]:
    """Получение состояния сессии"""
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE chat_id = ?", (chat_id,))
            row = cursor.fetchone()
            if row:
                log.info(f"Получена сессия для чата {chat_id}. Состояние: {row['state']}")
                return dict(row)
            return None

def clear_session(chat_id: int) -> None:
    """Очистка сессии для чата"""
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE chat_id = ?", (chat_id,))
            conn.commit()
            log.info(f"Сессия для чата {chat_id} очищена")

def log_operation(chat_id: int, operation: str, status: str, details: Optional[str] = None) -> None:
    """Логирование операции"""
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_logs (chat_id, operation, status, details)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, operation, status, details))
            conn.commit()
            log.debug(f"Лог операции: chat_id={chat_id}, operation={operation}, status={status}")

def get_stats() -> Dict[str, Any]:
    """Получение статистики"""
    stats = {}
    with _db_lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Всего сессий
            cursor.execute("SELECT COUNT(*) FROM sessions")
            stats['total_sessions'] = cursor.fetchone()[0]
            
            # Активные сессии (статус не 'finished')
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE state != 'FINISHED'")
            stats['active_sessions'] = cursor.fetchone()[0]

            # Всего операций
            cursor.execute("SELECT COUNT(*) FROM operation_logs")
            stats['total_operations'] = cursor.fetchone()[0]
            
            # Успешные операции
            cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE status = 'success'")
            stats['successful_operations'] = cursor.fetchone()[0]
            
            # Операции за последние 24 часа
            cursor.execute("SELECT COUNT(*) FROM operation_logs WHERE created_at > datetime('now', '-1 day')")
            stats['operations_last_24h'] = cursor.fetchone()[0]
            
    return stats

def cleanup_old_sessions(days_old: int = 7) -> Tuple[int, int]:
    """Удаление старых сессий и логов"""
    try:
        with _db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Удаление старых сессий
                cursor.execute(f'''
                    DELETE FROM sessions
                    WHERE created_at < datetime('now', '-{days_old} days')
                ''')
                
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
        log.critical(f"Критическая ошибка инициализации базы данных: {e}")
        # При импорте модуля, если БД не инициализируется, приложение не сможет работать.
        # Поэтому выбрасываем исключение, чтобы остановить запуск.
        raise RuntimeError("Не удалось инициализировать базу данных.") from e
