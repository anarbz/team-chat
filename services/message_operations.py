import sqlite3
import datetime
import os
from utils.chat_db_utils import get_chat_db_path
from data import db_session
from data.users import User


def save_message(chat_id: int, sender_id: int, text: str, file_info: dict = None) -> bool:
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return False

    try:
        now = datetime.datetime.now()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    mime_type TEXT,
                    FOREIGN KEY (message_id) REFERENCES messages(id_message) ON DELETE CASCADE
                )
            """)

            cursor.execute(
                "INSERT INTO messages (sender_id, message, time) VALUES (?, ?, ?)",
                (sender_id, text, now)
            )
            message_id = cursor.lastrowid

            if file_info:
                cursor.execute(
                    """INSERT INTO attachments 
                       (message_id, file_name, file_path, file_size, mime_type) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (message_id, file_info['file_name'], file_info['file_path'],
                     file_info['file_size'], file_info['mime_type'])
                )
            conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка сохранения сообщения: {e}")
        return False


def get_messages_with_attachments(chat_id: int, limit: int = 50, offset: int = 0):
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT id_message, sender_id, message, time FROM messages ORDER BY time LIMIT ? OFFSET ?",
            (limit, offset)
        )
        messages = [dict(row) for row in cur.fetchall()]

        if not messages:
            return messages

        # Собираем attachments для этих сообщений
        message_ids = [m['id_message'] for m in messages]
        placeholders = ','.join('?' for _ in message_ids)
        cur = conn.execute(f"""
            SELECT message_id, id, file_name, file_path, file_size, mime_type 
            FROM attachments 
            WHERE message_id IN ({placeholders})
        """, message_ids)
        attachments = cur.fetchall()

        att_by_msg = {}
        for att in attachments:
            att_by_msg.setdefault(att['message_id'], []).append(dict(att))

        for msg in messages:
            msg['attachments'] = att_by_msg.get(msg['id_message'], [])
    return messages


def get_messages(chat_id: int, limit: int = 50, offset: int = 0):
    msgs = get_messages_with_attachments(chat_id, limit, offset)
    for msg in msgs:
        msg.pop('attachments', None)
    return msgs


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


def edit_message(chat_id: int, message_id: int, new_text: str, user_id: int) -> bool:
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return False
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sender_id FROM messages WHERE id_message = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                return False
            cursor.execute(
                "UPDATE messages SET message = ? WHERE id_message = ?",
                (new_text, message_id)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка редактирования сообщения: {e}")
        return False

def delete_message(chat_id: int, message_id: int, user_id: int) -> bool:
    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        return False
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT sender_id FROM messages WHERE id_message = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            if not row or row[0] != user_id:
                return False
            cursor.execute("DELETE FROM messages WHERE id_message = ?", (message_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка удаления сообщения: {e}")
        return False