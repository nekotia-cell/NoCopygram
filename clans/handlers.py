import re
from aiogram.types import Message, CallbackQuery
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.dispatcher import dp
from core.bot import bot
from core.middlewares.antispam import antispam
from database.models import UserDB, ClanDB, ClanMemberDB
from clans.models import Clan
from clans.manager import get_top_clans
from config import CLAN_CREATION_COST, CLAN_NAME_MAX_LENGTH, CLAN_MIN_DEPOSIT

from utils.userhelpers import ensure_user_exists

@dp.message(F.text.lower().startswith("клан повысить"))
async def handle_clan_promote_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    try:
        if clan_data['creator_id'] != user_id:
            await message.reply(f"{user_link}, Только глава клана может повышать участников.", parse_mode=ParseMode.HTML)
            return

        target_user_id = int(message.text.split()[2])

        if ClanMemberDB.get_role(target_user_id, clan_name) is None:
            await message.reply(f"{user_link}, Этот пользователь не состоит в вашем клане.", parse_mode=ParseMode.HTML)
            return

        if target_user_id == clan_data['creator_id']:
            await message.reply(f"{user_link}, Вы не можете повысить главу клана.", parse_mode=ParseMode.HTML)
            return

        clan = Clan(clan_name, clan_data['creator_id'], clan_data['creator_first_name'])
        if clan.promote_member(target_user_id):
            new_role = clan.get_member_role(target_user_id)
            await message.reply(f"{user_link}, Вы повысили пользователя с ID {target_user_id} до {new_role}.", parse_mode=ParseMode.HTML)
        else:
            await message.reply(f"{user_link}, Не удалось повысить пользователя.", parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(f"{user_link}, Неверный формат команды. Используйте 'Клан повысить <user_id>'.", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("клан понизить"))
async def handle_clan_demote_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    try:
        user_role = ClanMemberDB.get_role(user_id)
        if clan_data['creator_id'] != user_id and user_role != "заместитель":
            await message.reply(f"{user_link}, Только глава или заместитель может понижать участников.", parse_mode=ParseMode.HTML)
            return

        target_user_id = int(message.text.split()[2])

        if ClanMemberDB.get_role(target_user_id, clan_name) is None:
            await message.reply(f"{user_link}, Этот пользователь не состоит в вашем клане.", parse_mode=ParseMode.HTML)
            return

        if target_user_id == clan_data['creator_id']:
            await message.reply(f"{user_link}, Вы не можете понизить главу клана.", parse_mode=ParseMode.HTML)
            return

        if target_user_id == user_id:
            await message.reply(f"{user_link}, Вы не можете понизить самого себя.", parse_mode=ParseMode.HTML)
            return

        clan = Clan(clan_name, clan_data['creator_id'], clan_data['creator_first_name'])
        if clan.demote_member(target_user_id):
            new_role = clan.get_member_role(target_user_id)
            await message.reply(f"{user_link}, Вы понизили пользователя с ID {target_user_id} до {new_role}.", parse_mode=ParseMode.HTML)
        else:
            await message.reply(f"{user_link}, Не удалось понизить пользователя.", parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(f"{user_link}, Неверный формат команды. Используйте 'Клан понизить <user_id>'.", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().in_(["клан топ", "топ клан", "топ кланов", "топ кланы"]))
@antispam
async def handle_clan_top_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    top_clans = get_top_clans()

    if not top_clans:
        await message.reply(f"{user_link}, Нет ни одного клана.", parse_mode=ParseMode.HTML)
        return

    top_list = f"<b>{user_link}, Топ 10 кланов:</b>\n"
    for i, clan in enumerate(top_clans):
        top_list += f"{i+1}. {clan['name']} — {clan['rating']}👑\n—————————————————"

    user_clan = UserDB.get_clan(user_id)
    if user_clan:
        clan_data = ClanDB.get(user_clan)
        if clan_data:
            top_list += f"\n{clan_data['name']} — {clan_data['rating']}👑"
    else:
        top_list += "\nВы не состоите в клане"

    await message.reply(top_list, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "клан удалить")
async def handle_clan_delete_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if message.chat.type != 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data or clan_data['creator_id'] != user_id:
        await message.reply(f"{user_link}, Только создатель клана может удалить клан.", parse_mode=ParseMode.HTML)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Удалить клан', callback_data=f'delete_clan:{clan_name}:{user_id}'),
            InlineKeyboardButton(text='Отмена', callback_data=f'cancel_delete:{user_id}')
        ]
    ])

    await message.answer("Ты уверен что хочешь удалить свой клан?", reply_markup=keyboard)


@dp.callback_query(F.data.startswith('delete_clan'))
async def clan_delete(call: CallbackQuery):
    try:
        clan_name, owner_id_text = call.data[len('delete_clan:'):].rsplit(':', 1)
        owner_id = int(owner_id_text)
    except (ValueError, IndexError):
        await call.answer("Некорректное подтверждение.")
        return
    clan_data = ClanDB.get(clan_name)
    if owner_id != call.from_user.id or not clan_data or clan_data['creator_id'] != call.from_user.id:
        await call.answer("❌ У вас нет права удалить этот клан.")
        return
    ClanDB.delete(clan_name)

    await call.answer("Клан удален.")
    await call.message.edit_text("Клан удален.", reply_markup=None)


@dp.callback_query(F.data.startswith('cancel_delete:'))
async def clan_cancel(call: CallbackQuery):
    try:
        owner_id = int(call.data.split(':', 1)[1])
    except (ValueError, IndexError):
        await call.answer("Некорректное действие.")
        return
    if owner_id != call.from_user.id:
        await call.answer("❌ Это не ваша кнопка.")
        return
    await call.answer("Отменено.")
    await call.message.edit_text("Отменено.", reply_markup=None)


@dp.message(F.text.lower().startswith("клан название"))
async def handle_clan_rename_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    try:
        user_role = ClanMemberDB.get_role(user_id)
        if clan_data['creator_id'] != user_id and user_role != "заместитель":
            await message.reply(f"{user_link}, Только глава или заместитель может менять название клана.", parse_mode=ParseMode.HTML)
            return

        new_clan_name = message.text[len("клан название"):].strip()

        if not new_clan_name:
            await message.reply(f"{user_link}, Новое название клана не может быть пустым.", parse_mode=ParseMode.HTML)
            return

        if len(new_clan_name) > CLAN_NAME_MAX_LENGTH:
            await message.reply(f"{user_link}, Максимальная длина названия клана {CLAN_NAME_MAX_LENGTH} символов.", parse_mode=ParseMode.HTML)
            return

        if ClanDB.exists(new_clan_name):
            await message.reply(f"{user_link}, Клан с таким названием уже существует.", parse_mode=ParseMode.HTML)
            return

        if re.search(r"[@:/\\\"']", new_clan_name):
            await message.reply(f"{user_link}, Название клана содержит запрещенные символы (@ : / \\ \").", parse_mode=ParseMode.HTML)
            return

        # Rename in DB
        with __import__('database.db', fromlist=['get_db']).get_db() as cursor:
            cursor.execute('UPDATE clans SET name = ? WHERE name = ?', (new_clan_name, clan_name))
            cursor.execute('UPDATE clan_members SET clan_name = ? WHERE clan_name = ?', (new_clan_name, clan_name))
            cursor.execute('UPDATE users SET clan_name = ? WHERE clan_name = ?', (new_clan_name, clan_name))

        await message.reply(f"{user_link}, Название клана успешно изменено на '{new_clan_name}'.", parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(f"{user_link}, Неверный формат команды. Используйте 'Клан название <новое название>'.", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "клан участники")
async def handle_clan_members_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if message.chat.type == 'private':
        return

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    members = ClanMemberDB.get_members(clan_name)

    if not members:
        await message.reply(f"{user_link}, В клане нет участников.", parse_mode=ParseMode.HTML)
        return

    members_list = "<b>Участники клана:</b>\n"
    for member in members:
        members_list += f"- {member.get('first_name', 'Unknown')} (ID: {member['user_id']}) - {member['role']}\n"

    await message.reply(members_list, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("клан кик"))
async def handle_clan_kick_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    try:
        user_role = ClanMemberDB.get_role(user_id)
        if clan_data['creator_id'] != user_id and user_role != "заместитель":
            await message.reply(f"{user_link}, Только глава или заместитель может исключать участников.", parse_mode=ParseMode.HTML)
            return

        kicked_user_id = int(message.text.split()[2])

        if ClanMemberDB.get_role(kicked_user_id, clan_name) is None:
            await message.reply(f"{user_link}, Этот пользователь не состоит в вашем клане.", parse_mode=ParseMode.HTML)
            return

        if kicked_user_id == clan_data['creator_id']:
            await message.reply(f"{user_link}, Вы не можете исключить главу клана.", parse_mode=ParseMode.HTML)
            return

        if kicked_user_id == user_id:
            await message.reply(f"{user_link}, Вы не можете исключить самого себя.", parse_mode=ParseMode.HTML)
            return

        clan = Clan(clan_name, clan_data['creator_id'], clan_data['creator_first_name'])
        clan.remove_member(kicked_user_id)

        await message.reply(f"{user_link}, Вы исключили пользователя с ID {kicked_user_id} из клана «{clan_name}»", parse_mode=ParseMode.HTML)

    except (ValueError, IndexError):
        await message.reply(f"{user_link}, Неверный формат команды. Используйте 'Клан кик <user_id>'.", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("клан пригласить"))
async def handle_clan_invite_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    try:
        user_role = ClanMemberDB.get_role(user_id)
        if clan_data['creator_id'] != user_id and user_role not in ["заместитель", "модератор"]:
            await message.reply(f"{user_link}, Только глава, заместитель или модератор может приглашать участников.", parse_mode=ParseMode.HTML)
            return

        invited_user_id = int(message.text.split()[2])

        if UserDB.get_clan(invited_user_id):
            await message.reply(f"{user_link}, Этот пользователь уже состоит в клане.", parse_mode=ParseMode.HTML)
            return

        try:
            await bot.send_chat_action(invited_user_id, action='typing')

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='Принять', callback_data=f'accept_invite:{clan_name}:{user_id}'),
                    InlineKeyboardButton(text='Отклонить', callback_data='decline_invite')
                ]
            ])

            invited_user_link = hlink("Пользователю", f"tg://user?id={invited_user_id}")
            await bot.send_message(
                invited_user_id,
                f"{invited_user_link}, Вас пригласили в клан «{clan_name}», Принять приглашение?",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )

            await message.reply(f"{user_link}, Вы отправили приглашение пользователю с ID {invited_user_id} в клан «{clan_name}»", parse_mode=ParseMode.HTML)

        except Exception as e:
            await message.reply(
                f"{user_link}, Произошла ошибка при отправке приглашения\n\nВозможно этот пользователь еще не писал ни одного сообщения боту",
                parse_mode=ParseMode.HTML
            )

    except (ValueError, IndexError):
        await message.reply(f"{user_link}, Неверный формат команды. Используйте 'Клан пригласить <user_id>'.", parse_mode=ParseMode.HTML)


@dp.callback_query(F.data.startswith('accept_invite'))
async def clan_accept_invite(call: CallbackQuery):
    data = call.data[len('accept_invite:'):].split(':')
    clan_name = data[0]
    user_id = call.from_user.id

    if UserDB.get_clan(user_id):
        await call.answer("Вы уже состоите в клане!")
        await call.message.edit_text("Вы уже состоите в клане.", reply_markup=None)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        await call.answer("Клан не найден!")
        return

    clan = Clan(clan_name, clan_data['creator_id'], clan_data['creator_first_name'])
    if clan.add_member(user_id):
        await call.answer("Вы вступили в клан!")
        await call.message.edit_text("Вы вступили в клан!", reply_markup=None)
    else:
        await call.answer("Клан переполнен!")
        await call.message.edit_text("Клан переполнен!", reply_markup=None)


@dp.callback_query(F.data == 'decline_invite')
async def clan_decline_invite(call: CallbackQuery):
    await call.answer("Вы отклонили приглашение.")
    await call.message.edit_text("Вы отклонили приглашение.", reply_markup=None)


@dp.message(F.text.lower().startswith("создать клан "))
async def handle_create_clan_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    if UserDB.get_clan(user_id):
        await message.reply(f"{user_link}, Вы уже состоите в клане.", parse_mode=ParseMode.HTML)
        return

    balance = UserDB.get_balance(user_id)
    if balance < CLAN_CREATION_COST:
        await message.reply(f"{user_link}, Недостаточно Кото-грамм для создания клана. Необходимо {CLAN_CREATION_COST}.", parse_mode=ParseMode.HTML)
        return

    try:
        clan_name = message.text[len("создать клан "):].strip()

        if not clan_name:
            await message.reply(f"{user_link}, Название клана не может быть пустым.", parse_mode=ParseMode.HTML)
            return

        if len(clan_name) > CLAN_NAME_MAX_LENGTH:
            await message.reply(f"{user_link}, Максимальная длина названия клана {CLAN_NAME_MAX_LENGTH} символов.", parse_mode=ParseMode.HTML)
            return

        if ClanDB.exists(clan_name):
            await message.reply(f"{user_link}, Клан с таким названием уже существует.", parse_mode=ParseMode.HTML)
            return

        if re.search(r"[@:/\\\"']", clan_name):
            await message.reply(f"{user_link}, Название клана содержит запрещенные символы (@ : / \\ \").", parse_mode=ParseMode.HTML)
            return

        if not UserDB.debit(user_id, CLAN_CREATION_COST):
            await message.reply(f"{user_link}, Недостаточно Кото-грамм для создания клана.", parse_mode=ParseMode.HTML)
            return

        first_name = message.from_user.first_name if message.from_user.first_name else "Нет имени"
        ClanDB.create(clan_name, user_id, first_name)
        ClanMemberDB.add(user_id, clan_name, "глава", increment_count=False)
        UserDB.set_clan(user_id, clan_name)

        await message.reply(
            f"{user_link}, Клан «{clan_name}» успешно создан. Списано {CLAN_CREATION_COST} Кото-грамм.",
            parse_mode=ParseMode.HTML
        )

    except IndexError:
        await message.reply(f"{user_link}, Неверный формат команды. Используйте: 'Создать клан <название>'", parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == "мой клан")
async def handle_my_clan_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    clan_data = ClanDB.get(clan_name)
    if not clan_data:
        return

    member_role = ClanMemberDB.get_role(user_id)
    clan_info = (
        f"<b>🛡️ Клан:</b> <code>{clan_data['name']}</code>\n\n"
        f"<b>🧑‍🤝‍🧑 Создатель:</b> {clan_data['creator_first_name']}\n"
        f"<b>👥 Участников:</b> {clan_data['members_count']}\n"
        f"<b>ℹ️ Ваша роль:</b> {member_role}\n\n"
        f"<b>👑 Рейтинг:</b> <code>{clan_data['rating']}</code>\n"
        f"<b>💰 Казна:</b> <code>{clan_data['treasury']}</code> Кото-грамм"
    )

    await message.reply(clan_info, parse_mode=ParseMode.HTML)


@dp.message(F.text.lower().startswith("клан казна"))
async def handle_clan_treasury_command(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if UserDB.is_blocked(user_id):
        return

    clan_name = UserDB.get_clan(user_id)
    if not clan_name:
        await message.reply(f"{user_link}, Вы не состоите в клане.", parse_mode=ParseMode.HTML)
        return

    try:
        amount = int(message.text.split()[2])

        if amount < CLAN_MIN_DEPOSIT:
            await message.reply(f"{user_link}, Минимальная сумма для пополнения казны клана {CLAN_MIN_DEPOSIT} Кото-грамм.", parse_mode=ParseMode.HTML)
            return

        if amount <= 0:
            await message.reply(f"{user_link}, Сумма должна быть положительной.", parse_mode=ParseMode.HTML)
            return

        balance = UserDB.get_balance(user_id)
        if balance < amount:
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return

        if not UserDB.debit(user_id, amount):
            await message.reply(f"{user_link}, Недостаточно Кото-грамм на балансе.", parse_mode=ParseMode.HTML)
            return
        ClanDB.update_treasury(clan_name, amount)

        await message.reply(
            f"{user_link}, Вы внесли <code>{amount}</code> Кото-грамм в казну клана",
            parse_mode=ParseMode.HTML
        )

    except (ValueError, IndexError):
        await message.reply(
            f"{user_link}, Неверный формат команды. Используйте «клан казна сумма».",
            parse_mode=ParseMode.HTML,
        )
