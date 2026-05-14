import os
from flask import Flask
from flask_login import LoginManager
from data import db_session
from data.users import User
from routes import (auth_bp, dashboard_bp, enter_bp, chat_bp,
                    chats_list_bp, edit_chat_bp, delete_chat_bp,
                    chat_members_bp, api_bp)

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'my-super-secretkey_123'

    db_session.global_init("db/team_chat.db")

    login_manager.init_app(app)
    login_manager.login_view = 'auth.index'

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(enter_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(chats_list_bp)
    app.register_blueprint(edit_chat_bp)
    app.register_blueprint(delete_chat_bp)
    app.register_blueprint(chat_members_bp)
    app.register_blueprint(api_bp)

    return app


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, int(user_id))
    db_sess.close()
    return user


def main():
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
