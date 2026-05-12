from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
import sqlite3
import os
import datetime
from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from data.users import User
from utils.chat_db_utils import get_chat_db_path
from services.message_operations import edit_message, delete_message

chat_bp = Blueprint('chat', __name__, template_folder='../templates')


@chat_bp.route('/chat/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def chat(chat_id):
    db_sess = db_session.create_session()
    try:
        chat_obj = db_sess.query(Chat).filter(Chat.id == chat_id).first()
        if not chat_obj:
            abort(404, description="Чат не найден")

        member = db_sess.query(ChatMember).filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == current_user.id
        ).first()
        if not member:
            abort(403, description="Вы не являетесь участником этого чата")

        db_path = get_chat_db_path(chat_id)
        if not db_path or not os.path.exists(db_path):
            abort(404, description="База сообщений чата не найдена")

        if request.method == 'POST':
            message_text = request.form.get('message', '').strip()
            if message_text:
                now = datetime.datetime.now()
                with sqlite3.connect(db_path) as conn:
                    conn.execute(
                        "INSERT INTO messages (sender_id, message, time) VALUES (?, ?, ?)",
                        (current_user.id, message_text, now)
                    )
                    conn.commit()
            return redirect(url_for('chat.chat', chat_id=chat_id))

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT id_message, sender_id, message, time FROM messages ORDER BY time"
            )
            messages_rows = cur.fetchall()

        sender_ids = {row['sender_id'] for row in messages_rows}
        users_map = {}
        if sender_ids:
            users_from_db = db_sess.query(User).filter(User.id.in_(sender_ids)).all()
            users_map = {u.id: u.login for u in users_from_db}

        messages = []
        for row in messages_rows:
            messages.append({
                'id': row['id_message'],
                'user': users_map.get(row['sender_id'], 'Unknown'),
                'time': row['time'],
                'message': row['message']
            })

        return render_template(
            'chat.html',
            messages=messages,
            username=current_user.login,
            chat_id=chat_id
        )

    finally:
        db_sess.close()


@chat_bp.route('/chat/<int:chat_id>/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message_route(chat_id, message_id):
    success = delete_message(chat_id, message_id, current_user.id)
    if not success:
        return 'Нельзя удалить чужое сообщение', 403
    return redirect(url_for('chat.chat', chat_id=chat_id))

@chat_bp.route('/chat/<int:chat_id>/edit_message/<int:message_id>', methods=['POST'])
@login_required
def edit_message_route(chat_id, message_id):
    data = request.get_json()
    new_text = data.get('new_text', '').strip() if data else ''
    if not new_text:
        return {'error': 'Пустое сообщение'}, 400
    success = edit_message(chat_id, message_id, new_text, current_user.id)
    if not success:
        return {'error': 'Нельзя редактировать чужое сообщение'}, 403
    return {'success': True}