import os
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from core.dispatcher import dp
from config import ADMIN_ID
from database.models import PromoDB


class CreatePromoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_amount = State()
    waiting_for_activations = State()


class DeletePromoState(StatesGroup):
    waiting_for_code = State()


class PromoInfoState(StatesGroup):
    waiting_for_code = State()


def get_main_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✨ Промокоды"), KeyboardButton(text="📥 Выгрузка")]],
        resize_keyboard=True
    )


def get_promo_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать промо"), KeyboardButton(text="🗑 Удалить промо")],
            [KeyboardButton(text="ℹ️ Промо инфо")],
            [KeyboardButton(text="◀️ Назад")]
        ],
        resize_keyboard=True
    )


def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


@dp.message(Command("adm"))
async def handle_adm_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return
    await message.answer("🔧 Панель администратора", reply_markup=get_main_admin_keyboard())


@dp.message(lambda message: message.text == "✨ Промокоды")
async def handle_promo_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🎫 Управление промокодами", reply_markup=get_promo_keyboard())


@dp.message(lambda message: message.text == "◀️ Назад")
async def handle_back_to_main(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("🔧 Панель администратора", reply_markup=get_main_admin_keyboard())


@dp.message(lambda message: message.text == "❌ Отмена")
async def handle_cancel(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await message.answer("❌ Действие отменено", reply_markup=get_promo_keyboard())


# ============ СОЗДАНИЕ ПРОМОКОДА ============

@dp.message(lambda message: message.text == "➕ Создать промо")
async def handle_create_promo_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(CreatePromoState.waiting_for_code)
    await message.answer("📝 Введите название промокода:", reply_markup=get_cancel_keyboard())


@dp.message(CreatePromoState.waiting_for_code)
async def process_promo_code(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=get_promo_keyboard())
        return
    
    code = message.text.strip().upper()
    
    if len(code) < 3:
        await state.clear()
        await message.answer("❌ Название слишком короткое. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    # В process_promo_code замените проверку существования:
    if PromoDB.get_by_code_case_insensitive(code):  # вместо PromoDB.get(code)
        await state.clear()
        await message.answer("❌ Такой промокод уже существует. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    await state.update_data(code=code)
    await state.set_state(CreatePromoState.waiting_for_amount)
    await message.answer(f"✅ Код: {code}\n\n💰 Введите количество Кото-грамм:", reply_markup=get_cancel_keyboard())


@dp.message(CreatePromoState.waiting_for_amount)
async def process_promo_amount(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=get_promo_keyboard())
        return
    
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            await state.clear()
            await message.answer("❌ Сумма должна быть больше 0. Возвращаю в меню.", reply_markup=get_promo_keyboard())
            return
    except ValueError:
        await state.clear()
        await message.answer("❌ Неверное число. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    await state.update_data(amount=amount)
    await state.set_state(CreatePromoState.waiting_for_activations)
    await message.answer(f"💰 Сумма: {amount}\n\n🔢 Введите количество активаций:", reply_markup=get_cancel_keyboard())


@dp.message(CreatePromoState.waiting_for_activations)
async def process_promo_activations(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание отменено", reply_markup=get_promo_keyboard())
        return
    
    try:
        activations = int(message.text.strip())
        if activations <= 0:
            await state.clear()
            await message.answer("❌ Количество активаций должно быть больше 0. Возвращаю в меню.", reply_markup=get_promo_keyboard())
            return
    except ValueError:
        await state.clear()
        await message.answer("❌ Неверное число. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    data = await state.get_data()
    code = data['code']
    amount = data['amount']
    
    PromoDB.create(code, amount, activations)
    await state.clear()
    
    await message.answer(
        f"✅ Промокод создан!\n\n🎫 Код: <code>{code}</code>\n💰 Кото-грамм: {amount}\n🔢 Активаций: {activations}",
        reply_markup=get_promo_keyboard(),
        parse_mode="HTML"
    )


# ============ УДАЛЕНИЕ ПРОМОКОДА ============

@dp.message(lambda message: message.text == "🗑 Удалить промо")
async def handle_delete_promo_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(DeletePromoState.waiting_for_code)
    await message.answer("🗑 Введите название промокода для удаления:", reply_markup=get_cancel_keyboard())


@dp.message(DeletePromoState.waiting_for_code)
async def process_delete_promo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Удаление отменено", reply_markup=get_promo_keyboard())
        return
    
    code = message.text.strip()
    
    # Ищем промокод без учета регистра
    promo = PromoDB.get_by_code_case_insensitive(code)
    if not promo:
        await state.clear()
        await message.answer("❌ Промокод не найден. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    # Удаляем по оригинальному коду из БД
    PromoDB.delete(promo['code'])
    await state.clear()
    await message.answer(f"✅ Промокод <code>{promo['code']}</code> удалён!", reply_markup=get_promo_keyboard(), parse_mode="HTML")

# ============ ИНФОРМАЦИЯ О ПРОМОКОДЕ ============

@dp.message(lambda message: message.text == "ℹ️ Промо инфо")
async def handle_promo_info_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.set_state(PromoInfoState.waiting_for_code)
    await message.answer("ℹ️ Введите название промокода:", reply_markup=get_cancel_keyboard())


@dp.message(PromoInfoState.waiting_for_code)
async def process_promo_info(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_promo_keyboard())
        return
    
    code = message.text.strip()
    
    # Ищем промокод без учета регистра
    promo = PromoDB.get_by_code_case_insensitive(code)
    
    if not promo:
        await state.clear()
        await message.answer("❌ Промокод не найден. Возвращаю в меню.", reply_markup=get_promo_keyboard())
        return
    
    used_count = len(promo['used_by'])
    remaining = promo['activations']
    total = used_count + remaining
    created_at = promo.get('created_at', 'Неизвестно')
    
    await state.clear()
    await message.answer(
        f"📊 Информация о промокоде <code>{promo['code']}</code>:\n\n"
        f"💰 Кото-грамм за активацию: {promo['koto_grams']}\n"
        f"🔢 Всего активаций: {total}\n"
        f"✅ Активировано: {used_count}\n"
        f"⏳ Осталось: {remaining}\n"
        f"📅 Создан: {created_at}",
        reply_markup=get_promo_keyboard(),
        parse_mode="HTML"
    )

# ============ ВЫГРУЗКА БАЗЫ ДАННЫХ ============

@dp.message(lambda message: message.text == "📥 Выгрузка")
async def handle_backup_button(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    db_path = "players.db"
    
    if not os.path.exists(db_path):
        await message.answer("❌ Файл базы данных не найден.", reply_markup=get_main_admin_keyboard())
        return
    
    try:
        file = FSInputFile(db_path, filename="players.db")
        await message.answer_document(
            document=file,
            caption=f"📁 Бэкап базы данных\n📦 Размер: {os.path.getsize(db_path) / 1024:.2f} KB",
            reply_markup=get_main_admin_keyboard()
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=get_main_admin_keyboard())
