import sqlalchemy
from datetime import datetime
from .db_session import SqlAlchemyBase


class Chat(SqlAlchemyBase):
    __tablename__ = 'chats'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    is_group = sqlalchemy.Column(sqlalchemy.Boolean, default=True) # для группового чата
    owner_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'),
                                 nullable=False)
    messages_db_path = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.now)