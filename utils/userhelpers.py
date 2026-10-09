# utils/user_helpers.py
from database.models import UserDB
import datetime
import pytz
from config import TIMEZONE

def ensure_user_exists(message):
    """Создаёт пользователя в БД если его нет"""
    user_id = message.from_user.id
    if not UserDB.get(user_id):
        now = datetime.datetime.now(pytz.utc).astimezone(TIMEZONE)
        UserDB.create(
            user_id=user_id,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            registration_date=now.strftime("%d.%m.%Y в %H:%M:%S")
        )
        return True
    return False