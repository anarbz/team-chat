from flask import render_template, redirect, url_for, request, Blueprint
from flask_login import login_user, logout_user, login_required
from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm

auth_bp = Blueprint('auth', __name__, template_folder='../templates')


@auth_bp.route('/', methods=['GET', 'POST'])
def index():
    login_form = LoginForm()
    register_form = RegisterForm()

    if request.method == 'POST' and 'login_submit' in request.form:
        if login_form.validate_on_submit():
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.email == login_form.email.data).first()
            if user and user.check_password(login_form.password.data):
                login_user(user, remember=login_form.remember_me.data)
                db_sess.close()
                return redirect(url_for('dashboard.dashboard'))
            else:
                message = 'Неправильный email или пароль'
                db_sess.close()
                return render_template('index.html', login_form=login_form, register_form=register_form,
                                       message=message)

    if request.method == 'POST' and 'register_submit' in request.form:
        if register_form.validate_on_submit():
            db_sess = db_session.create_session()
            existing_user = db_sess.query(User).filter(User.email == register_form.email.data).first()
            if existing_user:
                db_sess.close()
                return render_template('index.html', login_form=login_form, register_form=register_form,
                                       reg_message='Пользователь с таким email уже существует')

            existing_login = db_sess.query(User).filter(User.login == register_form.login.data).first()
            if existing_login:
                db_sess.close()
                return render_template('index.html', login_form=login_form, register_form=register_form,
                                       reg_message='Такой логин уже занят')

            user = User(login=register_form.login.data, email=register_form.email.data)
            user.set_password(register_form.password.data)
            db_sess.add(user)
            db_sess.commit()
            login_user(user, remember=False)
            db_sess.close()
            return redirect(url_for('dashboard.dashboard'))

    return render_template('index.html', login_form=login_form, register_form=register_form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            db_sess.close()
            return redirect(url_for('dashboard.dashboard'))
        db_sess.close()
        return render_template('login.html', title='Авторизация', form=form,
                               message='Неправильный логин или пароль')
    return render_template('login.html', title='Авторизация', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        existing_user = db_sess.query(User).filter(User.email == form.email.data).first()
        if existing_user:
            db_sess.close()
            return render_template('register.html', title='Регистрация', form=form,
                                   message='Пользователь с таким email уже существует')

        existing_login = db_sess.query(User).filter(User.login == form.login.data).first()
        if existing_login:
            db_sess.close()
            return render_template('register.html', title='Регистрация', form=form,
                                   message='Такой логин уже занят')

        user = User(login=form.login.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        login_user(user, remember=False)
        db_sess.close()
        return redirect(url_for('dashboard.dashboard'))
    return render_template('register.html', title='Регистрация', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.index'))
