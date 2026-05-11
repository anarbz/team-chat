import os
import sqlite3
from data import db_session
from data.chats import Chat

DB_DIR = "db/chats"


def ensure_chat_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


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


def create_chat(title, is_group: bool = True) -> int:
    ensure_chat_db_dir()
    db_sess = db_session.create_session()
    try:
        chat = Chat(
            title=title,
            is_group=is_group,
            messages_db_path=""
        )
        db_sess.add(chat)
        db_sess.flush()

        db_path = os.path.join(DB_DIR, f"chat_{chat.id}.db")
        chat.messages_db_path = db_path
        db_sess.commit()

        init_chat_messages_db(db_path)
        return chat.id
    finally:
        db_sess.close()


def add_members_to_chat(chat_id, user_ids):
    if not user_ids:
        return
    db_sess = db_session.create_session()
    try:
        for user_id in user_ids:
            from data.chat_members import ChatMember
            member = ChatMember(chat_id=chat_id, user_id=user_id)
            db_sess.add(member)
        db_sess.commit()
    finally:
        db_sess.close()


def create_full_chat(title, creator_user, member_logins, is_group=True):
    from data.users import User
    db_sess = db_session.create_session()
    try:
        users = db_sess.query(User).filter(User.login.in_(member_logins)).all()
        existing_logins = {u.login for u in users}
        missing = set(member_logins) - existing_logins
        if missing:
            raise ValueError(f"Пользователи не найдены: {missing}")

        chat_id = create_chat(title, is_group)

        member_ids = [u.id for u in users]
        if creator_user.id not in member_ids:
            member_ids.append(creator_user.id)

        add_members_to_chat(chat_id, member_ids)
        return chat_id
    finally:
        db_sess.close()