from flask import Flask, render_template
from data import db_session
from chat.chat_work import chat_bp
from data.users import User
from data.messages import Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secretkey_123'

app.register_blueprint(chat_bp)


@app.route('/')
def index():
    # основная стрница - вывод всех пользователей из бд
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return render_template('index.html', users=users)


def main():
    db_session.global_init("db/team_chat.db")
    app.run()


if __name__ == '__main__':
    main()
