import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "uploads/chats"

def get_chat_upload_dir(chat_id: int) -> str:
    path = os.path.join(current_app.root_path, UPLOAD_FOLDER, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path

def save_uploaded_file(file, chat_id: int) -> dict:
    if not file:
        return None
    original_name = secure_filename(file.filename)
    unique_id = uuid.uuid4().hex
    ext = os.path.splitext(original_name)[1]
    stored_name = f"{unique_id}{ext}"
    upload_dir = get_chat_upload_dir(chat_id)
    stored_path = os.path.join(upload_dir, stored_name)
    file.save(stored_path)
    return {
        'file_name': original_name,
        'file_path': os.path.relpath(stored_path, current_app.root_path).replace("\\", "/"),
        'file_size': os.path.getsize(stored_path),
        'mime_type': file.mimetype or 'application/octet-stream'
    }