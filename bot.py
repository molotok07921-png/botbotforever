# bot.py
# Telegram bot with:
# - Profile
# - Admin panel
# - Watch
# - Shop
# - Coins
# - Referral system
# - User-created clone bots

import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # your telegram id

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher(storage=MemoryStorage())

# ================= DATABASE =================

db = sqlite3.connect("database.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    bots_created INTEGER DEFAULT 0,
    ref_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_bots(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    bot_token TEXT
)
""")

db.commit()

# ================= MENU =================

menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="👀 Смотреть")
        ],
        [
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="🪙 Монеты")
        ],
        [
            KeyboardButton(text="⚙️ Админ панель")
        ]
    ],
    resize_keyboard=True
)

# ================= FUNCTIONS =================

def get_user(user_id):
    cursor.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )
    return cursor.fetchone()

def create_user(user_id, ref_by=None):
    if not get_user(user_id):
        cursor.execute(
            "INSERT INTO users(user_id, ref_by) VALUES(?, ?)",
            (user_id, ref_by)
        )
        db.commit()

        if ref_by and ref_by != user_id:
            cursor.execute(
                "UPDATE users SET referrals = referrals + 1, balance = balance + 10 WHERE user_id=?",
                (ref_by,)
            )
            db.commit()

# ================= START =================

@dp.message(CommandStart())
async def start(message: types.Message):

    args = message.text.split()

    ref_by = None

    if len(args) > 1:
        try:
            ref_by = int(args[1])
        except:
            pass

    create_user(message.from_user.id, ref_by)

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Это многофункциональный бот.",
        reply_markup=menu
    )

# ================= PROFILE =================

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):

    user = get_user(message.from_user.id)

    balance = user[1]
    referrals = user[2]
    bots_created = user[3]

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"💰 Баланс: <b>{balance}</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>\n"
        f"🤖 Создано ботов: <b>{bots_created}</b>"
    )

    await message.answer(text)

# ================= WATCH =================

@dp.message(F.text == "👀 Смотреть")
async def watch(message: types.Message):
    await message.answer(
        "🎬 Раздел просмотра.\n"
        "Тут можно добавить видео, посты или задания."
    )

# ================= SHOP =================

@dp.message(F.text == "🛒 Магазин")
async def shop(message: types.Message):
    await message.answer(
        "🛒 Магазин пока пуст."
    )

# ================= COINS =================

@dp.message(F.text == "🪙 Монеты")
async def coins(message: types.Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Реферальная программа",
                    callback_data="ref"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Создать своего бота",
                    callback_data="create_bot"
                )
            ]
        ]
    )

    await message.answer(
        "🪙 Выберите действие:",
        reply_markup=keyboard
    )

# ================= REF SYSTEM =================

@dp.callback_query(F.data == "ref")
async def ref_system(callback: types.CallbackQuery):

    ref_link = f"https://t.me/{(await bot.get_me()).username}?start={callback.from_user.id}"

    await callback.message.answer(
        f"👥 <b>Реферальная программа</b>\n\n"
        f"Приглашайте друзей и получайте монеты.\n\n"
        f"🔗 Ваша ссылка:\n<code>{ref_link}</code>"
    )

# ================= CREATE BOT =================

waiting_token = {}

@dp.callback_query(F.data == "create_bot")
async def create_clone(callback: types.CallbackQuery):

    waiting_token[callback.from_user.id] = True

    await callback.message.answer(
        "🤖 Отправьте токен вашего бота из @BotFather"
    )

@dp.message()
async def token_handler(message: types.Message):

    if message.from_user.id in waiting_token:

        token = message.text.strip()

        try:
            test_bot = Bot(token=token)
            me = await test_bot.get_me()

            cursor.execute(
                "INSERT INTO user_bots(owner_id, bot_token) VALUES(?, ?)",
                (message.from_user.id, token)
            )

            cursor.execute(
                "UPDATE users SET bots_created = bots_created + 1 WHERE user_id=?",
                (message.from_user.id,)
            )

            db.commit()

            del waiting_token[message.from_user.id]

            await message.answer(
                f"✅ Бот успешно подключён!\n\n"
                f"🤖 Имя: {me.first_name}\n"
                f"📛 Username: @{me.username}"
            )

        except Exception as e:

            await message.answer(
                "❌ Неверный токен."
            )

# ================= ADMIN PANEL =================

@dp.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Нет доступа.")

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_bots")
    bots = cursor.fetchone()[0]

    text = (
        f"⚙️ <b>Админ панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"🤖 Создано ботов: <b>{bots}</b>"
    )

    await message.answer(text)

# ================= RUN =================

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
