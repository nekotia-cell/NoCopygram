# из папки games/dice

import asyncio
import random
from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.middlewares.antispam import antispam
from database.models import UserDB
from assets.emojis import WIN_EMOJIS, LOSS_EMOJIS

from utils.userhelpers import ensure_user_exists

@dp.message(F.text.lower().startswith("кубы"))
@antispam
async def handle_cube_game(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )

    if UserDB.is_blocked(user_id):
        return

    try:
        _, stake_str, predicted_number_str = message.text.split()
        stake = int(stake_str)
        predicted_number = int(predicted_number_str)

        if stake <= 0:
            await message.reply(f"{user_link}, Ставка должна быть положительным числом.", parse_mode=ParseMode.HTML)
            return

        if not 1 <= predicted_number <= 6:
            await message.reply(f"{user_link}, Число должно быть от 1 до 6.", parse_mode=ParseMode.HTML)
            return

        if stake <= 99:
            await message.reply(f"{user_link}, Минимальная ставка 100 Кото-грамм", parse_mode=ParseMode.HTML)
            return

        balance = UserDB.get_balance(user_id)

        if stake > balance:
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return

        if not UserDB.debit(user_id, stake):
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return

        dice_message = await message.answer_dice(emoji='🎲')
        dice_value = dice_message.dice.value
        await asyncio.sleep(2.5)

        if dice_value == predicted_number:
            winnings = stake * 2
            UserDB.update_balance(user_id, winnings)
            random_win_emoji = random.choice(WIN_EMOJIS)
            result_message = (
                f"<b>{user_link}, Поздравляем! {random_win_emoji}</b>\n\n"
                f"🎲 Выпало: {dice_value}\n"
                f"✅ Вы выиграли: +{winnings} Кото-грамм!"
            )
        else:
            random_loss_emoji = random.choice(LOSS_EMOJIS)
            result_message = (
                f"<b>{user_link}, К сожалению, вы не угадали {random_loss_emoji}</b>\n\n"
                f"🎲 Выпало: {dice_value}\n"
                f"❌ Вы проиграли: {stake} Кото-грамм."
            )

        await message.reply(result_message, parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(
            f"{user_link}, Неверный формат команды. Используйте: кубы <ставка> <число от 1 до 6>.",
            parse_mode=ParseMode.HTML
        )
