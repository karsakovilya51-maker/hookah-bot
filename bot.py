import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ==========================================
# НАСТРОЙКИ И ТОКЕН
# ==========================================
BOT_TOKEN = "8806847684:AAEqBEY8p1U02TUnjJBRUY7pFRvdHdIuBCQ"
ADMIN_CHAT_ID = -1004430566048  # ID чата персонала

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# АССОРТИМЕНТ И ПРАЙС-ЛИСТ
# ==========================================
HOOKAH_TYPES = {
    "clay": {
        "title": "💨 На глиняной чаше",
        "price": 1400
    },
    "grapefruit": {
        "title": "🍊 На грейпфруте",
        "price": 1800
    },
    "pineapple": {
        "title": "🍍 На ананасе",
        "price": 2200
    },
    "cigar": {
        "title": "👑 Премиум (Сигарный табак Люкс)",
        "price": 2600
    }
}

STRENGTH_OPTIONS = {
    "light": "🟢 Легкий",
    "medium": "🟡 Средний",
    "hard": "🔴 Крепкий"
}

FLAVOR_PROFILES = [
    "🍊 Цитрусовый",
    "🍓 Ягодный",
    "🥭 Тропический / Фруктовый",
    "🍰 Десертный / Сладкий",
    "❄️ Свежий / С холодом",
    "🌿 Травянистый / Пряный"
]

# ==========================================
# СОСТОЯНИЯ ЗАКАЗА (FSM)
# ==========================================
class OrderHookah(StatesGroup):
    choosing_type = State()
    choosing_strength = State()
    choosing_flavor = State()
    waiting_comment = State()

# ==========================================
# КЛАВИАТУРЫ
# ==========================================
def get_types_keyboard():
    buttons = []
    for key, data in HOOKAH_TYPES.items():
        text = f"{data['title']} — {data['price']} ₽"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"type:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_strength_keyboard():
    buttons = [
        [InlineKeyboardButton(text=name, callback_data=f"strength:{key}")]
        for key, name in STRENGTH_OPTIONS.items()
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_type")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_flavor_keyboard():
    buttons = [
        [InlineKeyboardButton(text=flavor, callback_data=f"flavor:{flavor}")]
        for flavor in FLAVOR_PROFILES
    ]
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_strength")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить и вызвать кальянщика", callback_data="confirm_order")],
        [InlineKeyboardButton(text="✏️ Ввести пожелания / комментарий", callback_data="add_comment")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="restart")]
    ])

# ==========================================
# ХЕНДЛЕРЫ КОМАНД И ДИАЛОГА
# ==========================================
@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    # Определение стола из QR-кода (например, /start table_5 или /start 5)
    args = command.args
    if args:
        table_num = args.replace("table_", "")
        table_str = f"№ {table_num}"
    else:
        table_str = "Не определен (запуск без QR)"

    await state.clear()
    await state.update_data(table=table_str)

    text = (
        "👋 <b>Приветствуем в нашем Lounge!</b>\n\n"
        f"📌 <b>Ваш стол:</b> {table_str}\n\n"
        "<b>Шаг 1 из 3:</b> Выберите тип кальяна:"
    )
    await message.answer(text, reply_markup=get_types_keyboard(), parse_mode="HTML")
    await state.set_state(OrderHookah.choosing_type)

@dp.callback_query(F.data.startswith("type:"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    type_key = callback.data.split(":")[1]
    hookah_data = HOOKAH_TYPES.get(type_key)
    
    await state.update_data(
        type_key=type_key,
        type_title=hookah_data["title"],
        price=hookah_data["price"]
    )
    
    data = await state.get_data()
    table_str = data.get("table", "Не определен (запуск без QR)")

    await callback.message.edit_text(
        f"📌 <b>Стол:</b> {table_str}\n"
        f"💨 <b>Выбрано:</b> {hookah_data['title']} ({hookah_data['price']} ₽)\n\n"
        "<b>Шаг 2 из 3:</b> Выберите желаемую <b>крепость</b>:",
        reply_markup=get_strength_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.choosing_strength)

@dp.callback_query(F.data == "back_to_type")
async def back_to_type(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    table_str = data.get("table", "Не определен (запуск без QR)")
    
    await callback.message.edit_text(
        f"📌 <b>Ваш стол:</b> {table_str}\n\n"
        "<b>Шаг 1 из 3:</b> Выберите тип кальяна:",
        reply_markup=get_types_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.choosing_type)

@dp.callback_query(F.data.startswith("strength:"))
async def process_strength(callback: CallbackQuery, state: FSMContext):
    strength_key = callback.data.split(":")[1]
    strength_name = STRENGTH_OPTIONS.get(strength_key)
    
    await state.update_data(strength=strength_name)
    data = await state.get_data()
    table_str = data.get("table", "Не определен (запуск без QR)")

    await callback.message.edit_text(
        f"📌 <b>Стол:</b> {table_str}\n"
        f"⚡️ <b>Крепость:</b> {strength_name}\n\n"
        "<b>Шаг 3 из 3:</b> Выберите желаемый <b>профиль вкуса</b>:",
        reply_markup=get_flavor_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.choosing_flavor)

@dp.callback_query(F.data == "back_to_strength")
async def back_to_strength(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    table_str = data.get("table", "Не определен (запуск без QR)")
    
    await callback.message.edit_text(
        f"📌 <b>Стол:</b> {table_str}\n"
        f"💨 <b>Позиция:</b> {data.get('type_title')} ({data.get('price')} ₽)\n\n"
        "Выберите желаемую <b>крепость</b>:",
        reply_markup=get_strength_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.choosing_strength)

@dp.callback_query(F.data.startswith("flavor:"))
async def process_flavor(callback: CallbackQuery, state: FSMContext):
    flavor = callback.data.split(":", 1)[1]
    await state.update_data(flavor=flavor)
    await show_summary(callback.message, state)

async def show_summary(message: Message, state: FSMContext):
    data = await state.get_data()
    comment = data.get("comment", "Не указан")
    table_str = data.get("table", "Не определен (запуск без QR)")

    summary_text = (
        "📋 <b>ВАШ ЗАКАЗ:</b>\n\n"
        f"📌 <b>Стол:</b> {table_str}\n"
        f"💨 <b>Позиция:</b> {data.get('type_title')}\n"
        f"💰 <b>Стоимость:</b> <b>{data.get('price')} ₽</b>\n"
        f"⚡️ <b>Крепость:</b> {data.get('strength')}\n"
        f"🍓 <b>Вкусовая гамма:</b> {data.get('flavor')}\n"
        f"📝 <b>Комментарий:</b> {comment}\n\n"
        "Всё верно? Нажмите кнопку ниже для вызова кальянщика."
    )

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(summary_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")
    else:
        await message.answer(summary_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "add_comment")
async def ask_comment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Напишите в сообщении ваши пожелания (например: <i>'поменьше мяты'</i>, <i>'покислее'</i>):",
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.waiting_comment)

@dp.message(OrderHookah.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_summary(message, state)

@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    table_str = data.get("table", "Не определен (запуск без QR)")
    user_name = callback.from_user.full_name.replace("<", "&lt;").replace(">", "&gt;")
    username = f"@{callback.from_user.username}" if callback.from_user.username else "без username"
    comment = str(data.get('comment', 'Нет')).replace("<", "&lt;").replace(">", "&gt;")

    # Подтверждение гостю
    await callback.message.edit_text(
        "🎉 <b>Заказ принят!</b>\n\n"
        "Кальянщик уже получил ваш заказ и приступил к забивке. Ожидайте!",
        parse_mode="HTML"
    )

    # Уведомление в рабочий чат
    if ADMIN_CHAT_ID:
        admin_text = (
            "🚨 <b>НОВЫЙ ЗАКАЗ КАЛЬЯНА!</b>\n\n"
            f"📌 <b>Стол:</b> {table_str}\n"
            f"💨 <b>Позиция:</b> {data.get('type_title')}\n"
            f"💰 <b>Сумма:</b> <b>{data.get('price')} ₽</b>\n"
            f"⚡️ <b>Крепость:</b> {data.get('strength')}\n"
            f"🍓 <b>Вкусовая гамма:</b> {data.get('flavor')}\n"
            f"📝 <b>Пожелания:</b> {comment}\n\n"
            f"👤 <b>Гость:</b> {user_name} ({username})"
        )
        try:
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logging.error(f"Ошибка отправки администратору: {e}")

    await state.clear()

@dp.callback_query(F.data == "restart")
async def restart_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    table_str = data.get("table", "Не определен (запуск без QR)")
    
    await state.clear()
    await state.update_data(table=table_str)

    text = (
        "👋 <b>Приветствуем в нашем Lounge!</b>\n\n"
        f"📌 <b>Ваш стол:</b> {table_str}\n\n"
        "<b>Шаг 1 из 3:</b> Выберите тип кальяна:"
    )
    await callback.message.edit_text(text, reply_markup=get_types_keyboard(), parse_mode="HTML")
    await state.set_state(OrderHookah.choosing_type)

# ==========================================
# ЗАПУСК БОТА
# ==========================================
async def main():
    print("🚀 Бот успешно запущен и готовит кальяны!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
