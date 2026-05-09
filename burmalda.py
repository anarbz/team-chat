from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from data import db_session
from data.users import User
from data.chat_members import ChatMember
from chat.chat_work import chat_bp
from chat.chat_service import create_chat
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secretkey_123'

# Подключаем блюпринт чата Эрвина
app.register_blueprint(chat_bp)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, int(user_id))


@app.route('/')
def index():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return render_template('index.html', users=users, current_user=current_user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        existing_user = db_sess.query(User).filter(
            User.email == form.email.data
        ).first()

        if existing_user:
            return render_template(
                'register.html',
                title='Регистрация',
                form=form,
                message='Такой пользователь уже есть'
            )

        user = User(
            login=form.login.data,
            email=form.email.data
        )
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        return redirect(url_for('login'))

    return render_template(
        'register.html',
        title='Регистрация',
        form=form
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('index'))

        return render_template(
            'login.html',
            title='Авторизация',
            form=form,
            message='Неправильный логин или пароль'
        )

    return render_template(
        'login.html',
        title='Авторизация',
        form=form
    )


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/enter_chat', methods=['POST'])
@login_required
def enter_chat():
    chat_id_str = request.form.get('chat_id', '').strip()

    if not chat_id_str:
        return 'Укажите ID чата', 400

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return 'ID чата должен быть числом', 400

    db_sess = db_session.create_session()
    membership = db_sess.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()

    if not membership:
        return 'У вас нет доступа к этому чату', 403

    return redirect(url_for(
        'chat.chat',
        chat_id=chat_id,
        username=current_user.login
    ))


@app.route('/create_chat', methods=['GET', 'POST'])
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

        chat = create_chat(title, is_group=True)

        # Добавим самого создателя, если его логина нет в списке
        creator_already_added = current_user.login in existing_logins
        if not creator_already_added:
            users.append(current_user)

        for user in users:
            exists = db_sess.query(ChatMember).filter(
                ChatMember.chat_id == chat.id,
                ChatMember.user_id == user.id
            ).first()
            if not exists:
                member = ChatMember(chat_id=chat.id, user_id=user.id)
                db_sess.add(member)

        db_sess.commit()

        success_message = f"Чат успешно создан! ID чата: {chat.id}"
        return render_template('create_chat.html', success_message=success_message)

    return render_template('create_chat.html')


def main():
    db_session.global_init("db/team_chat.db")
    app.run(debug=True)


if __name__ == '__main__':
    main()