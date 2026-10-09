from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.bot import bot
from core.middlewares.antispam import antispam
from database.models import UserDB
from assets.emojis import PLACE_EMOJIS
from utils.text import gram_declension
from utils.formatters import format_balance
from users.vip import get_vip_prefix

from utils.userhelpers import ensure_user_exists

@dp.message(F.text.lower().startswith((
    "топ грам",
    "грам топ",
    "грамм топ",
    "топ грамм"
)))
@antispam
async def handle_top_gram_message(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id

    if UserDB.is_blocked(user_id):
        return

    try:
        parts = message.text.split()
        if len(parts) > 2:
            num_to_show = int(parts[2])
            if num_to_show < 10:
                num_to_show = 10
            elif num_to_show > 50:
                num_to_show = 50
        else:
            num_to_show = 10
    except (ValueError, IndexError):
        num_to_show = 10

    users = UserDB.get_top(num_to_show, min_balance=100000)

    top_users_text = f"<b>🏆 Топ {num_to_show} богачей по Кото-граммам во всем боте</b>\n\n"

    if not users:
        top_users_text = "Никто не накопил больше 100.000 Кото-грамм"
    else:
        for i, user in enumerate(users):
            username = user.get('first_name', f"User {user['user_id']}")
            vip_prefix = get_vip_prefix(user['user_id'])
            formatted_balance = format_balance(user['balance'])
            declension = gram_declension(user['balance'])
            top_users_text += f"{PLACE_EMOJIS[i]}. {vip_prefix}<b>{username}</b>: <code>{formatted_balance}</code> {declension}\n"

    await message.answer(top_users_text, parse_mode=ParseMode.HTML)
