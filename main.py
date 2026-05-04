from flask import Flask, render_template, request, redirect, url_for
from data import db_session
from chat.chat_work import chat_bp
from data.users import User
from data.chats import Chat
from data.chat_members import ChatMember
from chat.chat_service import create_chat
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secretkey_123'
app.register_blueprint(chat_bp)


def create_chat_with_id(chat_id, title, is_group=True):
    """Создаёт чат с заданным id, если его нет. Возвращает id чата."""
    db_sess = db_session.create_session()
    existing = db_sess.query(Chat).filter(Chat.id == chat_id).first()
    if existing:
        cid = existing.id
        db_sess.close()
        return cid

    chat = Chat(id=chat_id, title=title, is_group=is_group, messages_db_path="")
    db_sess.add(chat)
    db_sess.commit()

    db_dir = "db/chats"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, f"chat_{chat.id}.db")
    chat.messages_db_path = db_path
    db_sess.commit()

    from chat.chat_service import init_chat_messages_db
    init_chat_messages_db(db_path)
    db_sess.close()
    return chat.id


@app.route('/', methods=['GET', 'POST'])
def index():
    success_message = None
    error_message = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'register':
            login = request.form.get('reg_username', '').strip()
            password = request.form.get('reg_password', '').strip()
            if not login or not password:
                error_message = "Логин и пароль обязательны"
            else:
                db_sess = db_session.create_session()
                try:
                    existing = db_sess.query(User).filter(User.login == login).first()
                    if existing:
                        error_message = "Пользователь уже существует"
                    else:
                        user = User(login=login, hashed_password=generate_password_hash(password))
                        db_sess.add(user)
                        db_sess.commit()
                        success_message = f"Пользователь '{login}' успешно зарегистрирован! Теперь войдите в чат."
                finally:
                    db_sess.close()

        elif action == 'login':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            chat_id_str = request.form.get('chat_id', '').strip()
            if not username or not password or not chat_id_str:
                return "Все поля обязательны", 400
            try:
                chat_id = int(chat_id_str)
            except ValueError:
                return "ID чата должен быть числом", 400

            db_sess = db_session.create_session()
            try:
                user = db_sess.query(User).filter(User.login == username).first()
                if not user or not check_password_hash(user.hashed_password, password):
                    return "Неверный логин или пароль", 403

                membership = db_sess.query(ChatMember).filter(
                    ChatMember.chat_id == chat_id,
                    ChatMember.user_id == user.id
                ).first()
            finally:
                db_sess.close()

            if not membership:
                return "У вас нет доступа к этому чату", 403

            return redirect(url_for('chat.chat', chat_id=chat_id, username=username))

    return render_template('index.html', success_message=success_message, error_message=error_message)


@app.route('/create_chat', methods=['GET', 'POST'])
def create_chat_route():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        logins = request.form.getlist('logins')
        logins = [login.strip() for login in logins if login.strip()]

        if not title or not logins:
            errors = ["Название чата обязательно"] if not title else ["Укажите хотя бы одного участника"]
            return render_template('create_chat.html', errors=errors)

        db_sess = db_session.create_session()
        try:
            users = db_sess.query(User).filter(User.login.in_(logins)).all()
            existing_logins = {u.login for u in users}
            missing_logins = set(logins) - existing_logins
        finally:
            db_sess.close()

        if missing_logins:
            errors = [f"Пользователь '{login}' не найден" for login in missing_logins]
            return render_template('create_chat.html', errors=errors)

        from chat.chat_service import create_chat
        chat_id = create_chat(title, is_group=True)

        db_sess = db_session.create_session()
        try:
            for user in users:
                member = ChatMember(chat_id=chat_id, user_id=user.id)
                db_sess.add(member)
            db_sess.commit()
        finally:
            db_sess.close()

        success_message = f"Чат успешно создан! ID чата: {chat_id}"
        return render_template('create_chat.html', success_message=success_message)

    return render_template('create_chat.html')


def main():
    db_session.global_init("db/team_chat.db")
    app.run(debug=True)

if __name__ == '__main__':
    main()