# из папки games/roulette

import asyncio
import math
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from core.bot import bot
from core.middlewares.antispam import antispam
from database.models import UserDB, RouletteLogDB
from games.roulette.game import RouletteGame, spin_roulette, parse_bet
from config import LOG_LENGTH
from assets.gifs import ROULETTE_GIF

from utils.userhelpers import ensure_user_exists

# In-memory storage for active roulette games per chat
game_instances: dict = {}
game_locks: dict = {}


def get_game_instance(chat_id: int) -> RouletteGame:
    if chat_id not in game_instances:
        game_instances[chat_id] = RouletteGame()
    return game_instances[chat_id]


def get_game_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in game_locks:
        game_locks[chat_id] = asyncio.Lock()
    return game_locks[chat_id]


@dp.message(F.text.lower() == "го")
async def handle_go_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    chat_id = message.chat.id
    game = get_game_instance(chat_id)

    if message.chat.type == 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    async with get_game_lock(chat_id):
        if not game.bets:
            await message.reply("Никто не сделал ставок.")
            return
        bets = game.take_bets()

    gif_message = await message.answer_animation(ROULETTE_GIF)
    await asyncio.sleep(3)

    try:
        await bot.delete_message(chat_id, gif_message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении гифки: {e}")
        for bet in bets:
            UserDB.update_balance(bet['user_id'], bet['stake'])
        await message.reply("Не удалось удалить гифку. У меня нет прав администратора.")
        return

    winning_number, winning_color = spin_roulette()

    RouletteLogDB.add(f"{winning_number}{winning_color}")

    result_message = f"Рулетка: {winning_number} {winning_color}\n"
    winning_details = ""
    winners_found = False

    for bet in bets:
        user_id = bet['user_id']
        stake = bet['stake']
        bet_value = bet['bet']

        try:
            user = await bot.get_chat(user_id)
            user_link = hlink(user.first_name, f"tg://user?id={user_id}")
        except:
            user_link = f"User {user_id}"

        won = False
        winnings = 0

        if isinstance(bet_value, int):
            if bet_value == winning_number:
                won = True
                winnings = stake * 36
        elif isinstance(bet_value, tuple):
            if winning_number >= bet_value[0] and winning_number <= bet_value[1]:
                won = True
                winnings = stake * 0.91
                winnings = round(winnings)
        elif bet_value == 'red' or bet_value == 'black':
            if (bet_value == 'red' and winning_color == '🔴') or (bet_value == 'black' and winning_color == '⚫️'):
                won = True
                winnings = stake * 2

        if won:
            UserDB.update_balance(user_id, int(winnings))
            bet_desc = bet_value
            if bet_value == 'red':
                bet_desc = '🔴'
            elif bet_value == 'black':
                bet_desc = '⚫️'
            winning_details += f"{user_link} выиграл {int(winnings)} Кото-грамм на {bet_desc}\n"
            winners_found = True

    if not winners_found:
        result_message += "\n<blockquote><b>Никто не выиграл!</b></blockquote>"

    result_message += "\n" + winning_details
    await message.answer(result_message, parse_mode=ParseMode.HTML)



@dp.message(F.text.lower() == "лог")
async def handle_log_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id

    if message.chat.type == 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    log = RouletteLogDB.get_all()
    log_message = " ".join(log) if log else "История пуста"
    await message.answer(log_message)


@dp.message(F.text)
async def handle_roulette_bets(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")
    chat_id = message.chat.id
    text = message.text.lower()

    if message.chat.type == 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    game = get_game_instance(chat_id)

    if text == "отмена":
        total_refund = game.remove_user_bets(user_id)
        if total_refund > 0:
            UserDB.update_balance(user_id, total_refund)

        await message.reply(
            f"{user_link}, Ваши ставки отменены.\n\nВозвращено {total_refund} Кото-грамм.",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        parts = text.split()
        if len(parts) >= 2:
            if parts[0].isdigit():
                stake = int(parts[0])
                if stake <= 0:
                    await message.reply(f"{user_link}, Ставка должна быть положительной.", parse_mode=ParseMode.HTML)
                    return

                bets_str = parts[1:]

                if len(bets_str) > 16:
                    await message.reply(f"{user_link}, Максимальное количество ставок - 16.", parse_mode=ParseMode.HTML)
                    return

                balance = UserDB.get_balance(user_id)
                bet_message_lines = []
                amount_deducted = 0

                message_red_black = {'red': False, 'black': False}

                for bet_str in bets_str:
                    if balance >= stake:
                        bet_value = parse_bet(bet_str, user_id, {})

                        if bet_value is not None:
                            if bet_value == 'red':
                                if message_red_black['red'] or not game.can_place_color_bet(user_id, 'red'):
                                    bet_message_lines.append("Вы уже сделали ставку на 🔴.")
                                    continue
                                message_red_black['red'] = True
                            elif bet_value == 'black':
                                if message_red_black['black'] or not game.can_place_color_bet(user_id, 'black'):
                                    bet_message_lines.append("Вы уже сделали ставку на ⚫️.")
                                    continue
                                message_red_black['black'] = True

                            if not UserDB.debit(user_id, stake):
                                bet_message_lines.append("Недостаточно средств для этой ставки")
                                break
                            game.add_bet(user_id, stake, bet_value)

                            if bet_value == 'red':
                                game.set_color_bet(user_id, 'red')
                            elif bet_value == 'black':
                                game.set_color_bet(user_id, 'black')

                            amount_deducted += stake
                            balance -= stake

                            bet_description = bet_str
                            if bet_value == 'red':
                                bet_description = '🔴'
                            elif bet_value == 'black':
                                bet_description = '⚫️'
                            bet_message_lines.append(f"{stake} Кото-грамм на {bet_description}")
                        else:
                            bet_message_lines.append("Неверная ставка")
                    else:
                        bet_message_lines.append("Недостаточно средств для этой ставки")
                        break

                accepted_bets_message = "\n".join(bet_message_lines)
                await message.reply(
                    f"{user_link}, Ставки приняты:\n{accepted_bets_message}",
                    parse_mode=ParseMode.HTML
                )

    except ValueError:
        await message.reply(f"{user_link}, Ошибка в формате ставки.", parse_mode=ParseMode.HTML)
    except Exception as e:
        print(e)
