from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm
from routes import auth_bp, dashboard_bp, enter_bp, chat_bp, chats_list_bp, edit_chat_bp, delete_chat_bp, chat_members_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandex_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

@app.route('/')
def index():
    return render_template('base.html', title='Главная')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        # Проверка, нет ли уже такого пользователя
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form, message="Такой пользователь уже есть")

        user = User(login=form.login.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='Мой профиль')


def main():
    db_session.global_init("db/team_chat.db")

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(enter_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(chats_list_bp)
    app.register_blueprint(edit_chat_bp)
    app.register_blueprint(delete_chat_bp)
    app.register_blueprint(chat_members_bp)

    app.run(port=8080, host='127.0.0.1')

if __name__ == '__main__':
    main()