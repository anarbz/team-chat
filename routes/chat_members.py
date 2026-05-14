from flask import Blueprint, render_template
from flask_login import login_required, current_user

from data import db_session
from data.chats import Chat
from data.users import User
from data.chat_members import ChatMember

chat_members_bp = Blueprint('chat_members_page', __name__)


@chat_members_bp.route('/chat_members/<int:chat_id>')
@login_required
def chat_members(chat_id):
    db_sess = db_session.create_session()

    # ищем чат
    chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        db_sess.close()
        return 'Чат не найден', 404

    # проверяем, что пользователь состоит в чате
    current_member = db_sess.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id).first()

    if not current_member:
        db_sess.close()
        return 'У вас нет доступа к этому чату'

    members = db_sess.query(User).join(
        ChatMember, User.id == ChatMember.user_id).filter(
        ChatMember.chat_id == chat_id).all()

    db_sess.close()

    return render_template('chat_members.html',
                           chat=chat,
                           members=members,
                           title='Участники чата')
