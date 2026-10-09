from aiogram.types import Message
from aiogram import F
from aiogram.filters import Command
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode

from core.dispatcher import dp
from database.models import UserDB

from utils.userhelpers import ensure_user_exists

@dp.message(F.reply_to_message & F.text.lower() == "ид")
async def handle_get_id_command(message: Message):
    ensure_user_exists(message)
    replied_user_id = message.reply_to_message.from_user.id
    await message.reply(f"ID этого пользователя: `{replied_user_id}`", parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("gif"))
async def handle_gif_id(message: Message):
    ensure_user_exists(message)
    if message.reply_to_message and message.reply_to_message.animation:
        gif_id = message.reply_to_message.animation.file_id
        await message.reply(f"ID этой GIF: `{gif_id}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply("Ответьте этой командой на GIF, чтобы узнать её ID.")


@dp.message(F.text.lower().in_(["правила рулетки", "правила рулетка"]))
async def rules_ruletka(message: Message):
    ensure_user_exists(message)
    user_id = message.from_user.id
    user_link = hlink(message.from_user.first_name, f"tg://user?id={user_id}")

    if message.chat.type in ['group', 'supergroup']:
        await message.reply(
            f"<b>{user_link}, Лучше напиши это в личные сообщения боту,</b> а то боюсь меня выгонят отсюдова, за такой огромный текст :)",
            parse_mode=ParseMode.HTML
        )
        return

    if UserDB.is_blocked(user_id):
        return

    await message.reply(
        f"""{user_link}, Если ты тут, то тогда тебе либо интересно посмотреть что я тут накалякал, либо ты реально не знаешь как играть в Рулетку
    
Так что щас все объясню :)
(<u>!!!</u>) <b>Ограничений для минимальной ставки нет</b>

<b>Например вы пишите так:</b> <code>150 0-20</code> 
— То тогда это значит, что вы ставите 150 Кото-грамм на диапозон чисел от 0 до 20 и если какое-то число из этого диапазона выпадет, то тогда вы получите <u>91%</u> от вашей ставки, в нашем случае получится <u>150 * 0.91 = 136</u> Или можете по формуле:
<blockquote>•|--------------------------------------------------|•
<code>Y * 0.91 = X</code>\n\n<b>• Y - Ставка</b>\n<b>• X - Выигрыш</b>\n•|--------------------------------------------------|•</blockquote>    
    
• Также можно ставить вот так: «<code>150 к</code>» / «<code>150 ч</code>»
— При таком случае вы не ставите на диапозон чисел, тоесть теперь если в Рулетке выпадет красное или черное (в зависимости от того что вы поставили), то тогда при выигрыше вы получите <u>300</u> Кото-грамм
• • • <b>Ставка * 2</b>

• Ну или же вы можете поставить на одно число, <i>Например</i> «<code>100 30</code>»
— Вот здесь уже если выпадет именно то число которое вы написали, то тогда <u>ваша ставка умножиться на 36</u> (!), <tg-spoiler>боюсь представить что будет при выгрыше на ставке в 10.000 Кото-грамм</tg-spoiler>

<b>• И еще есть вариант с возможностью ставить сразу несколько ставок в одном сообщении,</b> <i>Например</i> «<code>100 0-20 к</code>»
<b>— В таком случае у вас спишется 200 Кото-грамм вместо 100, так как вы поставили сразу 2 ставки <u>(0-20 и к)</u></b>

<b>• • • Но если вы вдруг перехотели играть в Рулетку, а ставку уже сделали, то тогда достаточно написать слово</b> «<code>Отмена</code>» и все ваши ставки пропадут, а Кото-граммы которые вы потратили вернутся на ваш баланс

• • • Для просмотра истории выпадения чисел в рулетке, <i>напишите:</i> «<code>Лог</code>»

• • • После всех ставок, вы можете запустить рулетку, словом «<code>Го</code>» и увидеть результаты Рулетки.
<blockquote>❗️ <i>ВАЖНО:</i> <b>в результатах рулетки показываются только те пользователи, которые выиграли! Так что имейте ввиду</b></blockquote>""",
        parse_mode=ParseMode.HTML
    )
