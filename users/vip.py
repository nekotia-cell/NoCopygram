import time
from config import VIP_PRICE, VIP_DURATION, CROWN_EMOJI
from database.models import UserDB


def is_vip(user_id: int) -> bool:
    expires = UserDB.get_vip_expires(user_id)
    return expires > time.time()


def format_time_left(seconds: float) -> str:
    days = int(seconds // (24 * 3600))
    seconds %= (24 * 3600)
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)

    time_str = ""
    if days > 0:
        time_str += f"{days} дн.\n"
    if hours > 0:
        time_str += f"{hours} ч.\n"
    if minutes > 0:
        time_str += f"{minutes} мин."

    return time_str.strip()


def get_vip_prefix(user_id: int) -> str:
    return CROWN_EMOJI if is_vip(user_id) else ""


def buy_vip(user_id: int) -> bool:
    if is_vip(user_id):
        return False

    balance = UserDB.get_balance(user_id)
    if balance < VIP_PRICE:
        return False

    UserDB.update_balance(user_id, -VIP_PRICE)
    UserDB.set_vip(user_id, time.time() + VIP_DURATION)
    return True


def get_vip_time_left(user_id: int) -> str:
    if not is_vip(user_id):
        return ""
    expires = UserDB.get_vip_expires(user_id)
    return format_time_left(expires - time.time())
