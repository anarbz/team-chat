import sqlite3
import datetime

DB_NAME = "test_bd.db"

def init_db():
    """Создаёт таблицу messages."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id_message INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                message TEXT NOT NULL,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def add_message(user: str, message: str, time: datetime.datetime):
    """Добавляет новое сообщение в базу."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (user, message, time)
            VALUES (?, ?, ?)
        ''', (user, message, time))
        conn.commit()

def get_messages():
    """
    Возвращает список всех сообщений, отсортированных по времени.
    Сообщение (id_message, user, message, time).
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row  # чтобы обращаться по имени колонки (опционально)
        cursor = conn.cursor()
        cursor.execute('SELECT id_message, user, message, time FROM messages ORDER BY time')
        return cursor.fetchall()


def clear_db():
    """Удаляет все сообщения из таблицы messages."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM messages')
        conn.commit()


if __name__ == "__main__":
    init_db()
    clear_db()