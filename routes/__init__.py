from .auth import auth_bp
from .dashboard import dashboard_bp
from .enter import enter_bp
from .chat_routes import chat_bp
from .chats_list import chats_list_bp
from .edit_chat import edit_chat_bp

__all__ = ['auth_bp', 'dashboard_bp', 'enter_bp', 'chat_bp', 'chats_list_bp',
           'edit_chat_bp']
