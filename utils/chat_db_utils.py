import os
import sqlite3
from data import db_session
from data.chats import Chat

DB_DIR = "db/chats"


def ensure_chat_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def get_chat_db_path(chat_id: int) -> str | None:
    db_sess = db_session.create_session()
    try:
        chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            return None
        return chat.messages_db_path
    finally:
        db_sess.close()


def init_chat_messages_db(db_path: str):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id_message INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON messages(time)")
        conn.commit()