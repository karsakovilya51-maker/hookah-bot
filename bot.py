import os
import asyncio
import logging
import signal
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ==========================================
# ИГНОРИРУЕМ SIGHUP ДЛЯ RENDER
# ==========================================
signal.signal(signal.SIGHUP, signal.SIG_IGN)

# ==========================================
# НАСТРОЙКИ И ТОКЕН
# ==========================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "-1004430566048"))

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(storage=MemoryStorage())

# ==========================================
# РАСШИРЕННЫЙ АССОРТИМЕНТ КАЛЬЯНОВ
# ==========================================
HOOKAH_TYPES = {
    # ===== БЮДЖЕТНЫЙ СЕГМЕНТ (1400-1600) =====
    "clay": {
        "title": "🏺 На глиняной чаше",
        "price": 1400,
        "category": "Бюджетный",
        "description": "Классика. Тайминг 40+ мин"
    },
    "glass": {
        "title": "🥃 На стеклянной чаше",
        "price": 1500,
        "category": "Бюджетный",
        "description": "Чистый вкус без привкусов"
    },
    "classic_mix": {
        "title": "🔥 Микс «Классика»",
        "price": 1500,
        "category": "Бюджетный",
        "description": "Двойной яблоко + виноград"
    },
    "ceramic": {
        "title": "🍒 На керамической чаше",
        "price": 1600,
        "category": "Бюджетный",
        "description": "Равномерный прогрев"
    },
    "silicone": {
        "title": "🌿 На силиконовой чаше",
        "price": 1600,
        "category": "Бюджетный",
        "description": "Практичный и удобный"
    },
    "berry_mix": {
        "title": "🍬 Микс «Ягодный рай»",
        "price": 1600,
        "category": "Бюджетный",
        "description": "Клубника + малина + смородина"
    },
    
    # ===== СРЕДНИЙ СЕГМЕНТ (1800-2400) =====
    "grapefruit": {
        "title": "🍊 На грейпфруте",
        "price": 1800,
        "category": "Средний",
        "description": "Сочный цитрусовый вкус"
    },
    "apple": {
        "title": "🍎 На яблоке",
        "price": 1900,
        "category": "Средний",
        "description": "Легкая кислинка"
    },
    "pineapple": {
        "title": "🍍 На ананасе",
        "price": 2200,
        "category": "Средний",
        "description": "Экзотическая сладость"
    },
    "watermelon": {
        "title": "🍉 Арбузный бум",
        "price": 2400,
        "category": "Средний",
        "description": "Сочный, освежающий"
    },
    
    # ===== ПРЕМИУМ СЕГМЕНТ (2500-2900) =====
    "tropical": {
        "title": "💎 Мастер-микс «Тропический»",
        "price": 2500,
        "category": "Премиум",
        "description": "Манго + маракуйя + ананас"
    },
    "berry_bouquet": {
        "title": "💎 Мастер-микс «Ягодный букет»",
        "price": 2500,
        "category": "Премиум",
        "description": "Малина + вишня + гранат"
    },
    "dessert": {
        "title": "💎 Мастер-микс «Десертный»",
        "price": 2600,
        "category": "Премиум",
        "description": "Ваниль + чизкейк + шоколад"
    },
    "spicy_whiskey": {
        "title": "💎 Мастер-микс «Пряный виски»",
        "price": 2700,
        "category": "Премиум",
        "description": "Виски + корица + имбирь"
    },
    "satyr": {
        "title": "🧨 Satyr Platinum",
        "price": 2700,
        "category": "Премиум",
        "description": "Цитрус + корица + мускат"
    },
    "bonche": {
        "title": "🧨 Bonche (сигарный лист)",
        "price": 2800,
        "category": "Премиум",
        "description": "Благородный сигарный вкус"
    },
    "tangiers": {
        "title": "🧨 Tangiers (американский)",
        "price": 2900,
        "category": "Премиум",
        "description": "Элитный. Насыщенный."
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
# КАТАЛОГ КАЛЬЯНОВ (ЕДИНОЕ МЕНЮ)
# ==========================================
HOOKAH_CATALOG = """
<b>📋 КАТАЛОГ КАЛЬЯНОВ</b>  JOKERS LOUNGE

━━━━━━━━━━━━━━━━━━━━━━━

<b>🟢 БЮДЖЕТНЫЙ СЕГМЕНТ (1 400 - 1 600 ₽)</b>
─────────────
🏺 <b>На глиняной чаше</b> — 1 400 ₽
   Классика. Тайминг 40+ мин

🥃 <b>На стеклянной чаше</b> — 1 500 ₽
   Чистый вкус без привкусов

🔥 <b>Микс «Классика»</b> — 1 500 ₽
   Двойной яблоко + виноград

🍒 <b>На керамической чаше</b> — 1 600 ₽
   Равномерный прогрев

🌿 <b>На силиконовой чаше</b> — 1 600 ₽
   Практичный и удобный

🍬 <b>Микс «Ягодный рай»</b> — 1 600 ₽
   Клубника + малина + смородина

━━━━━━━━━━━━━━━━━━━━━━━

<b>🟡 СРЕДНИЙ СЕГМЕНТ (1 800 - 2 400 ₽)</b>
─────────────
🍊 <b>На грейпфруте</b> — 1 800 ₽
   Сочный цитрусовый вкус

🍎 <b>На яблоке</b> — 1 900 ₽
   Легкая кислинка

🍍 <b>На ананасе</b> — 2 200 ₽
   Экзотическая сладость

🍉 <b>Арбузный бум</b> — 2 400 ₽
   Сочный, освежающий

━━━━━━━━━━━━━━━━━━━━━━━

<b>🔴 ПРЕМИУМ-СЕГМЕНТ (2 500 - 2 900 ₽)</b>
─────────────
💎 <b>Мастер-микс «Тропический»</b> — 2 500 ₽
   Манго + маракуйя + ананас

💎 <b>Мастер-микс «Ягодный букет»</b> — 2 500 ₽
   Малина + вишня + гранат

💎 <b>Мастер-микс «Десертный»</b> — 2 600 ₽
   Ваниль + чизкейк + шоколад

💎 <b>Мастер-микс «Пряный виски»</b> — 2 700 ₽
   Виски + корица + имбирь

🧨 <b>Satyr Platinum</b> — 2 700 ₽
   Цитрус + корица + мускат

🧨 <b>Bonche (сигарный лист)</b> — 2 800 ₽
   Благородный сигарный вкус

🧨 <b>Tangiers (американский)</b> — 2 900 ₽
   Элитный. Насыщенный.

━━━━━━━━━━━━━━━━━━━━━━━

<i>🔥 Для заказа нажмите /start 
   и пройдите все шаги</i>
"""

# ==========================================
# СОСТОЯНИЯ ЗАКАЗА (FSM)
# ==========================================
class OrderHookah(StatesGroup):
    choosing_type = State()
    choosing_strength = State()
    choosing_flavor = State()
    waiting_comment = State()

# ==========================================
# ГЛАВНАЯ КЛАВИАТУРА (Reply)
# ==========================================
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Меню")],
            [KeyboardButton(text="📚 Каталог кальянов")],
            [KeyboardButton(text="🔄 Заменить угли")],
            [KeyboardButton(text="❓ Помощь и контакты")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )
    return keyboard

# ==========================================
# КЛАВИАТУРЫ ДЛЯ ЗАКАЗА (Inline)
# ==========================================
def get_types_keyboard():
    buttons = []
    
    # Добавляем разделители для категорий
    categories = ["Бюджетный", "Средний", "Премиум"]
    category_emojis = {"Бюджетный": "🟢", "Средний": "🟡", "Премиум": "🔴"}
    
    for category in categories:
        # Кнопка-заголовок категории (неактивная)
        buttons.append([InlineKeyboardButton(
            text=f"{category_emojis[category]} ━━━ {category} ━━━", 
            callback_data=f"sep:{category}"
        )])
        
        # Кнопки с позициями в категории
        for key, data in HOOKAH_TYPES.items():
            if data["category"] == category:
                text = f"{data['title']} — {data['price']} ₽"
                buttons.append([InlineKeyboardButton(
                    text=text, 
                    callback_data=f"type:{key}"
                )])
    
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
    logging.info(f"Команда /start от {message.from_user.id}")
    
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

# ==========================================
# НОВЫЕ ФУНКЦИИ
# ==========================================

@dp.message(F.text == "📚 Каталог кальянов")
async def show_catalog(message: Message):
    """Функция 'каталог кальянов' - показывает единый каталог"""
    await message.answer(
        HOOKAH_CATALOG,
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "🔄 Заменить угли")
async def replace_coals(message: Message):
    """Функция 'заменить угли' - сообщает о вызове мастера"""
    text = (
        "🔥 <b>Кальянный мастер скоро к вам подойдет!</b>\n\n"
        "Пожалуйста, ожидайте. Специалист заменит угли в ближайшее время.\n"
        "⏱ Ориентировочное время ожидания: 3-5 минут."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

@dp.message(F.text == "❓ Помощь и контакты")
async def help_and_contacts(message: Message):
    """Функция 'помощь и контакты' - показывает контакты"""
    text = (
        "📞 <b>ПОМОЩЬ И КОНТАКТЫ</b>\n\n"
        "📍 <b>Наш адрес:</b>\n"
        "Лаунж бар Joker's Lounge\n"
        "Ростов-на-Дону\n\n"
        
        "🗺 <b>Как добраться:</b>\n"
        "https://yandex.ru/maps/org/jokers_lounge/139909063671/\n\n"
        
        "💬 <b>Жалобы, предложения и хвалебные отзывы:</b>\n"
        "https://t.me/PravovedVayur\n\n"
        
        "🕐 <b>Время работы:</b>\n"
        "Ежедневно с 12:00 до 06:00\n\n"
        
        "📋 <b>Доступные команды:</b>\n"
        "/start - Перезапустить бота / Выбрать стол\n"
        "/menu - Каталог кальянов и напитков (скоро)\n"
        "/call - Заменить угли / Вызвать персонал\n"
        "/help - Помощь и контакты заведения"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

# ==========================================
# КОМАНДЫ ДЛЯ БОТА
# ==========================================

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """Команда /menu - показывает каталог"""
    await show_catalog(message)

@dp.message(Command("call"))
async def cmd_call(message: Message):
    """Команда /call - вызов персонала"""
    await replace_coals(message)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help - помощь и контакты"""
    await help_and_contacts(message)

# ==========================================
# ОБРАБОТЧИК ДЛЯ КНОПКИ "МЕНЮ"
# ==========================================

@dp.message(F.text == "📋 Меню")
async def show_main_menu(message: Message, state: FSMContext):
    """Кнопка 'Меню' - показывает главное меню"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        
    text = (
        "🍽 <b>ГЛАВНОЕ МЕНЮ</b>\n\n"
        "Выберите действие с помощью кнопок ниже:\n\n"
        "📚 <b>Каталог кальянов</b> - ознакомьтесь с ассортиментом\n"
        "🔄 <b>Заменить угли</b> - вызвать кальянного мастера\n"
        "❓ <b>Помощь и контакты</b> - информация о заведении\n\n"
        "Чтобы сделать заказ, нажмите /start"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_main_keyboard())

# ==========================================
# ОБРАБОТЧИК ДЛЯ РАЗДЕЛИТЕЛЕЙ (игнорируем)
# ==========================================

@dp.callback_query(F.data.startswith("sep:"))
async def handle_separator(callback: CallbackQuery):
    """Игнорируем нажатие на разделители"""
    await callback.answer()

# ==========================================
# ОСТАЛЬНЫЕ ХЕНДЛЕРЫ
# ==========================================

@dp.callback_query(F.data.startswith("type:"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    try:
        type_key = callback.data.split(":")[1]
        hookah_data = HOOKAH_TYPES.get(type_key)
        
        if not hookah_data:
            await callback.answer("❌ Такой тип кальяна не найден", show_alert=True)
            return
        
        await state.update_data(
            type_key=type_key,
            type_title=hookah_data["title"],
            price=hookah_data["price"]
        )
        
        data = await state.get_data()
        table_str = data.get("table", "Не определен (запуск без QR)")

        # Добавляем описание к выбранному кальяну
        await callback.message.edit_text(
            f"📌 <b>Стол:</b> {table_str}\n"
            f"💨 <b>Выбрано:</b> {hookah_data['title']} ({hookah_data['price']} ₽)\n"
            f"📝 <b>Описание:</b> {hookah_data['description']}\n\n"
            "<b>Шаг 2 из 3:</b> Выберите желаемую <b>крепость</b>:",
            reply_markup=get_strength_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(OrderHookah.choosing_strength)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в process_type: {e}")
        await callback.answer("❌ Произошла ошибка, попробуйте снова", show_alert=True)

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
    await callback.answer()

@dp.callback_query(F.data.startswith("strength:"))
async def process_strength(callback: CallbackQuery, state: FSMContext):
    try:
        strength_key = callback.data.split(":")[1]
        strength_name = STRENGTH_OPTIONS.get(strength_key)
        
        if not strength_name:
            await callback.answer("❌ Неверная опция", show_alert=True)
            return
        
        await state.update_data(strength=strength_name)
        data = await state.get_data()
        table_str = data.get("table", "Не определен (запуск без QR)")

        await callback.message.edit_text(
            f"📌 <b>Стол:</b> {table_str}\n"
            f"💨 <b>Позиция:</b> {data.get('type_title')} ({data.get('price')} ₽)\n"
            f"⚡️ <b>Крепость:</b> {strength_name}\n\n"
            "<b>Шаг 3 из 3:</b> Выберите желаемый <b>профиль вкуса</b>:",
            reply_markup=get_flavor_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(OrderHookah.choosing_flavor)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в process_strength: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

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
    await callback.answer()

@dp.callback_query(F.data.startswith("flavor:"))
async def process_flavor(callback: CallbackQuery, state: FSMContext):
    try:
        flavor = callback.data.split(":", 1)[1]
        await state.update_data(flavor=flavor)
        await show_summary(callback, state)
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка в process_flavor: {e}")
        await callback.answer("❌ Произошла ошибка", show_alert=True)

async def show_summary(event, state: FSMContext):
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

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(summary_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")
    elif isinstance(event, Message):
        await event.answer(summary_text, reply_markup=get_confirm_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "add_comment")
async def ask_comment(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📝 Напишите в сообщении ваши пожелания:\n"
        "<i>Например: 'поменьше мяты', 'покислее', 'сделать покрепче'</i>",
        parse_mode="HTML"
    )
    await state.set_state(OrderHookah.waiting_comment)
    await callback.answer()

@dp.message(OrderHookah.waiting_comment)
async def process_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await show_summary(message, state)

@dp.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()

        table_str = data.get("table", "Не определен (запуск без QR)")
        user_name = callback.from_user.full_name.replace("<", "&lt;").replace(">", "&gt;")
        username = f"@{callback.from_user.username}" if callback.from_user.username else "без username"
        comment = str(data.get('comment', 'Нет')).replace("<", "&lt;").replace(">", "&gt;")

        await callback.message.edit_text(
            "🎉 <b>Заказ принят!</b>\n\n"
            "Кальянщик уже получил ваш заказ и приступил к забивке.\n"
            "⏱ Ожидайте 7-10 минут.\n\n"
            "А пока можете насладиться атмосферой нашего Lounge! 🎵",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )

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
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text, parse_mode="HTML")

        await state.clear()
        await callback.answer("✅ Заказ подтвержден!")
        
    except Exception as e:
        logging.error(f"Ошибка в confirm_order: {e}")
        await callback.answer("❌ Ошибка при подтверждении заказа", show_alert=True)

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
    await callback.answer()

# ==========================================
# ВЕБ-СЕРВЕР ДЛЯ RENDER
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def handle_health(request):
    """Endpoint для проверки здоровья"""
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

# ==========================================
# KEEP-ALIVE ФУНКЦИЯ (ПИНГ)
# ==========================================
async def keep_alive():
    """Пинговать сервер каждые 5 минут, чтобы он не засыпал"""
    url = f"http://localhost:{os.getenv('PORT', 8080)}/health"
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        logging.info("✅ Keep-alive ping успешен")
                    else:
                        logging.warning(f"⚠️ Keep-alive ping ответил {response.status}")
        except Exception as e:
            logging.error(f"❌ Ошибка keep-alive: {e}")
        
        await asyncio.sleep(300)

# ==========================================
# ЗАПУСК
# ==========================================
async def main():
    logging.info("🚀 Запуск бота...")
    
    if not BOT_TOKEN:
        logging.error("❌ BOT_TOKEN не найден!")
        return

    await start_web_server()
    
    asyncio.create_task(keep_alive())
    logging.info("🔄 Keep-alive задача запущена (каждые 5 минут)")

    bot = Bot(token=BOT_TOKEN)
    
    try:
        me = await bot.get_me()
        logging.info(f"✅ Бот запущен: @{me.username}")
        
        commands = [
            types.BotCommand(command="start", description="Перезапустить бота / Выбрать стол"),
            types.BotCommand(command="menu", description="Каталог кальянов и напитков"),
            types.BotCommand(command="call", description="Заменить угли / Вызвать персонал"),
            types.BotCommand(command="help", description="Помощь и контакты заведения")
        ]
        await bot.set_my_commands(commands)
        
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("🔄 Webhook удален")
        
        await dp.start_polling(bot, skip_updates=True)
        
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
