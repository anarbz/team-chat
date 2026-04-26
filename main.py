from flask import Flask, render_template
from data import db_session
from data.users import User
from data.messages import Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-super-secretkey_123'


@app.route('/')
def index():
    # основная стрница - вывод всех пользователей из бд
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    return render_template('index.html', users=users)


@app.route('/chat')
def chat():
    # страница чата - пока что все сообщения в куче - общий чат
    db_sess = db_session.create_session()
    messages = db_sess.query(Message).all()
    return render_template('chat.html', messages=messages)


def main():
    db_session.global_init("db/team_chat.db")
    app.run()


if __name__ == '__main__':
    main()
