# bot.py

import asyncio
import logging
import time
import requests
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties

from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# ======================================
# CONFIG
# ======================================

TOKEN = "TOKEN"
ADMIN_ID = 123456789

YOOMONEY_TOKEN = "YOOMONEY_API_TOKEN"
YOOMONEY_RECEIVER = "4100111111111111"

# ======================================
# LOGGING
# ======================================

logging.basicConfig(level=logging.INFO)

# ======================================
# BOT
# ======================================

bot = Bot(
    token=TOKEN,

    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# ======================================
# DATABASE
# ======================================

async def init_db():

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id INTEGER PRIMARY KEY,

            username TEXT,
            first_name TEXT,

            coins INTEGER DEFAULT 0,

            premium INTEGER DEFAULT 0,

            referrals INTEGER DEFAULT 0,

            invited_by INTEGER,

            bots_created INTEGER DEFAULT 0
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS user_bots (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            owner_id INTEGER,

            bot_token TEXT,
            bot_username TEXT
        )
        """)

        await db.commit()


# ======================================
# USER
# ======================================

async def add_user(user):

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user.id,)
        )

        check = await cursor.fetchone()

        if not check:

            await db.execute("""
            INSERT INTO users (

                user_id,
                username,
                first_name,
                coins

            )

            VALUES (?, ?, ?, ?)
            """, (

                user.id,
                user.username,
                user.first_name,
                50

            ))

            await db.commit()


async def get_user(user_id):

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )

        return await cursor.fetchone()


# ======================================
# REFERRAL SYSTEM
# ======================================

async def activate_referral(
    user_id,
    ref_id
):

    if user_id == ref_id:
        return

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        cursor = await db.execute("""
        SELECT invited_by
        FROM users
        WHERE user_id = ?
        """, (user_id,))

        data = await cursor.fetchone()

        if data and data[0]:
            return

        await db.execute("""
        UPDATE users
        SET invited_by = ?
        WHERE user_id = ?
        """, (

            ref_id,
            user_id

        ))

        await db.execute("""
        UPDATE users

        SET

            referrals = referrals + 1,
            coins = coins + 25

        WHERE user_id = ?
        """, (ref_id,))

        await db.commit()


# ======================================
# MENU
# ======================================

def menu(user_id):

    keyboard = [

        [
            InlineKeyboardButton(
                text="👤 Профиль",
                callback_data="profile"
            ),

            InlineKeyboardButton(
                text="💎 Premium",
                callback_data="premium"
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
                text="👥 Рефералы",
                callback_data="referrals"
            ),

            InlineKeyboardButton(
                text="💰 Купить монеты",
                callback_data="buy_coins"
            )
        ]
    ]

    if user_id == ADMIN_ID:

        keyboard.append([

            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats"
            )

        ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


# ======================================
# YOOMONEY
# ======================================

pending_payments = {}


def create_yoomoney_payment(
    amount,
    user_id,
    description
):

    label = (
        f"user_"
        f"{user_id}_"
        f"{int(time.time())}"
    )

    pay_url = (
        "https://yoomoney.ru/quickpay/confirm.xml?"
        f"receiver={YOOMONEY_RECEIVER}"
        "&quickpay-form=shop"
        f"&targets={description}"
        f"&sum={amount}"
        "&paymentType=SB"
        f"&label={label}"
    )

    return {

        "payment_id": label,
        "pay_url": pay_url

    }


def check_yoomoney_payment(
    payment_label
):

    headers = {

        "Authorization":
        f"Bearer {YOOMONEY_TOKEN}",

        "Content-Type":
        "application/x-www-form-urlencoded"
    }

    response = requests.post(

        "https://yoomoney.ru/api/operation-history",

        headers=headers,

        data={
            "label": payment_label,
            "records": 10
        }

    )

    if response.status_code != 200:
        return False

    data = response.json()

    operations = data.get(
        "operations",
        []
    )

    for operation in operations:

        if (
            operation.get("label")
            == payment_label
        ):

            if (
                operation.get("status")
                == "success"
            ):

                return True

    return False


# ======================================
# START
# ======================================

@dp.message(CommandStart())
async def start(message: Message):

    args = message.text.split()

    await add_user(
        message.from_user
    )

    if len(args) > 1:

        ref_arg = args[1]

        if ref_arg.startswith("ref_"):

            ref_id = int(
                ref_arg.split("_")[1]
            )

            await activate_referral(

                message.from_user.id,
                ref_id

            )

    text = f"""
<b>Minimal Panel</b>

Добро пожаловать,
{message.from_user.first_name}
"""

    await message.answer(

        text,

        reply_markup=menu(
            message.from_user.id
        )
    )


# ======================================
# PROFILE
# ======================================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    user = await get_user(
        callback.from_user.id
    )

    premium = (
        "Да"
        if user[4]
        else "Нет"
    )

    text = f"""
<b>Профиль</b>

🆔 ID:
<code>{user[0]}</code>

💰 Монеты:
{user[3]}

💎 Premium:
{premium}

👥 Рефералы:
{user[5]}

🤖 Ботов:
{user[7]}
"""

    await callback.message.edit_text(

        text,

        reply_markup=menu(
            callback.from_user.id
        )
    )


# ======================================
# REFERRALS
# ======================================

@dp.callback_query(F.data == "referrals")
async def referrals(callback: CallbackQuery):

    me = await bot.get_me()

    ref_link = (
        f"https://t.me/"
        f"{me.username}"
        f"?start=ref_"
        f"{callback.from_user.id}"
    )

    user = await get_user(
        callback.from_user.id
    )

    text = f"""
<b>Реферальная система</b>

👥 Приглашено:
{user[5]}

🎁 Награда:
+25 монет

🔗 Ссылка:

<code>{ref_link}</code>
"""

    await callback.message.edit_text(

        text,

        reply_markup=menu(
            callback.from_user.id
        )
    )


# ======================================
# CREATE BOT
# ======================================

waiting_token = {}

@dp.callback_query(F.data == "create_bot")
async def create_bot(callback: CallbackQuery):

    waiting_token[
        callback.from_user.id
    ] = True

    text = """
<b>Создание бота</b>

1. Создай бота через @BotFather
2. Отправь токен сюда
"""

    await callback.message.edit_text(
        text
    )


@dp.message()
async def token_handler(message: Message):

    if (
        message.from_user.id
        not in waiting_token
    ):
        return

    token = message.text.strip()

    try:

        temp_bot = Bot(token=token)

        me = await temp_bot.get_me()

        async with aiosqlite.connect(
            "database.db"
        ) as db:

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

                bots_created =
                bots_created + 1,

                coins =
                coins + 10

            WHERE user_id = ?
            """, (

                message.from_user.id,
            ))

            await db.commit()

        del waiting_token[
            message.from_user.id
        ]

        text = f"""
✅ Бот добавлен

🤖 @{me.username}

💰 +10 монет
"""

        await message.answer(

            text,

            reply_markup=menu(
                message.from_user.id
            )
        )

    except:

        await message.answer(
            "❌ Неверный токен"
        )


# ======================================
# PREMIUM
# ======================================

@dp.callback_query(F.data == "premium")
async def premium(callback: CallbackQuery):

    payment = create_yoomoney_payment(

        amount=199,

        user_id=callback.from_user.id,

        description="Premium"

    )

    pending_payments[
        payment["payment_id"]
    ] = {

        "user_id":
        callback.from_user.id,

        "type":
        "premium"
    }

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=payment["pay_url"]
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔄 Проверить оплату",
                    callback_data=
                    f"check_{payment['payment_id']}"
                )
            ]
        ]
    )

    await callback.message.edit_text(

        """
💎 Premium

199₽
""",

        reply_markup=keyboard
    )


# ======================================
# BUY COINS
# ======================================

@dp.callback_query(F.data == "buy_coins")
async def buy_coins(callback: CallbackQuery):

    payment = create_yoomoney_payment(

        amount=99,

        user_id=callback.from_user.id,

        description="500 coins"

    )

    pending_payments[
        payment["payment_id"]
    ] = {

        "user_id":
        callback.from_user.id,

        "type":
        "coins",

        "coins":
        500
    }

    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 Оплатить",
                    url=payment["pay_url"]
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔄 Проверить оплату",
                    callback_data=
                    f"check_{payment['payment_id']}"
                )
            ]
        ]
    )

    await callback.message.edit_text(

        """
💰 500 монет

99₽
""",

        reply_markup=keyboard
    )


# ======================================
# CHECK PAYMENT
# ======================================

@dp.callback_query(
    F.data.startswith("check_")
)
async def check_payment(
    callback: CallbackQuery
):

    payment_id = (
        callback.data
        .replace("check_", "")
    )

    payment = pending_payments.get(
        payment_id
    )

    if not payment:

        await callback.answer(

            "Платёж не найден",

            show_alert=True
        )

        return

    status = check_yoomoney_payment(
        payment_id
    )

    if not status:

        await callback.answer(

            "Оплата пока не найдена",

            show_alert=True
        )

        return

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        # PREMIUM
        if payment["type"] == "premium":

            await db.execute("""
            UPDATE users

            SET premium = 1

            WHERE user_id = ?
            """, (

                payment["user_id"],
            ))

        # COINS
        if payment["type"] == "coins":

            await db.execute("""
            UPDATE users

            SET coins = coins + ?

            WHERE user_id = ?
            """, (

                payment["coins"],
                payment["user_id"]

            ))

        await db.commit()

    del pending_payments[
        payment_id
    ]

    await callback.message.edit_text(
        "✅ Оплата подтверждена"
    )


# ======================================
# ADMIN STATS
# ======================================

@dp.callback_query(
    F.data == "admin_stats"
)
async def admin_stats(
    callback: CallbackQuery
):

    if (
        callback.from_user.id
        != ADMIN_ID
    ):
        return

    async with aiosqlite.connect(
        "database.db"
    ) as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )

        users = (
            await cursor.fetchone()
        )[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM user_bots"
        )

        bots = (
            await cursor.fetchone()
        )[0]

    text = f"""
<b>Статистика</b>

👤 Пользователей:
{users}

🤖 Ботов:
{bots}
"""

    await callback.message.edit_text(

        text,

        reply_markup=menu(
            callback.from_user.id
        )
    )


# ======================================
# MAIN
# ======================================

async def main():

    await init_db()

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
