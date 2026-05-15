# bot.py

import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ===================== SETTINGS =====================

TOKEN = "8565366731:AAHvZzapi6Q8I1x_z8Kxzseu1jnZgVLkg1s"
ADMIN_ID = 8075802187  # Твой Telegram ID

# ====================================================

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

def get_main_menu(user_id):

    buttons = [
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="👀 Смотреть")
        ],
        [
            KeyboardButton(text="🛒 Магазин"),
            KeyboardButton(text="🪙 Монеты")
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append(
            [KeyboardButton(text="⚙️ Админ панель")]
        )

    return ReplyKeyboardMarkup(
        keyboard=buttons,
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

    if get_user(user_id):
        return

    cursor.execute(
        "INSERT INTO users(user_id, ref_by) VALUES(?, ?)",
        (user_id, ref_by)
    )

    db.commit()

    if ref_by and ref_by != user_id:

        cursor.execute(
            "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
            (ref_by,)
        )

        cursor.execute(
            "UPDATE users SET balance = balance + 10 WHERE user_id=?",
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
        f"Добро пожаловать в бота.",
        reply_markup=get_main_menu(message.from_user.id)
    )

# ================= PROFILE =================

@dp.message(F.text == "👤 Профиль")
async def profile(message: types.Message):

    user = get_user(message.from_user.id)

    balance = user[1]
    referrals = user[2]
    bots_created = user[3]

    text = (
        f"👤 <b>Профиль</b>\n\n"
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
        "👀 Раздел просмотра.\n\n"
        "Тут можно добавить:\n"
        "• видео\n"
        "• задания\n"
        "• контент\n"
        "• подписки"
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

# ================= REFERRAL SYSTEM =================

@dp.callback_query(F.data == "ref")
async def referral_system(callback: types.CallbackQuery):

    me = await bot.get_me()

    ref_link = (
        f"https://t.me/{me.username}"
        f"?start={callback.from_user.id}"
    )

    await callback.message.answer(
        f"👥 <b>Реферальная система</b>\n\n"
        f"Приглашайте друзей и получайте монеты.\n\n"
        f"💸 Награда: 10 монет\n\n"
        f"🔗 Ваша ссылка:\n"
        f"<code>{ref_link}</code>"
    )

    await callback.answer()

# ================= CREATE CLONE BOT =================

waiting_for_token = {}

@dp.callback_query(F.data == "create_bot")
async def create_bot(callback: types.CallbackQuery):

    waiting_for_token[callback.from_user.id] = True

    await callback.message.answer(
        "🤖 Отправьте токен вашего бота из @BotFather"
    )

    await callback.answer()

# ================= TOKEN HANDLER =================

@dp.message()
async def token_handler(message: types.Message):

    if message.from_user.id not in waiting_for_token:
        return

    token = message.text.strip()

    try:

        test_bot = Bot(token=token)

        me = await test_bot.get_me()

        cursor.execute(
            """
            INSERT INTO user_bots(owner_id, bot_token)
            VALUES(?, ?)
            """,
            (message.from_user.id, token)
        )

        cursor.execute(
            """
            UPDATE users
            SET bots_created = bots_created + 1
            WHERE user_id=?
            """,
            (message.from_user.id,)
        )

        db.commit()

        del waiting_for_token[message.from_user.id]

        await message.answer(
            f"✅ Бот успешно подключён!\n\n"
            f"🤖 Имя: {me.first_name}\n"
            f"📛 Username: @{me.username}"
        )

    except Exception as e:

        await message.answer(
            "❌ Неверный токен бота."
        )

# ================= ADMIN PANEL =================

@dp.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return await message.answer(
            "❌ У вас нет доступа."
        )

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

    # Удаляем webhook чтобы работал polling
    await bot.delete_webhook(drop_pending_updates=True)

    print("Bot started")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
