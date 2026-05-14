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
    return render_template('dashboard.html')


@dashboard_bp.route('/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat_route():
    if request.method == 'POST':
        chat_type = request.form.get('chat_type', 'group')
        is_group = chat_type == 'group'

        title = request.form.get('title', '').strip()
        logins = request.form.getlist('logins')
        logins = [login.strip() for login in logins if login.strip()]

        if not title or not logins:
            errors = ['Название чата обязательно'] if not title else ['Укажите хотя бы одного участника']
            return render_template('create_chat.html', errors=errors,
                                   chat_type=chat_type)

        if current_user.login in logins:
            errors = ['Не нужно добавлять себя в участники']
            return render_template('create_chat.html', errors=errors,
                                   chat_type=chat_type)

        if not is_group and len(logins) != 1:
            errors = ['Для личного чата нужен ровно один собеседник']
            return render_template('create_chat.html', errors=errors,
                                   chat_type=chat_type)

        if is_group and len(logins) < 2:
            errors = ['Для группового чата нужно минимум два участника кроме вас']
            return render_template('create_chat.html', errors=errors,
                                   chat_type=chat_type)

        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.login.in_(logins)).all()
        existing_logins = {u.login for u in users}
        missing_logins = set(logins) - existing_logins

        if missing_logins:
            errors = [f"Пользователь '{login}' не найден" for login in missing_logins]
            db_sess.close()
            return render_template('create_chat.html', errors=errors,
                                   chat_type=chat_type)

        chat_id = create_chat(title, current_user.id, is_group=is_group)

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
        db_sess.close()

        return redirect(url_for('chat.chat', chat_id=chat_id))

    chat_type = request.args.get('type', 'group')

    if chat_type not in ['personal', 'group']:
        chat_type = 'group'

    return render_template('create_chat.html', chat_type=chat_type)