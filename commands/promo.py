from aiogram.types import Message
from aiogram import F
from aiogram.utils.markdown import hlink
from aiogram.enums import ParseMode
from core.dispatcher import dp
from database.models import PromoDB, UserDB
from core.middlewares.antispam import antispam


# Используем lambda вместо startswith
@dp.message(lambda message: message.text and message.text.startswith('#'))
@antispam
async def handle_promo_text(message: Message):
    """Активация промокода через #код (регистронезависимо)"""
    user_id = message.from_user.id
    
    # Проверяем, не заблокирован ли пользователь
    if UserDB.is_blocked(user_id):
        return
    
    # Получаем текст (убираем # и пробелы)
    text = message.text.strip()
    code = text[1:].strip()  # Убираем # в начале
    
    # Проверяем длину кода (минимум 1 символ после #)
    if len(code) < 1:
        return
    
    # Ищем промокод без учета регистра ТОЛЬКО если есть # в начале
    promo = PromoDB.get_by_code_case_insensitive(code)
    
    # Если промокод не найден — молча игнорируем (не отвечаем)
    if not promo:
        return
    
    # Если нашли — проверяем остальное...
    
    # Проверяем, не использовал ли уже этот пользователь
    if user_id in promo['used_by']:
        await message.reply("❌ Вы уже активировали этот промокод.")
        return
    
    # Проверяем, остались ли активации
    if promo['activations'] <= 0:
        await message.reply("❌ У промокода закончились активации.")
        return
    
    # Активируем промокод (используем оригинальный код из БД)
    success = PromoDB.use(promo['code'], user_id)
    if not success:
        await message.reply("❌ Ошибка активации промокода.")
        return
    
    # Начисляем баланс
    UserDB.update_balance(user_id, promo['koto_grams'])
    
    user_link = hlink(
        f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
        f"tg://user?id={user_id}"
    )
    
    await message.reply(
        f"✅ {user_link}, промокод активирован!\n\n"
        f"🎫 Код: <code>{promo['code']}</code>\n"
        f"💰 Получено: +{promo['koto_grams']} Кото-грамм",
        parse_mode=ParseMode.HTML
    )
