from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from database.models import UserDB
from utils.text import gram_declension
from users.vip import get_vip_prefix

from utils.user_helpers import ensure_user_exists

@dp.message(F.reply_to_message & F.text.lower().startswith(("п ", "передать ")))
async def handle_transfer_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.chat.type == 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    try:
        amount = int(message.text.split()[1])
        sender_id = message.from_user.id
        recipient_id = message.reply_to_message.from_user.id

        if sender_id == recipient_id:
            await message.reply("Нельзя перевести самому себе.")
            return

        sender_balance = UserDB.get_balance(sender_id)
        if sender_balance < amount:
            await message.reply("У вас недостаточно средств.")
            return

        if UserDB.get(recipient_id) is None:
            UserDB.create(recipient_id, message.reply_to_message.from_user.first_name, 
                         message.reply_to_message.from_user.last_name)

        UserDB.update_balance(sender_id, -amount)
        UserDB.update_balance(recipient_id, amount)

        sender_link = hlink(
            f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
            f"tg://user?id={sender_id}"
        )
        recipient_link = hlink(
            f"{message.reply_to_message.from_user.first_name} {message.reply_to_message.from_user.last_name or ''}".strip(),
            f"tg://user?id={recipient_id}"
        )
        declension = gram_declension(amount)
        vip_prefix = get_vip_prefix(user_id)

        await message.answer(
            f"{vip_prefix}{sender_link} передал <code>{amount}</code> {declension} пользователю {recipient_link}\n\n<blockquote><b><i>BOT IN BETA-TEST</i></b></blockquote>",
            parse_mode=ParseMode.HTML
        )

    except (IndexError, ValueError):
        await message.reply(
            "Неверный формат команды. Используйте «<code>П количество</code>» или «<code>Передать количество</code>»",
            parse_mode=ParseMode.HTML
        )
