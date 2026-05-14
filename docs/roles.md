# Даша Родичева (пользователи и доступ)
- модель User; 
- регистрация; 
- вход 
- выход
- хеширование паролей;
- проверка уникальности логина и email; 
- работа с текущим пользователем - current user
- базовая защита страниц от неавторизованного доступа.
- сессии
- основной дизайн 

routes/auth, data/user, forms/user, static/css/css.style
templates/base, templates/index, templates/login, templates/register



# Анар Байрамов (чаты и участники)
- модель Chat; 
- модель ChatMember;
- создание группового чата
- создание личного чата
- генерацию отдельного файла БД для нового чата
- сохранение пути к БД сообщений
- добавление участников в чат
- список чатов пользователя
- список участников чата

routes/chat_members, routes/chat_list, routes/delete_chat, routes/edit_chat, routes/chat_routes(только download_file), services/chat_creation, services/message_operations(только get_messages_with_attachments), data/db_session, data/chats, data/chat_members

templates: chat_members, chats, create_chat, edit_chat
# Эрвин Семизаров (сообщения)
- модуль работы с сообщениями
- модель Message для базы конкретного чата
- подключение к нужной БД сообщений по пути
- загрузку сообщений конкретного чата
- отправку сообщений
- вывод истории сообщений
- удаление сообщений 
- редактирование сообщений
- вложения

routes/dashboard, routes/enter, routes/chat_routes, routes/init.py
services/chat_creation (только create_full_chat), services/message_operations,
utils/init.py, utils/chat_db_utils, utils/file_utils, reset_db

templates: chat, dashboard

