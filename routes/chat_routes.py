import os
import sqlite3
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, abort, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from data.users import User
from utils.chat_db_utils import get_chat_db_path
from services.message_operations import (
    save_message,
    get_messages_with_attachments,
    get_message_senders,
    edit_message,
    delete_message
)

chat_bp = Blueprint('chat', __name__, template_folder='../templates')

# Конфигурация для загруженных файлов
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'doc', 'docx', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

        # Обработка POST – отправка сообщения (с файлом или без)
        if request.method == 'POST':
            message_text = request.form.get('message', '').strip()
            uploaded_file = request.files.get('file')

            file_info = None
            if uploaded_file and uploaded_file.filename != '' and allowed_file(uploaded_file.filename):
                filename = secure_filename(uploaded_file.filename)
                # Папка для файлов конкретного чата
                chat_upload_dir = os.path.join(UPLOAD_FOLDER, f'chat_{chat_id}')
                os.makedirs(chat_upload_dir, exist_ok=True)
                file_path = os.path.join(chat_upload_dir, filename)
                uploaded_file.save(file_path)
                file_info = {
                    'file_name': filename,
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'mime_type': uploaded_file.mimetype
                }

            if message_text or file_info:
                save_message(chat_id, current_user.id, message_text, file_info)

            return redirect(url_for('chat.chat', chat_id=chat_id))

        # GET – получение сообщений с вложениями
        messages = get_messages_with_attachments(chat_id)
        senders = get_message_senders(messages, db_sess)  # передаём сессию для оптимизации

        # Формируем список для шаблона
        messages_for_template = []
        for msg in messages:
            messages_for_template.append({
                'id': msg['id_message'],
                'user': senders.get(msg['sender_id'], 'Unknown'),
                'time': msg['time'],
                'message': msg['message'],
                'attachments': msg.get('attachments', [])
            })

        return render_template(
            'chat.html',
            messages=messages_for_template,
            username=current_user.login,
            chat_id=chat_id
        )

    finally:
        db_sess.close()


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


@chat_bp.route('/chat/<int:chat_id>/delete_message/<int:message_id>', methods=['POST'])
@login_required
def delete_message_route(chat_id, message_id):
    success = delete_message(chat_id, message_id, current_user.id)
    if not success:
        return 'Нельзя удалить чужое сообщение', 403
    return redirect(url_for('chat.chat', chat_id=chat_id))


@chat_bp.route('/download/<int:chat_id>/<int:attachment_id>')
@login_required
def download_file(chat_id, attachment_id):
    # Проверяем, что пользователь состоит в чате
    db_sess = db_session.create_session()
    try:
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

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT file_path, file_name FROM attachments WHERE id = ?",
            (attachment_id,)
        )
        att = cur.fetchone()
        if not att:
            abort(404)

    return send_file(att['file_path'], as_attachment=True, download_name=att['file_name'])