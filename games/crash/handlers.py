# из папки games/crash

import math
from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.bot import bot
from core.middlewares.antispam import antispam
from database.models import UserDB
from games.crash.game import get_random_multiplier_with_probabilities

from utils.userhelpers import ensure_user_exists

@dp.message(F.text.lower().startswith("краш"))
@antispam
async def handle_crash_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )
    chat_id = message.chat.id

    if UserDB.is_blocked(user_id):
        return

    try:
        _, stake_str, multiplier_str = message.text.split(" ")
        stake = int(stake_str)
        multiplier = float(multiplier_str)

        if stake <= 0 or multiplier <= 1:
            await message.reply(
                f"{user_link}, Ставка должна быть положительным числом, а множитель больше 1",
                parse_mode=ParseMode.HTML
            )
            return

        if not (1 <= multiplier <= 13):
            await message.reply(f"{user_link}, Множитель должен быть от 1 до 13", parse_mode=ParseMode.HTML)
            return

        balance = UserDB.get_balance(user_id)

        if stake <= 9:
            await message.reply(f"{user_link}, Минимальная ставка 10 Кото-грам", parse_mode=ParseMode.HTML)
            return

        if balance < stake:
            await message.reply(f"{user_link}, Недостаточно Кото-грам на балансе", parse_mode=ParseMode.HTML)
            return

        if not UserDB.debit(user_id, stake):
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе", parse_mode=ParseMode.HTML)
            return

    except ValueError:
        await message.reply("Неверный формат команды. Используйте «краш <ставка> <множитель>»")
        return

    bot_multiplier = get_random_multiplier_with_probabilities(multiplier)
    if bot_multiplier is None:
        await message.reply("Неверный диапазон множителя. Используйте множитель от 1 до 13")
        return

    if bot_multiplier > multiplier:
        payout = stake * multiplier
        payout = math.floor(payout)
        UserDB.update_balance(user_id, payout)

        win_message = f"{user_link}, Игра остановилась на x{bot_multiplier} 📈\n✅ Победа! Ваш приз: +{payout} Кото-грамм"
        await bot.send_message(chat_id, win_message, parse_mode=ParseMode.HTML)
    else:
        loss_message = f"{user_link}, Игра остановилась на x{bot_multiplier} 📈\n❌ Вы проиграли {stake} Кото-грамм"
        await bot.send_message(chat_id, loss_message, parse_mode=ParseMode.HTML)
