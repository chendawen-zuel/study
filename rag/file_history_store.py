"""SQLite 长期会话存储。每次操作单独连接，避免 Streamlit 多线程共用连接。"""
import json
import sqlite3
from uuid import uuid4
from pathlib import Path
from contextlib import contextmanager
from config_data import ROOT


class HistoryStore:
    def __init__(self, path=ROOT / 'chat_history' / 'history.sqlite3'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL REFERENCES sessions(id),
                    role TEXT NOT NULL, content TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def new_session(self):
        session_id = str(uuid4())
        with self.connect() as db:
            db.execute('INSERT INTO sessions(id,title) VALUES (?,?)', (session_id, '新对话'))
        return session_id

    def sessions(self):
        with self.connect() as db:
            return [dict(x) for x in db.execute('SELECT * FROM sessions ORDER BY rowid DESC')]

    def messages(self, session_id):
        with self.connect() as db:
            rows = db.execute('SELECT * FROM messages WHERE session_id=? ORDER BY id', (session_id,))
            return [dict(x) | {'details': json.loads(x['details'])} for x in rows]

    def save_turn(self, session_id, question, result):
        # 问题和回答在同一个事务写入：失败时不会留下半个对话。
        with self.connect() as db:
            count = db.execute('SELECT COUNT(*) FROM messages WHERE session_id=?', (session_id,)).fetchone()[0]
            if count == 0:
                db.execute('UPDATE sessions SET title=? WHERE id=?', (question[:24], session_id))
            db.executemany('INSERT INTO messages(session_id,role,content,details) VALUES (?,?,?,?)', [
                (session_id, 'user', question, '{}'),
                (session_id, 'assistant', result['answer'], json.dumps(result, ensure_ascii=False)),
            ])
