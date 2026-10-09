# из папки games/basketball

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

@dp.message(F.text.lower().startswith("баскет"))
@antispam
async def handle_basketball_game(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )

    if UserDB.is_blocked(user_id):
        return

    try:
        _, stake_str = message.text.split()
        stake = int(stake_str)

        if stake <= 0:
            await message.reply(f"{user_link}, Ставка должна быть положительным числом.", parse_mode=ParseMode.HTML)
            return

        if stake <= 99:
            await message.reply(f"{user_link}, Минимальная ставка 100 Кото-грамм", parse_mode=ParseMode.HTML)
            return

        balance = UserDB.get_balance(user_id)

        if stake > balance:
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return

        UserDB.update_balance(user_id, -stake)

        dice_message = await message.answer_dice(emoji='🏀')
        dice_value = dice_message.dice.value
        await asyncio.sleep(3.5)

        if dice_value in [1, 2]:
            loss_emoji = random.choice(LOSS_EMOJIS)
            result_message = (
                f"<b>К сожелению вы не попали {loss_emoji}</b>\n\n"
                f"❌ Вы проиграли: {stake} Кото-грамм."
            )
        elif dice_value == 3:
            win_emoji = random.choice(WIN_EMOJIS)
            refund = int(stake * 0.5)
            UserDB.update_balance(user_id, refund)
            result_message = (
                f"<b>Оу, Ну это было близко! 😧</b>\n\n"
                f"{win_emoji} Вам возвращено 50% от ставки: {refund} Кото-грамм"
            )
        elif dice_value == 4:
            winnings = stake * 2
            UserDB.update_balance(user_id, winnings)
            two_pointer_replies = [
                "Двухочковый!",
                "МАЛАДЕЦ",
                "Да ты снайпер"
            ]
            result_message = (
                f"<b>{random.choice(two_pointer_replies)} 🏀</b>\n\n"
                f"✅ Вы выиграли: +{winnings} Кото-грамм! (ваша ставка * 2)"
            )
        elif dice_value == 5:
            winnings = int(stake * 2.5)
            UserDB.update_balance(user_id, winnings)
            three_pointer_replies = [
                "Трехочковый!",
                "Почти девятка йоу",
                "Да ты снайпер! Точно в цель",
                "ОДААА",
                "МАЛАДЕЦ"
            ]
            result_message = (
                f"<b>{random.choice(three_pointer_replies)} 🏀</b>\n\n"
                f"✅ Вы выиграли: +{winnings} Кото-грамм!"
            )
        else:
            result_message = "Неизвестный результат"

        await message.reply(f"{user_link}, {result_message}", parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(
            f"{user_link}, Неверный формат команды. Используйте: баскет <ставка>.",
            parse_mode=ParseMode.HTML
        )
