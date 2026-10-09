# из папки users/

import pytz
import datetime
from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command

from core.dispatcher import dp
from core.middlewares.antispam import antispam
from database.models import UserDB, ClanDB, ClanMemberDB
from users.vip import is_vip, get_vip_prefix, buy_vip, get_vip_time_left
from utils.text import gram_declension
from config import TIMEZONE

from utils.userhelpers import ensure_user_exists

@dp.message(CommandStart())
@antispam
async def start_handler(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")
    chat_id = message.chat.id

    await message.answer(
        f"""Добро пожаловать {user_link}

KOTO GRAM - это виртуальная валюта. У нас можно создать собственный клан(скоро), играть в игры.
<b>• Для просмотра всех игр напишите:</b>
• • • <code>Игры</code>

• Можно смотреть топ по Кото-грамам во всем боте
<code>Топ грам N</code>
Где N = число просмотра мест в топе (Минимум: 10. Максимум: 50)
• • • Например: <code>Топ грам 20</code>

• Также вы можете получать Бонус раз в 24 часа
<b>• • • Для получения бонуса, напишите:</b> <code>Бонус</code>

<i>Также у нас есть VIP-статус, для более подробной информации напишите:</i> «<code>Вип</code>»

Валюту можно передавать другим пользователям.

•|--------------------------------------------------|•
<b>❗️ Важно:</b> Большинство функционала бота работает только в групповых чатах!
•|--------------------------------------------------|•

<b>БОТ НАХОДИТСЯ В БЕТА-ТЕСТЕ!</b>""",
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.lower() == "профиль")
async def handle_profile(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    user = UserDB.get(user_id)
    if not user:
        await message.reply(
            f"{user_link}, 🚫 Вы не зарегистрированы. Напишите «<code>Бонус</code>», а потом снова «<code>Профиль</code>»",
            parse_mode=ParseMode.HTML
        )
        return

    clan_info = "Отсутствует"
    if user['clan_name']:
        clan_data = ClanDB.get(user['clan_name'])
        if clan_data:
            clan_info = f"{clan_data['name']}"

    profile_info = (
        f"<b>Профиль:</b>\n\n"
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
        f"<b>👤 Имя:</b> {user_link}\n"
        f"<b>💰 Кото-граммы:</b> <code>{user['balance']}</code>\n"
        f"<b>🛡️ Клан:</b> {clan_info}\n\n"
        f"<b><blockquote>📅 Дата регистрации: {user['registration_date']}</blockquote></b>"
    )

    await message.reply(profile_info, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "вип")
@antispam
async def handle_vip_info(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id

    if UserDB.is_blocked(user_id):
        return

    vipsob = """<b>VIP привилегии: (на 69 дней)</b>

<blockquote><i>1. 👑 - Эксклюзивный значок, отображаемый в топе, переводе Кото-грамм и балансе
2. При получении бонуса, вы будете получать от 700 до 1000 Кото-грамм</i></blockquote>

<b>Цена випа 500 Кото-грам (Временно)</b>
<i>Для покупки напишите:</i> «<code>Купить вип</code>»"""

    await message.answer(vipsob, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "купить вип")
@antispam
async def handle_vip_purchase(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )

    if UserDB.is_blocked(user_id):
        return

    if is_vip(user_id):
        await message.reply(
            f"{user_link}, <b>У вас уже есть VIP!</b> Для более подробной информации напишите «<code>Мой вип</code>»",
            parse_mode=ParseMode.HTML
        )
        return

    if buy_vip(user_id):
        await message.reply(
            f"<b>{user_link}, Вы успешно приобрели VIP-статус на 69 дней!</b>\n\nДля подробной информации, напишите «<code>Мой вип</code>»",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply(
            f"<b>{user_link}, Недостаточно Кото-грам для покупки VIP-статуса.</b> <blockquote><i>Необходимо 500 Кото-грам</i></blockquote>\n\nПодробнее: «<code>Вип</code>»",
            parse_mode=ParseMode.HTML
        )


@dp.message(F.text.lower() == "мой вип")
@antispam
async def handle_my_vip(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )

    if UserDB.is_blocked(user_id):
        return

    if is_vip(user_id):
        time_left = get_vip_time_left(user_id)
        await message.reply(
            f"<b>{user_link}, Ваш VIP истекает через:</b>\n{time_left}\n\n<b>Возможности випа:</b> «<code>Вип</code>»",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply(
            f"{user_link}, У вас нет активного VIP-статуса. Купить его можно, написав «<code>Купить вип</code>»",
            parse_mode=ParseMode.HTML
        )


@dp.message(F.text.lower().in_(["б", "баланс", "грам", "грамм"]))
async def handle_gram_message(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id

    if UserDB.is_blocked(user_id):
        return

    balance = UserDB.get_balance(user_id)
    declension = gram_declension(balance)
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )
    vip_prefix = get_vip_prefix(user_id)

    await message.answer(
        f"{vip_prefix}{user_link}\n<blockquote>💰 Баланс: <b>{balance}</b> {declension}</blockquote>",
        parse_mode=ParseMode.HTML
    )
