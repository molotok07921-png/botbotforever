# =========================
# WORKING TELEGRAM BOT
# aiogram 3.x
# =========================

import asyncio
import logging
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# =========================
# SETTINGS
# =========================

TOKEN = "8565366731:AAHvZzapi6Q8I1x_z8Kxzseu1jnZgVLkg1s"
ADMIN_ID = 8075802187

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# BOT
# =========================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# =========================
# DATABASE
# =========================

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

# =========================
# USER STATE
# =========================

waiting_token = {}

# =========================
# FUNCTIONS
# =========================

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
        INSERT INTO users(
            user_id,
            ref_by
        )
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

# =========================
# MAIN MENU
# =========================

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

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    args = message.text.split()

    ref_by = None

    if len(args) > 1:
        try:
            ref_by = int(args[1])
        except:
            pass

    create_user(
        message.from_user.id,
        ref_by
    )

    text = (
        f"👋 Привет, "
        f"{message.from_user.first_name}!\n\n"
        f"🏠 Главное меню:"
    )

    await message.answer(
        text,
        reply_markup=main_menu(
            message.from_user.id
        )
    )

# =========================
# PROFILE
# =========================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = get_user(
        callback.from_user.id
    )

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: "
        f"<code>{callback.from_user.id}</code>\n\n"
        f"💰 Баланс: "
        f"<b>{user[1]}</b>\n\n"
        f"👥 Рефералы: "
        f"<b>{user[2]}</b>\n\n"
        f"🤖 Создано ботов: "
        f"<b>{user[3]}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(
            callback.from_user.id
        )
    )

# =========================
# WATCH
# =========================

@dp.callback_query(F.data == "watch")
async def watch(callback: CallbackQuery):

    text = (
        "👀 <b>Смотреть</b>\n\n"
        "Здесь можно добавить:\n"
        "• видео\n"
        "• задания\n"
        "• контент"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(
            callback.from_user.id
        )
    )

# =========================
# SHOP
# =========================

@dp.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):

    text = (
        "🛒 <b>Магазин</b>\n\n"
        "Магазин пока пуст."
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(
            callback.from_user.id
        )
    )

# =========================
# COINS
# =========================

@dp.callback_query(F.data == "coins")
async def coins(callback: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Реферальная система",
                    callback_data="ref"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Создать бота",
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
        "🪙 <b>Монеты</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

# =========================
# REFERRAL
# =========================

@dp.callback_query(F.data == "ref")
async def referral(callback: CallbackQuery):

    me = await bot.get_me()

    link = (
        f"https://t.me/"
        f"{me.username}"
        f"?start="
        f"{callback.from_user.id}"
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
        f"💸 Награда: 10 монет\n\n"
        f"🔗 Ваша ссылка:\n\n"
        f"<code>{link}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard
    )

# =========================
# CREATE BOT
# =========================

@dp.callback_query(F.data == "create_bot")
async def create_bot(callback: CallbackQuery):

    waiting_token[
        callback.from_user.id
    ] = True

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
        "🤖 Отправьте токен "
        "от @BotFather",
        reply_markup=keyboard
    )

# =========================
# TOKEN HANDLER
# =========================

@dp.message()
async def token_handler(message: Message):

    if message.from_user.id not in waiting_token:
        return

    token = message.text.strip()

    try:

        test_bot = Bot(token=token)

        me = await test_bot.get_me()

        cursor.execute(
            """
            INSERT INTO user_bots(
                owner_id,
                bot_token
            )
            VALUES(?, ?)
            """,
            (
                message.from_user.id,
                token
            )
        )

        cursor.execute(
            """
            UPDATE users
            SET bots_created =
            bots_created + 1
            WHERE user_id=?
            """,
            (
                message.from_user.id,
            )
        )

        db.commit()

        del waiting_token[
            message.from_user.id
        ]

        text = (
            f"✅ Бот подключён!\n\n"
            f"🤖 Имя: "
            f"{me.first_name}\n"
            f"📛 Username: "
            f"@{me.username}"
        )

        await message.answer(
            text,
            reply_markup=main_menu(
                message.from_user.id
            )
        )

    except Exception as e:

        await message.answer(
            "❌ Неверный токен."
        )

# =========================
# ADMIN PANEL
# =========================

@dp.callback_query(F.data == "admin")
async def admin(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM user_bots"
    )

    bots = cursor.fetchone()[0]

    text = (
        f"⚙️ <b>Админ панель</b>\n\n"
        f"👥 Пользователей: "
        f"<b>{users}</b>\n\n"
        f"🤖 Ботов создано: "
        f"<b>{bots}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(
            callback.from_user.id
        )
    )

# =========================
# BACK
# =========================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):

    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=main_menu(
            callback.from_user.id
        )
    )

# =========================
# RUN
# =========================

async def main():

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    print("BOT STARTED")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
