import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# -------------------------------------------------------------------
# НАСТРОЙКИ
# -------------------------------------------------------------------
BOT_TOKEN = "8806847684:AAHvIlND-TGVYyd-BXY830tY6_IvgdxkhTE"
ADMIN_CHAT_ID = -1004430566048

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# -------------------------------------------------------------------
# СОСТОЯНИЯ (FSM)
# -------------------------------------------------------------------
class HookahOrder(StatesGroup):
    choosing_strength = State()
    choosing_flavor = State()
    confirming = State()

# -------------------------------------------------------------------
# ХЕНДЛЕРЫ
# -------------------------------------------------------------------
async def show_strength_selection(message: types.Message, table_number: str, state: FSMContext):
    await state.update_data(table=table_number)

    builder = InlineKeyboardBuilder()
    builder.button(text="🟢 Легкий", callback_data="strength_Легкий")
    builder.button(text="🟡 Средний", callback_data="strength_Средний")
    builder.button(text="🔴 Крепкий", callback_data="strength_Крепкий")
    builder.adjust(1)

    await message.answer(
        f"👋 <b>Приветствуем в нашем Lounge!</b>\n\n"
        f"📍 Ваш стол: <b>{table_number}</b>\n\n"
        f"<b>Шаг 1 из 2:</b> Выберите желаемую крепость кальяна:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(HookahOrder.choosing_strength)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject, state: FSMContext):
    table_number = command.args if command.args else "Не определен (запуск без QR)"
    await show_strength_selection(message, table_number, state)

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    table_number = data.get("table", "Не определен (запуск без QR)")
    await show_strength_selection(message, table_number, state)

@dp.callback_query(HookahOrder.choosing_strength, F.data.startswith("strength_"))
async def process_strength(callback: types.CallbackQuery, state: FSMContext):
    strength = callback.data.split("_")[1]
    await state.update_data(strength=strength)

    builder = InlineKeyboardBuilder()
    builder.button(text="🍊 Цитрусовый mix", callback_data="flavor_Цитрусовый mix")
    builder.button(text="🍓 Ягодный mix", callback_data="flavor_Ягодный mix")
    builder.button(text="🍏 Фруктовый mix", callback_data="flavor_Фруктовый mix")
    builder.button(text="🍰 Десертный / Сладкий", callback_data="flavor_Десертный / Сладкий")
    builder.button(text="🌿 Свежий / Травянистый", callback_data="flavor_Свежий / Травянистый")
    builder.button(text="🎲 На усмотрение мастера", callback_data="flavor_На усмотрение мастера")
    builder.adjust(2)

    await callback.message.edit_text(
        f"Выбрана крепость: <b>{strength}</b>\n\n"
        f"<b>Шаг 2 из 2:</b> Выберите предпочитаемую вкусовую гамму:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(HookahOrder.choosing_flavor)

@dp.callback_query(HookahOrder.choosing_flavor, F.data.startswith("flavor_"))
async def process_flavor(callback: types.CallbackQuery, state: FSMContext):
    flavor = callback.data.split("_")[1]
    await state.update_data(flavor=flavor)

    data = await state.get_data()

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Отправить заказ", callback_data="send_order")
    builder.button(text="🔄 Начать заново", callback_data="restart")
    builder.adjust(1)

    await callback.message.edit_text(
        f"📋 <b>Проверьте ваш заказ:</b>\n\n"
        f"📍 <b>Стол:</b> {data.get('table')}\n"
        f"💨 <b>Крепость:</b> {data.get('strength')}\n"
        f"🍓 <b>Вкус:</b> {flavor}\n\n"
        f"Всё верно?",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(HookahOrder.confirming)

@dp.callback_query(F.data == "restart")
async def process_restart(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Заказ отменен. Отсканируйте QR-код заново или введите /start.")

@dp.callback_query(HookahOrder.confirming, F.data == "send_order")
async def process_send_order(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    username = f"@{callback.from_user.username}" if callback.from_user.username else callback.from_user.full_name

    admin_message = (
        f"🚨 <b>НОВЫЙ ЗАКАЗ КАЛЬЯНА!</b>\n\n"
        f"📌 <b>Стол:</b> № {data.get('table')}\n"
        f"💨 <b>Крепость:</b> {data.get('strength')}\n"
        f"🍓 <b>Вкусовая гамма:</b> {data.get('flavor')}\n\n"
        f"👤 <b>Гость:</b> {username}"
    )

    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="HTML")
        await callback.message.edit_text(
            "✅ <b>Ваш заказ принят!</b>\n\nКальянный мастер уже приступил к забивке. Ожидайте у своего стола.",
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при отправке заказа. Обратитесь к персоналу.")
        logging.error(f"Ошибка отправки в чат {ADMIN_CHAT_ID}: {e}")

    await state.clear()

# -------------------------------------------------------------------
# СЕРВЕР ПРОВЕРКИ АКТИВНОСТИ ДЛЯ ОБЛАКА
# -------------------------------------------------------------------
async def handle_health(request):
    return web.Response(text="Bot is alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# -------------------------------------------------------------------
# ЗАПУСК БОТА
# -------------------------------------------------------------------
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    print("🚀 Бот успешно запущен в облаке!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
