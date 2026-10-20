import random
import time
from aiogram.types import Message
from aiogram import F
from aiogram.filters import CommandStart
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.middlewares.antispam import antispam
from database.models import UserDB
from utils.text import gram_declension, time_declension
from users.vip import is_vip, get_vip_prefix
from utils.userhelpers import ensure_user_exists
from utils.formatters import format_balance
from core.bot import bot


def bonus_is_available(user_id: int) -> bool:
    max_balance_for_bonus = 8000 if is_vip(user_id) else 5000
    return (
        UserDB.get_balance(user_id) <= max_balance_for_bonus
        and time.time() - UserDB.get_bonus_timer(user_id) >= 24 * 3600
    )


async def get_bonus_deep_link() -> str:
    bot_user = await bot.me()
    return f"https://t.me/{bot_user.username}?start=bonus"


@dp.message(CommandStart(deep_link=True))
async def handle_bonus_deep_link(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) == 2 and parts[1].strip().lower() == "bonus":
        await handle_bonus_command(message)

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
            f"{vip_prefix}{user_link}, Бонус доступен только при балансе меньше {format_balance(max_balance_for_bonus)}",
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

        if not UserDB.claim_bonus(user_id, bonus_amount, current_time, 24 * 3600):
            await message.reply(
                f"{vip_prefix}{user_link}, бонус уже был получен другим запросом или еще недоступен.",
                parse_mode=ParseMode.HTML,
            )
            return
        declension = gram_declension(bonus_amount)

        await message.reply(
            f"🤑 {vip_prefix}{user_link}Поздравляю! Тебе начислено {format_balance(bonus_amount)} {declension}!\n\n<blockquote><b><i>BOT IN BETA-TEST</i></b></blockquote>",
            parse_mode=ParseMode.HTML
        )
