from flask import Blueprint, render_template, request, redirect, url_for, abort, send_file, current_app
from flask_login import login_required, current_user
import os
from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from data.users import User
from utils.chat_db_utils import get_chat_db_path
from services.message_operations import save_message, edit_message, delete_message, get_messages_with_attachments, get_message_senders
from utils.file_utils import save_uploaded_file

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

        if request.method == 'POST':
            message_text = request.form.get('message', '').strip()
            file = request.files.get('file')
            file_info = None
            if file and file.filename:
                file_info = save_uploaded_file(file, chat_id)
            if message_text or file_info:
                save_message(chat_id, current_user.id, message_text, file_info)
            return redirect(url_for('chat.chat', chat_id=chat_id))

        # Получаем сообщения с вложениями
        messages = get_messages_with_attachments(chat_id, limit=1000, offset=0)
        # Преобразуем для шаблона
        for msg in messages:
            msg['id'] = msg['id_message']
        # Получаем логины отправителей
        senders = get_message_senders(messages, db_sess)
        for msg in messages:
            msg['user'] = senders.get(msg['sender_id'], 'Unknown')
        return render_template(
            'chat.html',
            messages=messages,
            username=current_user.login,
            chat_id=chat_id,
            chat_title=chat_obj.title
        )
    finally:
        db_sess.close()


@chat_bp.route('/chat/<int:chat_id>/download/<int:attachment_id>')
@login_required
def download_file(chat_id, attachment_id):
    # Проверка доступа к чату
    db_sess = db_session.create_session()
    try:
        chat_obj = db_sess.query(Chat).filter(Chat.id == chat_id).first()
        if not chat_obj:
            abort(404)
        member = db_sess.query(ChatMember).filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == current_user.id
        ).first()
        if not member:
            abort(403)
    finally:
        db_sess.close()

    db_path = get_chat_db_path(chat_id)
    if not db_path or not os.path.exists(db_path):
        abort(404)

    import sqlite3
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT file_path, file_name FROM attachments WHERE id = ?",
            (attachment_id,)
        )
        att = cur.fetchone()
        if not att:
            abort(404)

    # Преобразуем относительный путь в абсолютный
    abs_path = os.path.join(current_app.root_path, att['file_path'])
    if not os.path.exists(abs_path):
        abort(404)

    return send_file(abs_path, as_attachment=True, download_name=att['file_name'])


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