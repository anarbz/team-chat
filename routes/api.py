from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user

from data import db_session
from data.chats import Chat
from data.chat_members import ChatMember
from data.users import User
from services.message_operations import save_message, get_messages_with_attachments, get_message_senders

api_bp = Blueprint('api', __name__)


def json_error(message, status_code):
    return make_response(jsonify({'error': message}), status_code)


def chat_to_dict(chat):
    return {
        'id': chat.id,
        'title': chat.title,
        'is_group': chat.is_group,
        'owner_id': chat.owner_id,
        'created_date': str(chat.created_date)
    }


def check_chat_access(db_sess, chat_id):
    if not current_user.is_authenticated:
        return None, json_error('Unauthorized', 401)

    chat = db_sess.get(Chat, chat_id)
    if not chat:
        return None, json_error('Not found', 404)

    member = db_sess.query(ChatMember).filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id == current_user.id
    ).first()

    if not member:
        return None, json_error('Forbidden', 403)

    return chat, None


@api_bp.route('/api/chats', methods=['GET'])
def get_chats():
    if not current_user.is_authenticated:
        return json_error('Unauthorized', 401)

    db_sess = db_session.create_session()
    try:
        memberships = db_sess.query(ChatMember).filter(
            ChatMember.user_id == current_user.id
        ).all()
        chat_ids = [membership.chat_id for membership in memberships]
        chats = db_sess.query(Chat).filter(Chat.id.in_(chat_ids)).all() if chat_ids else []
        return jsonify({'chats': [chat_to_dict(chat) for chat in chats]})
    finally:
        db_sess.close()


@api_bp.route('/api/chats/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    db_sess = db_session.create_session()
    try:
        chat, error = check_chat_access(db_sess, chat_id)
        if error:
            return error

        messages = get_messages_with_attachments(chat.id, limit=100, offset=0)
        senders = get_message_senders(messages, db_sess)

        return jsonify({
            'messages': [
                {
                    'id': message['id_message'],
                    'sender_id': message['sender_id'],
                    'sender': senders.get(message['sender_id'], 'Unknown'),
                    'message': message['message'],
                    'time': str(message['time']),
                    'attachments': [
                        {
                            'id': attachment['id'],
                            'file_name': attachment['file_name'],
                            'file_size': attachment['file_size'],
                            'mime_type': attachment['mime_type']
                        }
                        for attachment in message.get('attachments', [])
                    ]
                }
                for message in messages
            ]
        })
    finally:
        db_sess.close()
