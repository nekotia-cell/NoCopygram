# из папки games/mines

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def generate_mines_keyboard(user_id: int, mine_positions: list, revealed: set, cancel_button: bool = True) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    buttons = []

    for i in range(25):
        if i in revealed:
            if i in mine_positions:
                buttons.append(InlineKeyboardButton(text="💣", callback_data="noop"))
            else:
                buttons.append(InlineKeyboardButton(text="❌", callback_data="noop"))
        else:
            buttons.append(InlineKeyboardButton(text="❓", callback_data=f"mine_{user_id}_{i}"))

    # Arrange in rows of 5
    for i in range(0, 25, 5):
        keyboard.inline_keyboard.append(buttons[i:i+5])

    if cancel_button:
        cancel_btn = InlineKeyboardButton(text="❌", callback_data=f"cancel_{user_id}")
        keyboard.inline_keyboard.append([cancel_btn])

    return keyboard


def add_claim_button(keyboard: InlineKeyboardMarkup, user_id: int) -> InlineKeyboardMarkup:
    claim_button = InlineKeyboardButton(text="💵 Забрать выигрыш", callback_data=f"claim_{user_id}")
    keyboard.inline_keyboard.append([claim_button])
    return keyboard
