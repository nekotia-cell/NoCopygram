import asyncio
import time
import os
import sys

# Определяем абсолютный путь к корню проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Добавляем также родительскую директорию (на всякий случай)
sys.path.insert(0, os.path.dirname(PROJECT_ROOT))

from core.bot import bot
from core.dispatcher import dp
from database.db import init_db, close_db
from database.models import ActiveGameDB, UserDB, ClanDB
from config import GAME_TIMEOUT, CLAN_RATING_UPDATE_INTERVAL

import games.dice.handlers
import games.basketball.handlers

# Используем абсолютные импорты относительно корня проекта
from commands import gamesmenu
from commands import top
from commands import bonus
from commands import transfer
from commands import other
from commands.admin import block
from commands.admin import balance
import commands.admin.adminmenu

# Импортируем остальные модули
import users.handlers
import clans.handlers
import games.mines.handlers
import games.roulette.handlers
import games.crash.handlers

from commands import promo

async def check_game_timeouts():
    while True:
        await asyncio.sleep(30)
        current_time = time.time()
        
        games = ActiveGameDB.get_all()
        for game_data in games:
            if current_time - game_data['last_action_time'] > GAME_TIMEOUT:
                user_id = game_data['user_id']
                game_dict = game_data['game_data']
                
                # Atomically remove the game and refund it exactly once.
                if not ActiveGameDB.expire_and_refund(user_id, game_dict['stake']):
                    continue
                
                # Try to edit message
                try:
                    if game_dict.get('message_id') and game_dict.get('chat_id'):
                        from core.bot import bot
                        await bot.edit_message_text(
                            "Время вышло! Ставка возвращена.",
                            chat_id=game_dict['chat_id'],
                            message_id=game_dict['message_id'],
                            reply_markup=None
                        )
                except Exception as e:
                    print(f"Error editing message: {e}")
                


async def update_clan_ratings():
    last_update = time.time()
    while True:
        await asyncio.sleep(60)
        current_time = time.time()

        if current_time - last_update >= CLAN_RATING_UPDATE_INTERVAL:
            # Update clan ratings logic here if needed
            last_update = current_time
            print("Рейтинги кланов обновлены")


async def keep_alive():
    while True:
        await asyncio.sleep(60)


async def main():
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Start background tasks
    asyncio.create_task(check_game_timeouts())
    asyncio.create_task(update_clan_ratings())
    asyncio.create_task(keep_alive())

    print('Бот запущен...')
    try:
        await dp.start_polling(bot)
    finally:
        close_db()


if __name__ == "__main__":
    asyncio.run(main())
