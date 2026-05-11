from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from data import db_session
from data.users import User
from data.chat_members import ChatMember
from services.chat_creation import create_chat

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """список чатов будет добавлен позже ДОБАВЬТЕ ЕГО ГОСПОДИ ИИСУСЕ"""
    return render_template('dashboard.html')


@dashboard_bp.route('/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat_route():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        logins = request.form.getlist('logins')
        logins = [login.strip() for login in logins if login.strip()]

        if not title or not logins:
            errors = ['Название чата обязательно'] if not title else ['Укажите хотя бы одного участника']
            return render_template('create_chat.html', errors=errors)

        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.login.in_(logins)).all()
        existing_logins = {u.login for u in users}
        missing_logins = set(logins) - existing_logins

        if missing_logins:
            errors = [f"Пользователь '{login}' не найден" for login in missing_logins]
            return render_template('create_chat.html', errors=errors)

        chat_id = create_chat(title, is_group=True)

        creator_already_added = current_user.login in existing_logins
        if not creator_already_added:
            users.append(current_user)

        for user in users:
            exists = db_sess.query(ChatMember).filter(
                ChatMember.chat_id == chat_id,
                ChatMember.user_id == user.id
            ).first()
            if not exists:
                member = ChatMember(chat_id=chat_id, user_id=user.id)
                db_sess.add(member)

        db_sess.commit()

        success_message = f"Чат успешно создан! ID чата: {chat_id}"
        return render_template('create_chat.html', success_message=success_message)

    return render_template('create_chat.html')