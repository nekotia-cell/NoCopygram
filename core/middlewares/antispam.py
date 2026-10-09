import time
from aiogram.types import Message
from typing import Callable

spam_control: dict = {}
SPAM_DELAY = 3

def antispam(handler: Callable):
    async def wrapper(event: Message, **kwargs):
        user_id = event.from_user.id
        now = time.time()

        if user_id in spam_control and now - spam_control[user_id] < SPAM_DELAY:
            time_left = round(SPAM_DELAY - (now - spam_control[user_id]))
            await event.reply(f"Слишком много попыток, подождите {time_left} сек.")
            return

        spam_control[user_id] = now
        return await handler(event, **kwargs)
    return wrapper
