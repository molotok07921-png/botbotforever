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
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ================= SETTINGS =================

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789

# ============================================

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

def main_menu(user_id):

    buttons = [
        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile"
            )
        ],
        [
            InlineKeyboardButton(
                text="👀 Смотреть",
                callback_data="watch"
            )
        ],
        [
            InlineKeyboardButton(
                text="🛒 Магазин",
                callback_data="shop"
            )
        ],
        [
            InlineKeyboardButton(
                text="🪙 Монеты",
                callback_data="coins"
            )
        ]
    ]

    if user_id == ADMIN_ID:
        buttons.append([
            InlineKeyboardButton(
                text="⚙️ Админ панель",
                callback_data="admin"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
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
        """
        INSERT INTO users(user_id, ref_by)
        VALUES(?, ?)
        """,
        (user_id, ref_by)
    )

    db.commit()

    if ref_by and ref_by != user_id:

        cursor.execute(
            """
            UPDATE users
            SET referrals = referrals + 1
            WHERE user_id=?
            """,
            (ref_by,)
        )

        cursor.execute(
            """
            UPDATE users
            SET balance = balance + 10
            WHERE user_id=?
            """,
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

    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в бота."
    )

    await message.answer(
        text,
        reply_markup=main_menu(message.from_user.id)
    )

# ================= PROFILE =================

@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):

    user = get_user(callback.from_user.id)

    balance = user[1]
    referrals = user[2]
    bots_created = user[3]

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"💰 Баланс: <b>{balance}</b>\n"
        f"👥 Рефералов: <b>{referrals}</b>\n"
        f"🤖 Создано ботов: <b>{bots_created}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )

# ================= WATCH =================

@dp.callback_query(F.data == "watch")
async def watch(callback: types.CallbackQuery):

    text = (
        "👀 <b>Смотреть</b>\n\n"
        "Тут можно добавить:\n"
        "• видео\n"
        "• контент\n"
        "• задания\n"
        "• подписки"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )

# ================= SHOP =================

@dp.callback_query(F.data == "shop")
async def shop(callback: types.CallbackQuery):

    text = (
        "🛒 <b>Магазин</b>\n\n"
        "Магазин пока пуст."
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )

# ================= COINS =================

@dp.callback_query(F.data == "coins")
async def coins(callback: types.CallbackQuery):

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
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🪙 <b>Монеты</b>\n\nВыберите действие:",
        reply_markup=keyboard
    )

# ================= REF SYSTEM =================

@dp.callback_query(F.data == "ref")
async def referral(callback: types.CallbackQuery):

    me = await bot.get_me()

    ref_link = (
        f"https://t.me/{me.username}"
        f"?start={callback.from_user.id}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="coins"
                )
            ]
        ]
    )

    text = (
        f"👥 <b>Реферальная система</b>\n\n"
        f"💸 За каждого друга: 10 монет\n\n"
        f"🔗 Ваша ссылка:\n"
        f"<code>{ref_link}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

# ================= CREATE BOT =================

waiting_for_token = {}

@dp.callback_query(F.data == "create_bot")
async def create_bot(callback: types.CallbackQuery):

    waiting_for_token[callback.from_user.id] = True

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="coins"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        "🤖 Отправьте токен бота из @BotFather",
        reply_markup=keyboard
    )

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

        text = (
            f"✅ Бот успешно подключён!\n\n"
            f"🤖 Имя: {me.first_name}\n"
            f"📛 Username: @{me.username}"
        )

        await message.answer(
            text,
            reply_markup=main_menu(message.from_user.id)
        )

    except:

        await message.answer(
            "❌ Неверный токен."
        )

# ================= ADMIN PANEL =================

@dp.callback_query(F.data == "admin")
async def admin(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM user_bots")
    bots = cursor.fetchone()[0]

    text = (
        f"⚙️ <b>Админ панель</b>\n\n"
        f"👥 Пользователей: <b>{users}</b>\n"
        f"🤖 Создано ботов: <b>{bots}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )

# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(callback: types.CallbackQuery):

    text = (
        f"🏠 Главное меню\n\n"
        f"Выберите действие:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )

# ================= RUN =================

async def main():

    await bot.delete_webhook(drop_pending_updates=True)

    print("Bot started")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
