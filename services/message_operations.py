import sqlite3
import datetime
import os
from utils.chat_db_utils import get_chat_db_path
from data import db_session
from data.users import User


def save_message(chat_id: int, sender_id: int, text: str) -> bool:
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return False

    try:
        now = datetime.datetime.now()
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                "INSERT INTO messages (sender_id, message, time) VALUES (?, ?, ?)",
                (sender_id, text, now)
            )
            conn.commit()
        return True
    except Exception:
        return False


def get_messages(chat_id: int, limit: int = 50, offset: int = 0):
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id_message, sender_id, message, time FROM messages ORDER BY time LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_message_senders(messages, db_sess=None):
    if not messages:
        return {}

    sender_ids = {msg['sender_id'] for msg in messages}
    close_session = False
    if db_sess is None:
        db_sess = db_session.create_session()
        close_session = True

    try:
        users = db_sess.query(User).filter(User.id.in_(sender_ids)).all()
        return {u.id: u.login for u in users}
    finally:
        if close_session:
            db_sess.close()


def count_messages(chat_id: int) -> int:
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return 0

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM messages")
        return cur.fetchone()[0]