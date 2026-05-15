# requirements:
# pip install aiogram aiosqlite python-dotenv

import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties

TOKEN = "ТОКЕН_БОТА"
ADMIN_ID = 123456789  # твой telegram id

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# ---------------- БАЗА ДАННЫХ ---------------- #

async def init_db():
    async with aiosqlite.connect("database.db") as db:

        # пользователи
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            coins INTEGER DEFAULT 0,
            bots_created INTEGER DEFAULT 0
        )
        """)

        # созданные боты
        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER,
            bot_token TEXT,
            bot_username TEXT
        )
        """)

        await db.commit()


async def add_user(user_id, username, first_name):
    async with aiosqlite.connect("database.db") as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )

        user = await cursor.fetchone()

        if not user:
            await db.execute("""
            INSERT INTO users (
                user_id,
                username,
                first_name,
                coins,
                bots_created
            )
            VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                username,
                first_name,
                100,
                0
            ))

            await db.commit()


async def get_user(user_id):
    async with aiosqlite.connect("database.db") as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )

        return await cursor.fetchone()


# ---------------- КНОПКИ ---------------- #

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👤 Профиль",
                    callback_data="profile"
                ),

                InlineKeyboardButton(
                    text="🛍 Магазин",
                    callback_data="shop"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🚫 Галерея",
                    callback_data="gallery"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🤖 Создать бота (+10✨)",
                    callback_data="create_bot"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔥 Халява (+50✨)",
                    callback_data="bonus"
                )
            ]
        ]
    )


def admin_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💰 Выдать монеты",
                    callback_data="admin_give_coins"
                )
            ]
        ]
    )


# ---------------- START ---------------- #

@dp.message(CommandStart())
async def start(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    text = f"""
<b>Добро пожаловать в Bot Panel</b>

Выберите нужный раздел ниже 👇
"""

    await message.answer(
        text,
        reply_markup=main_menu()
    )


# ---------------- ПРОФИЛЬ ---------------- #

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(callback.from_user.id)

    text = f"""
<b>👤 Ваш профиль</b>

🆔 ID: <code>{user[0]}</code>
👤 Имя: {user[2]}
💎 Монеты: {user[3]}
🤖 Создано ботов: {user[4]}
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )


# ---------------- БОНУС ---------------- #

@dp.callback_query(F.data == "bonus")
async def bonus(callback: CallbackQuery):

    async with aiosqlite.connect("database.db") as db:

        await db.execute("""
        UPDATE users
        SET coins = coins + 50
        WHERE user_id = ?
        """, (callback.from_user.id,))

        await db.commit()

    await callback.answer(
        "Вы получили +50 монет",
        show_alert=True
    )


# ---------------- СОЗДАНИЕ БОТА ---------------- #

user_waiting_token = {}


@dp.callback_query(F.data == "create_bot")
async def create_bot(callback: CallbackQuery):

    user_waiting_token[callback.from_user.id] = True

    text = """
<b>🤖 Создание бота</b>

1. Создай бота через @BotFather
2. Отправь токен сюда

Пример:
<code>123456:ABC...</code>
"""

    await callback.message.edit_text(text)


@dp.message()
async def get_token(message: Message):

    if message.from_user.id not in user_waiting_token:
        return

    token = message.text.strip()

    try:
        test_bot = Bot(token=token)

        me = await test_bot.get_me()

        async with aiosqlite.connect("database.db") as db:

            await db.execute("""
            INSERT INTO user_bots (
                owner_id,
                bot_token,
                bot_username
            )
            VALUES (?, ?, ?)
            """, (
                message.from_user.id,
                token,
                me.username
            ))

            await db.execute("""
            UPDATE users
            SET
                coins = coins + 10,
                bots_created = bots_created + 1
            WHERE user_id = ?
            """, (message.from_user.id,))

            await db.commit()

        del user_waiting_token[message.from_user.id]

        text = f"""
✅ Бот успешно добавлен

🤖 Username: @{me.username}

💎 Вам начислено +10 монет
"""

        await message.answer(
            text,
            reply_markup=main_menu()
        )

    except Exception:

        await message.answer(
            "❌ Неверный токен"
        )


# ---------------- МАГАЗИН ---------------- #

@dp.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):

    text = """
🛍 <b>Магазин</b>

Тут можно добавить:
• VIP
• Покупку монет
• Подписки
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )


# ---------------- ГАЛЕРЕЯ ---------------- #

@dp.callback_query(F.data == "gallery")
async def gallery(callback: CallbackQuery):

    text = """
🚫 <b>Галерея</b>

Тут будет список созданных ботов.
"""

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )


# ---------------- АДМИН ПАНЕЛЬ ---------------- #

@dp.message(F.text == "/admin")
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙ Админ панель",
        reply_markup=admin_panel()
    )


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect("database.db") as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        users_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM user_bots"
        )

        bots_count = (await cursor.fetchone())[0]

    text = f"""
📊 <b>Статистика</b>

👤 Пользователей: {users_count}
🤖 Ботов создано: {bots_count}
"""

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel()
    )


# ---------------- ЗАПУСК ---------------- #

async def main():

    await init_db()

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())