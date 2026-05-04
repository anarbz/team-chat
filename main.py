from flask import Flask, render_template, request, redirect, url_for
from data import db_session
from chat.chat_work import chat_bp
from data.users import User
from data.chats import Chat
from data.chat_members import ChatMember
from chat.chat_service import create_chat

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
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        chat_id_str = request.form.get('chat_id', '').strip()
        if not username or not chat_id_str:
            return "Имя и ID чата обязательны", 400
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            return "ID чата должен быть числом", 400

        db_sess = db_session.create_session()

        user = db_sess.query(User).filter(User.login == username).first()
        if not user:
            user = User(login=username)
            db_sess.add(user)
            db_sess.commit()

        chat_id = create_chat_with_id(chat_id, title=f"Chat {chat_id}", is_group=True)

        membership = db_sess.query(ChatMember).filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id == user.id
        ).first()
        db_sess.close()
        if not membership:
            return "У вас нет доступа к этому чату", 403

        db_sess.close()
        return redirect(url_for('chat.chat', chat_id=chat_id, username=username))

    return render_template('index.html')


@app.route('/create_chat', methods=['GET', 'POST'])
def create_chat_route():
    db_sess = db_session.create_session()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        members_str = request.form.get('members', '').strip()
        if not title or not members_str:
            return "Название и участники обязательны", 400

        logins = [login.strip() for login in members_str.split(',') if login.strip()]
        if not logins:
            return "Укажите хотя бы одного участника", 400

        users = db_sess.query(User).filter(User.login.in_(logins)).all()
        if len(users) != len(logins):
            missing = set(logins) - {u.login for u in users}
            return f"Пользователи не найдены: {', '.join(missing)}", 400

        chat = create_chat(title, is_group=True)
        for user in users:
            member = ChatMember(chat_id=chat.id, user_id=user.id)
            db_sess.add(member)
        db_sess.commit()
        return redirect(url_for('index'))

    return render_template('create_chat.html')


def main():
    db_session.global_init("db/team_chat.db")
    app.run(debug=True)

if __name__ == '__main__':
    main()