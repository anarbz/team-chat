from flask import Blueprint, render_template
from flask_login import login_required, current_user

from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember


chats_list_bp = Blueprint('chats_list', __name__)


@chats_list_bp.route('/chats')
@login_required
def chats():
    # получаем все чаты текущего пользователя
    db_sess = db_session.create_session()

    memberships = db_sess.query(ChatMember).filter(
        ChatMember.user_id == current_user.id).all()

    chat_ids = [membership.chat_id for membership in memberships]

    if chat_ids:
        user_chats = db_sess.query(Chat).filter(Chat.id.in_(chat_ids)).all()
    else:
        user_chats = []

    # кол-во участников на чат
    member_counts = {}
    for chat in user_chats:
        count = db_sess.query(ChatMember).filter(
            ChatMember.chat_id == chat.id).count()
        member_counts[chat.id] = count

    db_sess.close()

    return render_template('chats.html',
                           chats=user_chats,
                           title='Мои чаты',
                           member_counts=member_counts)
