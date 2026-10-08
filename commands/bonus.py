import random
import time
from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.middlewares.antispam import antispam
from database.models import UserDB
from utils.text import gram_declension, time_declension
from users.vip import is_vip, get_vip_prefix
from utils.user_helpers import ensure_user_exists

@dp.message(F.text.lower() == "бонус")
@antispam
async def handle_bonus_command(message: Message):
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )
    current_time = time.time()

    if UserDB.is_blocked(user_id):
        return

    ensure_user_exists(message)

    max_balance_for_bonus = 8000 if is_vip(user_id) else 5000
    vip_prefix = get_vip_prefix(user_id)

    balance = UserDB.get_balance(user_id)
    if balance > max_balance_for_bonus:
        await message.reply(
            f"{vip_prefix}{user_link}, Бонус доступен только при балансе меньше {max_balance_for_bonus}",
            parse_mode=ParseMode.HTML
        )
        return

    bonus_timer = UserDB.get_bonus_timer(user_id)
    if current_time - bonus_timer < 24 * 3600:
        time_left = 24 * 3600 - (current_time - bonus_timer)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        hours_declension = time_declension(hours, "час")
        minutes_declension = time_declension(minutes, "минут")

        await message.reply(
            f"{vip_prefix}{user_link}, Вы сможете получить бонус только через {hours} {hours_declension} и {minutes} {minutes_declension} ⏳\n\n<blockquote><b><i>BOT IN BETA-TEST</i></b></blockquote>",
            parse_mode=ParseMode.HTML
        )
    else:
        if is_vip(user_id):
            bonus_amount = random.randint(700, 1000)
        else:
            bonus_amount = random.randint(300, 600)

        UserDB.update_balance(user_id, bonus_amount)
        UserDB.set_bonus_timer(user_id, current_time)
        declension = gram_declension(bonus_amount)

        await message.reply(
            f"🤑 {vip_prefix}{user_link}Поздравляю! Тебе начислено {bonus_amount} {declension}!\n\n<blockquote><b><i>BOT IN BETA-TEST</i></b></blockquote>",
            parse_mode=ParseMode.HTML
        )
