from flask import Blueprint, render_template, request, redirect, url_for, abort, send_from_directory
from flask_login import login_required, current_user
import os
from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from utils.chat_db_utils import get_chat_db_path
from services.message_operations import save_message, get_messages_with_attachments
from utils.file_utils import save_uploaded_file
from werkzeug.utils import secure_filename
from flask import current_app
from data.users import User

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
            uploaded_file = request.files.get('file')
            file_info = None
            if uploaded_file and uploaded_file.filename != '':
                file_info = save_uploaded_file(uploaded_file, chat_id)

            if message_text or file_info:
                save_message(chat_id, current_user.id, message_text or "", file_info)

            return redirect(url_for('chat.chat', chat_id=chat_id))

        messages = get_messages_with_attachments(chat_id, limit=100)

        sender_ids = {msg['sender_id'] for msg in messages}
        users_map = {}
        if sender_ids:
            users_from_db = db_sess.query(User).filter(User.id.in_(sender_ids)).all()
            users_map = {u.id: u.login for u in users_from_db}

        for msg in messages:
            msg['user'] = users_map.get(msg['sender_id'], 'Unknown')

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
            attachment = cur.fetchone()
        if not attachment:
            abort(404)

        file_path = attachment['file_path']
        file_name = attachment['file_name']

        absolute_path = os.path.join(current_app.root_path, file_path)
        directory = os.path.dirname(absolute_path)
        filename = os.path.basename(absolute_path)
        return send_from_directory(directory, filename, as_attachment=True, download_name=file_name)
    finally:
        db_sess.close()