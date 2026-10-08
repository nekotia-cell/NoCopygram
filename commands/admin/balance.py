from aiogram.types import Message
from aiogram import F

from core.dispatcher import dp
from database.models import UserDB
from config import ADMIN_ID


@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID) & F.text.lower().startswith("выдать "))
async def handle_admin_command(message: Message):
    try:
        amount = int(message.text.split()[1])
        reply_to_user_id = message.reply_to_message.from_user.id

        UserDB.update_balance(reply_to_user_id, amount)
        await message.reply(f"Выдано {amount} Кото-грамм пользователю @{message.reply_to_message.from_user.username}")
    except (IndexError, ValueError):
        await message.reply("Неверный формат команды. Используйте 'выдать <количество>'")


@dp.message(F.reply_to_message & (F.from_user.id == ADMIN_ID) & F.text.lower().startswith("забрать "))
async def handle_take_command(message: Message):
    try:
        amount = int(message.text.split()[1])
        reply_to_user_id = message.reply_to_message.from_user.id

        balance = UserDB.get_balance(reply_to_user_id)
        if balance >= amount:
            UserDB.update_balance(reply_to_user_id, -amount)
            await message.reply(f"Забрано {amount} Кото-грамм у пользователя @{message.reply_to_message.from_user.username}")
        else:
            await message.reply(f"У пользователя @{message.reply_to_message.from_user.username} недостаточно средств.")

    except (IndexError, ValueError):
        await message.reply("Неверный формат команды. Используйте 'забрать <количество>'")
