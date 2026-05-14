import os
import shutil
import sys


def reset_all():
    db_dir = "db"
    chats_dir = os.path.join(db_dir, "chats")

    main_db = os.path.join(db_dir, "team_chat.db")
    if os.path.exists(main_db):
        os.remove(main_db)

    if os.path.exists(chats_dir):
        shutil.rmtree(chats_dir)

    os.makedirs(chats_dir, exist_ok=True)


if __name__ == "__main__":
    reset_all()
