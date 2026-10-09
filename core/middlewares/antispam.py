import time
from functools import wraps
from typing import Callable

from aiogram.types import Message

spam_control: dict[int, float] = {}
SPAM_DELAY = 3


def antispam(handler: Callable):
    @wraps(handler)
    async def wrapper(event: Message, **kwargs):
        user = event.from_user

        if user is None:
            return await handler(event)

        user_id = user.id
        now = time.time()

        if (
            user_id in spam_control
            and now - spam_control[user_id] < SPAM_DELAY
        ):
            time_left = round(
                SPAM_DELAY - (now - spam_control[user_id])
            )
            await event.reply(
                f"Слишком много попыток, подождите {time_left} сек."
            )
            return

        spam_control[user_id] = now

        # Не передаём служебные параметры aiogram обработчику.
        return await handler(event)

    return wrapper
