import sqlalchemy
from .db_session import SqlAlchemyBase

# какие пользователи состоят в чате
class ChatMember(SqlAlchemyBase):
    __tablename__ = 'chat_members'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('chats.id'),
                                nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('users.id'),
                                nullable=False)
