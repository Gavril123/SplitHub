import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo
)

# --- НАСТРОЙКИ (Берутся из переменных окружения на хостинге) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0)) # По умолчанию 0, если не задан
APP_URL = os.getenv("APP_URL", "https://tiny-salamander-f7e6cd.netlify.app/")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/+mgCGOEPq4hgyZmZi")
# -----------------------------------------------------------

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Храним активные заказы: {user_id: order_text}
active_orders = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Открыть приложение")],
            [KeyboardButton(text="Наш канал")]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    await message.answer(text="Добро пожаловать в SplitHub!", reply_markup=keyboard)

@dp.message(F.text == "Открыть приложение")
async def open_app(message: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Запустить магазин", web_app=WebAppInfo(url=APP_URL))]
        ]
    )
    await message.answer("Нажмите на кнопку ниже, чтобы начать покупки:", reply_markup=inline_kb)

@dp.message(F.text == "Наш канал")
async def open_channel(message: Message):
    await message.answer(f"Переходите в наш канал: {CHANNEL_URL}")

# --- ЛОВИМ ЗАКАЗ С САЙТА ---
@dp.message(F.text.startswith("🔥"))
async def catch_order(message: Message):
    if message.from_user.id == ADMIN_ID:
        return

    user_id = message.from_user.id
    
    # Сохраняем текст заказа в память
    active_orders[user_id] = message.text

    try:
        await message.delete()
    except:
        pass

    # Отправляем админу с пометкой, что можно юзать /acc
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Новый заказ от {message.from_user.full_name} (@{message.from_user.username})\n\n{message.text}\n\n👉 Напиши /acc чтобы подтвердить, или /dec чтобы отклонить",
        parse_mode="HTML"
    )
    
    await message.answer("✅ Ваш заказ отправлен на проверку! Ожидайте.")

# --- КОМАНДЫ ПОДТВЕРЖДЕНИЯ / ОТКЛОНЕНИЯ ---
@dp.message(Command("acc"), F.from_user.id == ADMIN_ID)
async def approve_order(message: Message):
    if not active_orders:
        await message.answer("Нет активных заказов для подтверждения.")
        return
        
    # Берем последний заказ (по ID пользователя)
    user_id = list(active_orders.keys())[-1]
    order_text = active_orders.pop(user_id)

    # Уведомляем клиента
    try:
        await bot.send_message(
            chat_id=user_id,
            text="✅ Ваш заказ успешно подтвержден! Спасибо за покупку."
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение клиенту {user_id}: {e}")

    await message.answer(f"✅ Заказ клиента {user_id} подтвержден!")

@dp.message(Command("dec"), F.from_user.id == ADMIN_ID)
async def reject_order(message: Message):
    if not active_orders:
        await message.answer("Нет активных заказов для отклонения.")
        return

    user_id = list(active_orders.keys())[-1]
    active_orders.pop(user_id)

    # Уведомляем клиента
    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ваш заказ отклонен. Пожалуйста, свяжитесь с поддержкой."
        )
    except Exception as e:
        logging.error(f"Не удалось отправить сообщение клиенту {user_id}: {e}")

    await message.answer(f"❌ Заказ клиента {user_id} отклонен!")

async def main():
    if not BOT_TOKEN:
        print("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
        return
    if not ADMIN_ID:
        print("ОШИБКА: ADMIN_ID не найден в переменных окружения!")
        return
        
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")