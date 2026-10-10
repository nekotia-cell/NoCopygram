# из папки games/mines

import asyncio
import math
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.bot import bot
from core.middlewares.antispam import antispam
from database.models import UserDB, ActiveGameDB
from games.mines.game import MinesGame, MULTIPLIERS
from games.mines.keyboard import generate_mines_keyboard, add_claim_button

from utils.userhelpers import ensure_user_exists

@dp.message(F.text.lower().startswith("мины"))
@antispam
async def handle_mines_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )

    if UserDB.is_blocked(user_id):
        return

    if ActiveGameDB.get(user_id):
        await message.reply("У вас уже есть активная игра. Завершите ее перед началом новой.")
        return

    try:
        _, stake_str = message.text.split(" ", 1)
        stake = int(stake_str)

        if stake <= 0:
            await message.reply(f"{user_link}Ставка должна быть положительным числом", parse_mode=ParseMode.HTML)
            return

        if stake <= 9:
            await message.reply(f"{user_link}, Минимальная ставка 10 Кото-грамм", parse_mode=ParseMode.HTML)
            return

        balance = UserDB.get_balance(user_id)

        if balance < stake:
            await message.reply(f"{user_link}, Недостаточно Кото-грамов на балансе", parse_mode=ParseMode.HTML)
            return

        if not UserDB.debit(user_id, stake):
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return

    except ValueError:
        await message.reply("Неверный формат команды. Используйте 'мины <ставка>'")
        return

    game = MinesGame(user_id, stake, message.chat.id)
    ActiveGameDB.save(user_id, 'mines', game.to_dict())

    game_start_message = (
        f"{user_link}, Вы начали игру минное поле!\n"
        "Для начала игры выберите одно из закрытых полей\n"
        f"Ставка: {stake}\n"
        f"Выигрыш: x{MULTIPLIERS[0]}\n\n"
    )

    keyboard = generate_mines_keyboard(user_id, game.mine_positions, set())
    sent_message = await message.answer(game_start_message, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    
    game.message_id = sent_message.message_id
    ActiveGameDB.save(user_id, 'mines', game.to_dict())


@dp.callback_query(F.data.startswith("mine_"))
async def handle_mines_callback(call: CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    try:
        _, user_id_str, button_index_str = call.data.split("_")
        button_index = int(button_index_str)
        user_id_from_callback = int(user_id_str)

        if user_id != user_id_from_callback or not 0 <= button_index < 25:
            await call.answer("❌ Это не ваша игра!")
            return
    except (ValueError, IndexError):
        print(f"Error parsing callback {call.data}")
        return

    game_data = ActiveGameDB.get(user_id)
    if not game_data or game_data['game_type'] != 'mines':
        await call.answer("Игра не найдена. Начните новую.")
        return

    game = MinesGame.from_dict(user_id, game_data['game_data'])

    if button_index in game.revealed:
        await call.answer("Вы уже открыли эту ячейку.")
        return

    is_safe = game.reveal(button_index)

    if not is_safe:
        ActiveGameDB.delete(user_id)
        revealed = set(game.mine_positions) | game.revealed
        keyboard = generate_mines_keyboard(user_id, game.mine_positions, revealed)
        await call.message.edit_reply_markup(reply_markup=keyboard)
        await call.answer("Ты попал по мине!")
        await bot.send_message(chat_id, "Вы проиграли 💣")
        ActiveGameDB.delete(user_id)
    else:
        if not game.is_max_multiplier():
            game.next_multiplier()
            ActiveGameDB.save(user_id, 'mines', game.to_dict())

            new_multiplier = game.get_current_multiplier()
            updated_message = (
                "Вы начали игру минное поле!\n"
                "Для начала игры выберите одно из закрытых полей\n"
                f"Ставка: {game.stake}\n"
                f"Выигрыш: x{new_multiplier}\n\n"
            )

            main_keyboard = generate_mines_keyboard(user_id, game.mine_positions, game.revealed, cancel_button=False)
            add_claim_button(main_keyboard, user_id)

            await call.message.edit_text(updated_message, reply_markup=main_keyboard, parse_mode=ParseMode.HTML)
            await call.answer("Безопасно!")
        else:
            winnings = game.calculate_winnings()
            if not ActiveGameDB.settle(user_id, winnings):
                await call.answer("Игра уже завершена другим запросом.")
                return

            end_message = f"Игра закончена!\nВы выиграли: {winnings} Кото-грамм"
            await call.message.edit_text(end_message, reply_markup=None, parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith("claim_"))
async def handle_claim_callback(call: CallbackQuery):
    user_id = call.from_user.id

    try:
        owner_id = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некорректная кнопка.")
        return
    if owner_id != user_id:
        await call.answer("❌ Это не ваша игра!")
        return

    game_data = ActiveGameDB.get(user_id)
    if not game_data or game_data['game_type'] != 'mines':
        await call.answer("Игра не найдена. Начните новую.")
        return

    game = MinesGame.from_dict(user_id, game_data['game_data'])
    winnings = game.calculate_winnings()

    if not ActiveGameDB.settle(user_id, winnings):
        await call.answer("Игра уже завершена другим запросом.")
        return

    end_message = f"Игра закончена!\nВы выиграли: {winnings} Кото-грамм"
    await call.message.edit_text(end_message, reply_markup=None)

    await call.answer("Вы забрали выигрыш!")


@dp.callback_query(F.data.startswith("cancel_"))
async def handle_cancel_callback(call: CallbackQuery):
    user_id = call.from_user.id

    try:
        owner_id = int(call.data.split("_", 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некорректная кнопка.")
        return
    if owner_id != user_id:
        await call.answer("❌ Это не ваша игра!")
        return

    game_data = ActiveGameDB.get(user_id)
    if not game_data or game_data['game_type'] != 'mines':
        await call.answer("Игра не найдена.")
        return

    game = MinesGame.from_dict(user_id, game_data['game_data'])
    if not ActiveGameDB.expire_and_refund(user_id, game.stake):
        await call.answer("Игра уже завершена другим запросом.")
        return

    await call.message.delete()
    await call.answer("Игра отменена.")
