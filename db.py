import sqlite3, threading
DB_PATH = 'bot_state.db'
_lock = threading.Lock()

def init_db():
    with _lock, sqlite3.connect(DB_PATH) as c:
        c.execute('CREATE TABLE IF NOT EXISTS sessions (chat_id INTEGER PRIMARY KEY, state TEXT, transcript TEXT)')
        c.commit()

def set_session(chat_id, state, transcript=None):
    with _lock, sqlite3.connect(DB_PATH) as c:
        c.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)', (chat_id, state, transcript))
        c.commit()

def get_session(chat_id):
    with _lock, sqlite3.connect(DB_PATH) as c:
        row = c.execute('SELECT state, transcript FROM sessions WHERE chat_id=?', (chat_id,)).fetchone()
        return {'state': row[0], 'transcript': row[1]} if row else None

def clear_session(chat_id):
    with _lock, sqlite3.connect(DB_PATH) as c:
        c.execute('DELETE FROM sessions WHERE chat_id=?', (chat_id,))
        c.commit()
