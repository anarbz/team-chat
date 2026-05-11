from flask import request, redirect, url_for, Blueprint
from flask_login import login_required, current_user
from data import db_session
from data.chat_members import ChatMember

enter_bp = Blueprint('enter', __name__)


@enter_bp.route('/enter_chat', methods=['POST'])
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

    return redirect(url_for('chat.chat', chat_id=chat_id, username=current_user.login))