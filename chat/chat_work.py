from flask import Blueprint, render_template, request, redirect, url_for
import datetime
from chat.test_bd_work import init_db, add_message, get_messages

# Создаём блюпринт для чата
chat_bp = Blueprint('chat', __name__)

# При первом импорте гарантируем существование таблицы
init_db()

@chat_bp.route('/chat/<chat_id>/<username>', methods=['GET', 'POST'])
def chat(chat_id, username):
    # Обработка отправки сообщения
    if request.method == 'POST':
        message_text = request.form.get('message', '').strip()
        if message_text:
            # Сохраняем сообщение с текущим временем
            now = datetime.datetime.now()
            add_message(username, message_text, now)
        # После отправки перенаправляем на ту же страницу (методом GET)
        return redirect(url_for('chat.chat', chat_id=chat_id, username=username))

    # Получаем все сообщения из БД
    messages = get_messages()
    # Преобразуем время в строку для отображения (если требуется)
    # В get_messages возвращаются Row объекты, можно обращаться по ключам
    return render_template('chat.html', messages=messages, username=username, chat_id=chat_id)