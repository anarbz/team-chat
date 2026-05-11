import os

from flask import Blueprint, redirect, url_for
from flask_login import login_required, current_user

from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember


delete_chat_bp = Blueprint('delete_chat', __name__)


@delete_chat_bp.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    db_sess = db_session.create_session()

    # ищем чат по id
    chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        db_sess.close()
        return 'Чат не найден'

    # проверяем, что пользователь состоит в чате
    current_member = db_sess.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id).first()

    if not current_member:
        db_sess.close()
        return 'У вас нет доступа к этому чату'

    db_path = chat.messages_db_path

    # удаляем участников чата
    db_sess.query(ChatMember).filter(ChatMember.chat_id == chat_id).delete()

    # удаляем сам чат
    db_sess.delete(chat)
    db_sess.commit()
    db_sess.close()

    # удаляем отдельную бд сообщений чата
    if db_path and os.path.exists(db_path):
        os.remove(db_path)

    return redirect(url_for('chats_list.chats'))