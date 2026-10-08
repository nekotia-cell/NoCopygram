from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from core.dispatcher import dp


async def show_games_menu(message: Message):
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="От Кото-грамма", callback_data=f"games_koto_gram_{user_id}"),
            InlineKeyboardButton(text="От Грамма", callback_data=f"games_gram_{user_id}")
        ]
    ])

    await message.answer(
        f"<b>{user_link}, Выберите раздел игр, который хотите посмотреть:</b>\n   1⃣ От Кото-грама\n   2⃣ От Грамма",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_koto_gram_games(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=f"games_menu_{call.from_user.id}")]
    ])

    await call.message.edit_text(
        "<b>🎮 Игры от Кото-грамма:</b>\n\n"
        "• <code>Кубы &lt;ставка&gt; &lt;число от 1 до 6&gt;</code>\n"
        "• <code>Баскет &lt;ставка&gt;</code>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def show_gram_games(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=f"games_menu_{call.from_user.id}")]
    ])

    await call.message.edit_text(
        "<b>🎲 Игры от GRAMM:</b>\n\n"
        "• <code>Мины &lt;ставка&gt;</code>\n"
        "• • • Например: <code>Мины 50</code>\n\n"
        "• <code>Краш &lt;ставка&gt; &lt;множитель от 1.01 до 13&gt;</code>\n"
        "• • • Например: <code>Краш 20 2</code> / <code>Краш 20 3.69</code>\n\n"
        "• Рулетка: &lt;ставка&gt; &lt;диапозон чисел от 1 до 36 / «к» (красное) или «ч» (черное)&gt;\n"
        "• • • Например: <code>150 0-20</code>\n"
        "<blockquote>— Полные правила игры, с объяснениями: «<code>Правила рулетки</code>»</blockquote>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("games"))
async def games_handl(message: Message):
    await show_games_menu(message)


@dp.message(F.text.lower() == "игры")
async def games_handler(message: Message):
    await show_games_menu(message)


@dp.callback_query(F.data.startswith("games_menu_"))
async def callback_games_menu(call: CallbackQuery):
    user_id = call.from_user.id
    callback_user_id = int(call.data.split('_')[2])

    if user_id != callback_user_id:
        await call.answer("❌ Это не ваша кнопка!")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="От Кото-грамма", callback_data=f"games_koto_gram_{user_id}"),
            InlineKeyboardButton(text="От Грамма", callback_data=f"games_gram_{user_id}")
        ]
    ])

    await call.message.edit_text(
        "<b>Выберите раздел игр, который хотите посмотреть:</b>\n   1⃣ От Кото-грама\n   2⃣ От Грамма",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data.startswith("games_koto_gram_"))
async def callback_games_koto_gram(call: CallbackQuery):
    user_id = call.from_user.id
    callback_user_id = int(call.data.split('_')[3])

    if user_id != callback_user_id:
        await call.answer("❌ Это не ваша кнопка!")
        return

    await show_koto_gram_games(call)


@dp.callback_query(F.data.startswith("games_gram_"))
async def callback_games_gram(call: CallbackQuery):
    user_id = call.from_user.id
    callback_user_id = int(call.data.split('_')[2])

    if user_id != callback_user_id:
        await call.answer("❌ Это не ваша кнопка!")
        return

    await show_gram_games(call)
