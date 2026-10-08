from aiogram.types import Message
from aiogram.filters import Command

from core.dispatcher import dp
from database.models import UserDB
from config import ADMIN_ID


@dp.message(Command("stopb"))
async def handle_block_command(message: Message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id_to_block = int(message.text.split()[1])
            UserDB.set_blocked(user_id_to_block, True)
            await message.reply(f"Пользователь с ID {user_id_to_block} заблокирован.")
        except (IndexError, ValueError):
            await message.reply("Неверный формат команды. Используйте /stopb <user_id>")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")


@dp.message(Command("unblock"))
async def handle_unblock_command(message: Message):
    if message.from_user.id == ADMIN_ID:
        try:
            user_id_to_unblock = int(message.text.split()[1])
            UserDB.set_blocked(user_id_to_unblock, False)
            await message.reply(f"Пользователь с ID {user_id_to_unblock} разблокирован.")
        except (IndexError, ValueError):
            await message.reply("Неверный формат команды. Используйте /unblock <user_id>")
    else:
        await message.reply("У вас нет прав для выполнения этой команды.")
