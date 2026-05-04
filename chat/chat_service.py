import os
import sqlite3
from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from data.users import User

DB_DIR = "db/chats"


def get_chat_by_id(chat_id) -> Chat | None:
    # возвращает чат по его id или None
    db_sess = db_session.create_session()
    return db_sess.query(Chat).filter(Chat.id == chat_id).first()


def get_chat_db_path(chat_id):
    # возвращает путь к бд сообщений чата по chat_id
    chat = get_chat_by_id(chat_id)
    if not chat:
        return None
    return chat.messages_db_path


def ensure_chat_db_dir():
    # создаёт папку для бд чатов, если её ещё нет
    os.makedirs(DB_DIR, exist_ok=True)


def init_chat_messages_db(db_path: str):
    # создаёт отдельную бд для сообщений конкретного чата
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id_message INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """)
        conn.commit()


def create_chat(title, is_group: bool = True) -> int:
    """Создаёт чат в основной БД и возвращает его id"""
    ensure_chat_db_dir()
    db_sess = db_session.create_session()

    chat = Chat(
        title=title,
        is_group=is_group,
        messages_db_path=""
    )
    db_sess.add(chat)
    db_sess.commit()

    db_path = os.path.join(DB_DIR, f"chat_{chat.id}.db")
    db_sess = db_session.create_session()
    chat_to_update = db_sess.query(Chat).get(chat.id)
    chat_to_update.messages_db_path = db_path
    db_sess.commit()
    db_sess.close()

    init_chat_messages_db(db_path)
    return chat.id
