from flask import Blueprint, render_template, request, redirect, url_for, abort
import datetime
import sqlite3
from data import db_session
from data.users import User
from data.chats import Chat
from data.chat_members import ChatMember
import os

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat/<int:chat_id>/<username>', methods=['GET', 'POST'])
def chat(chat_id, username):
    db_sess = db_session.create_session()
    try:
        user = db_sess.query(User).filter(User.login == username).first()
        if not user:
            return redirect(url_for('index'))

        member = db_sess.query(ChatMember).filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user.id
        ).first()

        if not member:
            abort(403, description="Вы не являетесь участником этого чата")

        chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            abort(404, description="Чат не найден")

        db_path = chat.messages_db_path
        if not db_path or not os.path.exists(db_path):
            abort(404, description="База сообщений чата не найдена")

        if request.method == 'POST':
            message_text = request.form.get('message', '').strip()
            if message_text:
                now = datetime.datetime.now()
                with sqlite3.connect(db_path) as conn:
                    conn.execute(
                        "INSERT INTO messages (sender_id, message, time) VALUES (?, ?, ?)",
                        (user.id, message_text, now)
                    )
                    conn.commit()
            return redirect(url_for('chat.chat', chat_id=chat_id, username=username))

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT id_message, sender_id, message, time FROM messages ORDER BY time")
            messages_rows = cur.fetchall()

        sender_ids = {row['sender_id'] for row in messages_rows}
        users_map = {}
        if sender_ids:
            users_from_db = db_sess.query(User).filter(User.id.in_(sender_ids)).all()
            users_map = {u.id: u.login for u in users_from_db}

        messages = []
        for row in messages_rows:
            messages.append({
                'user': users_map.get(row['sender_id'], 'Unknown'),
                'time': row['time'],
                'message': row['message']
            })

        return render_template('chat.html', messages=messages, username=username, chat_id=chat_id)

    finally:
        db_sess.close()