from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user

from data import db_session
from data.users import User
from data.chats import Chat
from data.chat_members import ChatMember


edit_chat_bp = Blueprint('edit_chat', __name__)


@edit_chat_bp.route('/edit_chat/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def edit_chat(chat_id):
    db_sess = db_session.create_session()

    # ищем чат по id
    chat = db_sess.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        db_sess.close()
        return 'Чат не найден', 404

    # проверяем, что текущий пользователь состоит в этом чате
    current_member = db_sess.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id).first()

    if not current_member:
        db_sess.close()
        return 'У вас нет доступа к этому чату'

    # групповой чат редактирует только создатель
    if chat.is_group and chat.owner_id != current_user.id:
        db_sess.close()
        return 'Редактировать групповой чат может только создатель'

    if request.method == 'POST':
        title = request.form.get('title', '').strip()

        if not title:
            members = get_chat_users(db_sess, chat_id)
            db_sess.close()
            return render_template('edit_chat.html', chat=chat,
                                   members=members,
                                   errors=['Название чата обязательно'])

        chat.title = title

        # в личном чате можно менять только название
        if not chat.is_group:
            db_sess.commit()
            db_sess.close()
            return redirect(url_for('chats_list.chats'))

        logins = request.form.getlist('logins')
        logins = [login.strip() for login in logins if login.strip()]

        owner = db_sess.query(User).filter(User.id == chat.owner_id).first()

        # создатель всегда остаётся в группе
        if owner.login not in logins:
            logins.append(owner.login)

        users = db_sess.query(User).filter(User.login.in_(logins)).all()
        existing_logins = {user.login for user in users}
        missing_logins = set(logins) - existing_logins

        if missing_logins:
            members = get_chat_users(db_sess, chat_id)
            errors = [f"Пользователь '{login}' не найден" for login in missing_logins]
            db_sess.close()
            return render_template('edit_chat.html', chat=chat,
                                   members=members, errors=errors)

        if len(users) < 3:
            members = get_chat_users(db_sess, chat_id)
            db_sess.close()
            return render_template('edit_chat.html', chat=chat,
                                   members=members,
                                   errors=['В групповом чате должно быть минимум 3 участника'])

        # заменяем старый список участников новым
        db_sess.query(ChatMember).filter(ChatMember.chat_id == chat_id).delete()

        for user in users:
            member = ChatMember(chat_id=chat_id, user_id=user.id)
            db_sess.add(member)

        db_sess.commit()
        db_sess.close()

        return redirect(url_for('chats_list.chats'))

    members = get_chat_users(db_sess, chat_id)
    db_sess.close()

    return render_template('edit_chat.html', chat=chat, members=members)


def get_chat_users(db_sess, chat_id):
    # получаем пользователей, которые состоят в чате
    members = db_sess.query(ChatMember).filter(ChatMember.chat_id == chat_id).all()
    user_ids = [member.user_id for member in members]

    if not user_ids:
        return []

    return db_sess.query(User).filter(User.id.in_(user_ids)).all()