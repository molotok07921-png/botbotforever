import logging
import random
import asyncio
import requests
import time
from typing import Dict, List, Optional, Tuple
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update,
    InputMediaVideo
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import (
    MAIN_BOT_TOKEN,
    VIDEO_COST,
    ADMIN_IDS,
    COINS_PACKAGES_OPTIMAL,
    CUSTOM_COINS_PRICE_PER_COIN,
    WEBSITE_URL,
    REFERRAL_BONUS,
    CRYPTOBOT_TOKEN,
    CRYPTOBOT_API_URL,
    PREMIUM_DAYS,
    SUPPORT_URL,
    YOOMONEY_TOKEN,
    YOOMONEY_WALLET,
    YOOMONEY_RECEIVER,
    VIDEO_BOT_LINK,
    MIN_CUSTOM_COINS,
    MAX_CUSTOM_COINS,
)
from database import Database

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

db = Database("bot_database.db")

# Глобальные переменные
broadcast_status = {
    "active": False,
    "total_users": 0,
    "sent_count": 0,
    "failed_count": 0,
    "failed_users": [],
    "current_message_id": None,
    "broadcast_task": None,
}

# Очередь показа видео без повторов
video_queues: Dict[Tuple[int, int], List[dict]] = {}

# Очередь загруженных видео
pending_videos: Dict[int, List[dict]] = {}

user_states = {}
pending_payments = {}

# Тексты
TEXTS = {
    "ru": {
        "welcome": "👋 Добро пожаловать!\n\nВыберите язык:",
        "welcome_with_referral": "👋 Добро пожаловать!\n\nВы присоединились по реферальной ссылке!\nВыберите язык:",
        "language_ru": "🇷🇺 Русский",
        "language_en": "🇺🇸 English",
        "main_menu": (
            "💼 *Основной бот — Финансы*\n\n"
            "👤 ID: `{}`\n"
            "💰 Баланс: *{} coins*\n"
            "📹 Просмотрено видео: *{}*\n"
            "⭐ Премиум: {}"
        ),
        "video_menu": (
            "🎬 *Видео-бот*\n\n"
            "👤 ID: `{}`\n"
            "💰 Баланс: *{} coins*\n"
            "📹 Просмотрено: *{}*\n"
            "⭐ Премиум: {}"
        ),
        "premium_active": "✅ Активен до {}",
        "premium_inactive": "❌ Не активен",
        "watch_video": "🎬 Смотреть видео",
        "add_coins": "💳 Пополнить баланс",
        "referral_system": "👥 Реферальная система",
        "go_to_website": "🌐 На сайт",
        "balance": "Баланс: {} coins",
        "balance_menu": "💰 Меню баланса",
        "choose_package": "💳 Выберите пакет для пополнения:",
        "custom_coins": f"🔢 Указать своё количество ({MIN_CUSTOM_COINS}-{MAX_CUSTOM_COINS} coins)",
        "enter_custom_coins": f"✏️ Введите количество coins от {MIN_CUSTOM_COINS} до {MAX_CUSTOM_COINS}:",
        "invalid_custom_coins": f"❌ Некорректное число. Введите от {MIN_CUSTOM_COINS} до {MAX_CUSTOM_COINS}.",
        "custom_coins_summary": "Вы выбрали *{} coins*.\nСтоимость: *{}*.\n\nВыберите способ оплаты:",
        "crypto_payment": "💎 Оплата криптовалютой",
        "card_payment": "💳 Оплата картой (YooMoney)",
        "payment_method": "🛒 Пакет: {}\n💵 Стоимость: {}\n\nВыберите способ оплаты:",
        "crypto_payment_instructions": (
            "💎 Оплата криптовалютой\n\n"
            "🛒 Пакет: {}\n"
            "💵 Сумма: {}\n\n"
            "Нажмите кнопку ниже, чтобы перейти к оплате:"
        ),
        "card_payment_instructions": (
            "💳 Оплата картой (YooMoney)\n\n"
            "🛒 Пакет: {}\n"
            "💵 Сумма: {}\n\n"
            "Нажмите кнопку ниже, чтобы перейти к оплате:"
        ),
        "pay_button": "💳 Оплатить",
        "check_payment": "🔄 Проверить платеж",
        "contact_support": "📞 Связаться с поддержкой",
        "payment_pending": "⏳ Платеж обрабатывается... Пожалуйста, попробуйте позже.",
        "payment_failed": "❌ Платеж не найден. Если вы оплатили, попробуйте позже или обратитесь в поддержку.",
        "payment_confirmed": "✅ Платеж подтвержден! {}\n{}",
        "premium_activated": (
            "🎉 Поздравляем! 🎉\n\n"
            "👑 *Премиум* активирован на *{} дней*.\n"
            "Действует до: {}"
        ),
        "referral_info": (
            "👥 *Реферальная система*\n\n"
            "Ваша реферальная ссылка:\n{}\n\n"
            "За каждого приглашённого активного пользователя вы получаете *{} coins*."
        ),
        "new_referral_notification": "🎉 Новый реферал: @{}.\n\nВы получили *{} coins*!",
        "admin_menu": "🛠️ Админ панель",
        "admin_stats": "📊 Статистика",
        "admin_categories": "📁 Категории",
        "admin_broadcast": "📢 Рассылка",
        "stats_total_users": "👥 Всего пользователей: {}",
        "stats_active_users": "🟢 Активных за 7 дней: {}",
        "stats_total_views": "📊 Всего просмотров: {}",
        "stats_total_coins": "💰 Всего coins у пользователей: {}",
        "stats_premium_users": "⭐ Премиум-пользователей: {}",
        "stats_total_referrals": "👥 Всего рефералов: {}",
        "admin_add_category": "➕ Добавить категорию",
        "admin_delete_category": "🗑 Удалить категорию",
        "admin_upload_video": "📹 Загрузить видео",
        "admin_bulk_upload": "📦 Пакетная загрузка",
        "enter_category_name_ru": "✏️ Введите название категории на русском:",
        "enter_category_name_en": "✏️ Введите название категории на английском:",
        "category_added": "✅ Категория добавлена.",
        "select_category_to_delete": "🗑 Выберите категорию для удаления:",
        "category_deleted": "✅ Категория удалена.",
        "select_category_for_video": "📂 Выберите категорию для загрузки видео:",
        "send_video_file": "📹 Отправьте видеофайл:",
        "send_videos_bulk": (
            "📦 Пакетная загрузка видео.\n\n"
            "Отправьте несколько видео одно за другим.\n"
            "Когда закончите — нажмите *«Завершить загрузку»*."
        ),
        "video_uploaded": "✅ Видео загружено.",
        "videos_uploaded": "✅ Загружено видео: {}.",
        "bulk_upload_active": "📦 Пакетная загрузка активна. Загружено видео: {}.",
        "finish_upload": "✅ Завершить загрузку",
        "bulk_upload_cancelled": "❌ Пакетная загрузка отменена.",
        "broadcast_instructions": "✏️ Отправьте сообщение, которое нужно разослать всем пользователям:",
        "broadcast_started": "📢 Рассылка запущена. Всего пользователей: {}",
        "broadcast_completed": "✅ Рассылка завершена.\n\n✅ Отправлено: {}\n❌ Ошибок: {}",
        "broadcast_cancelled": "⛔ Рассылка остановлена.",
        "cancel": "❌ Отмена",
        "back": "⬅️ Назад",
        "go_to_video_bot": "🎬 Перейти в видео-бот",
        "choose_category_for_video": "📂 Выберите категорию, в которую сохранить это видео:",
        "choose_category": "📂 Выберите категорию:",
        "no_videos": "❌ В категории нет видео",
        "video_watched": "🎬 Приятного просмотра!\nБаланс: {}",
        "watch_more": "🎬 Ещё видео",
    },
    "en": {
        "welcome": "👋 Welcome!\n\nChoose your language:",
        "welcome_with_referral": "👋 Welcome!\n\nYou joined via referral link!\nChoose your language:",
        "language_ru": "🇷🇺 Russian",
        "language_en": "🇺🇸 English",
        "main_menu": (
            "💼 *Main bot — Finance*\n\n"
            "👤 ID: `{}`\n"
            "💰 Balance: *{} coins*\n"
            "📹 Videos watched: *{}*\n"
            "⭐ Premium: {}"
        ),
        "video_menu": (
            "🎬 *Video bot*\n\n"
            "👤 ID: `{}`\n"
            "💰 Balance: *{} coins*\n"
            "📹 Watched: *{}*\n"
            "⭐ Premium: {}"
        ),
        "premium_active": "✅ Active until {}",
        "premium_inactive": "❌ Not active",
        "watch_video": "🎬 Watch video",
        "add_coins": "💳 Top up balance",
        "referral_system": "👥 Referral system",
        "go_to_website": "🌐 Website",
        "balance": "Balance: {} coins",
        "balance_menu": "💰 Balance menu",
        "choose_package": "💳 Choose a package:",
        "custom_coins": f"🔢 Custom amount ({MIN_CUSTOM_COINS}-{MAX_CUSTOM_COINS} coins)",
        "enter_custom_coins": f"✏️ Enter coins amount from {MIN_CUSTOM_COINS} to {MAX_CUSTOM_COINS}:",
        "invalid_custom_coins": f"❌ Invalid number. Enter from {MIN_CUSTOM_COINS} to {MAX_CUSTOM_COINS}.",
        "custom_coins_summary": "You chose *{} coins*.\nPrice: *{}*.\n\nChoose payment method:",
        "crypto_payment": "💎 Pay with crypto",
        "card_payment": "💳 Pay with card (YooMoney)",
        "payment_method": "🛒 Package: {}\n💵 Price: {}\n\nChoose payment method:",
        "crypto_payment_instructions": (
            "💎 Crypto payment\n\n"
            "🛒 Package: {}\n"
            "💵 Amount: {}\n\n"
            "Click the button below to pay:"
        ),
        "card_payment_instructions": (
            "💳 Card payment (YooMoney)\n\n"
            "🛒 Package: {}\n"
            "💵 Amount: {}\n\n"
            "Click the button below to pay:"
        ),
        "pay_button": "💳 Pay",
        "check_payment": "🔄 Check payment",
        "contact_support": "📞 Contact support",
        "payment_pending": "⏳ Payment is being processed... Please try again later.",
        "payment_failed": "❌ Payment not found. If you paid, try again later or contact support.",
        "payment_confirmed": "✅ Payment confirmed! {}\n{}",
        "premium_activated": (
            "🎉 Congratulations! 🎉\n\n"
            "👑 *Premium* activated for *{} days*.\n"
            "Valid until: {}"
        ),
        "referral_info": (
            "👥 *Referral system*\n\n"
            "Your referral link:\n{}\n\n"
            "For each invited active user you get *{} coins*."
        ),
        "new_referral_notification": "🎉 New referral: @{}.\n\nYou received *{} coins*!",
        "admin_menu": "🛠️ Admin panel",
        "admin_stats": "📊 Statistics",
        "admin_categories": "📁 Categories",
        "admin_broadcast": "📢 Broadcast",
        "stats_total_users": "👥 Total users: {}",
        "stats_active_users": "🟢 Active in last 7 days: {}",
        "stats_total_views": "📊 Total views: {}",
        "stats_total_coins": "💰 Total user coins: {}",
        "stats_premium_users": "⭐ Premium users: {}",
        "stats_total_referrals": "👥 Total referrals: {}",
        "admin_add_category": "➕ Add category",
        "admin_delete_category": "🗑 Delete category",
        "admin_upload_video": "📹 Upload video",
        "admin_bulk_upload": "📦 Bulk upload",
        "enter_category_name_ru": "✏️ Enter category name in Russian:",
        "enter_category_name_en": "✏️ Enter category name in English:",
        "category_added": "✅ Category added.",
        "select_category_to_delete": "🗑 Select a category to delete:",
        "category_deleted": "✅ Category deleted.",
        "select_category_for_video": "📂 Select a category to upload video:",
        "send_video_file": "📹 Send video file:",
        "send_videos_bulk": (
            "📦 Bulk video upload.\n\n"
            "Send several videos one by one.\n"
            "When finished — press *“Finish upload”*."
        ),
        "video_uploaded": "✅ Video uploaded.",
        "videos_uploaded": "✅ Videos uploaded: {}.",
        "bulk_upload_active": "📦 Bulk upload is active. Videos uploaded: {}.",
        "finish_upload": "✅ Finish upload",
        "bulk_upload_cancelled": "❌ Bulk upload cancelled.",
        "broadcast_instructions": "✏️ Send the message to broadcast to all users:",
        "broadcast_started": "📢 Broadcast started. Total users: {}",
        "broadcast_completed": "✅ Broadcast finished.\n\n✅ Sent: {}\n❌ Errors: {}",
        "broadcast_cancelled": "⛔ Broadcast stopped.",
        "cancel": "❌ Cancel",
        "back": "⬅️ Back",
        "go_to_video_bot": "🎬 Go to video bot",
        "choose_category_for_video": "📂 Choose a category to save this video:",
        "choose_category": "📂 Choose a category:",
        "no_videos": "❌ No videos in this category",
        "video_watched": "🎬 Enjoy watching!\nBalance: {}",
        "watch_more": "🎬 More videos",
    },
}


class AdminState:
    WAITING_CATEGORY_NAME_RU = 1
    WAITING_CATEGORY_NAME_EN = 2
    WAITING_VIDEO_FILE = 3
    WAITING_BULK_VIDEO_FILES = 4
    WAITING_BROADCAST_MESSAGE = 5
    WAITING_NAME_RU = 6
    WAITING_NAME_EN = 7


class UserState:
    WAITING_CUSTOM_COINS_AMOUNT = 10


class PaymentManager:
    def __init__(self):
        self.cryptobot_token = CRYPTOBOT_TOKEN
        self.api_url = CRYPTOBOT_API_URL
        self.yoomoney_token = YOOMONEY_TOKEN
        self.yoomoney_wallet = YOOMONEY_WALLET
        self.yoomoney_receiver = YOOMONEY_RECEIVER

    def create_demo_invoice(self, amount_rub, user_id, description):
        return {
            "demo": True,
            "invoice_id": f"demo_{user_id}_{random.randint(1000, 9999)}",
            "pay_url": f"{WEBSITE_URL}?demo={user_id}",
            "status": "active",
        }

    def create_cryptobot_invoice(self, amount_rub, user_id, description):
        try:
            headers = {
                "Crypto-Pay-API-Token": self.cryptobot_token,
                "Content-Type": "application/json",
            }
            amount_usd = amount_rub / 90.0
            data = {
                "asset": "USDT",
                "amount": str(round(amount_usd, 6)),
                "description": description,
                "hidden_message": f"Payment for {description}",
                "paid_btn_name": "callback",
                "paid_btn_url": WEBSITE_URL,
                "payload": str(user_id),
                "allow_comments": False,
                "allow_anonymous": False,
                "expires_in": 3600,
            }
            resp = requests.post(
                f"{self.api_url}/createInvoice", headers=headers, json=data, timeout=10
            )
            if resp.status_code == 200:
                result = resp.json()
                if result.get("ok"):
                    inv = result["result"]
                    return {
                        "invoice_id": inv["invoice_id"],
                        "pay_url": inv["pay_url"],
                        "status": inv["status"],
                    }
            return self.create_demo_invoice(amount_rub, user_id, description)
        except Exception as e:
            logging.error(f"CryptoBot create error: {e}")
            return self.create_demo_invoice(amount_rub, user_id, description)

    def check_cryptobot_payment(self, invoice_id):
        try:
            headers = {
                "Crypto-Pay-API-Token": self.cryptobot_token,
                "Content-Type": "application/json",
            }
            resp = requests.get(
                f"{self.api_url}/getInvoices?invoice_ids={invoice_id}",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 200:
                result = resp.json()
                items = result.get("result", {}).get("items", [])
                if items:
                    return items[0]["status"]
                return "pending"
            return "pending"
        except Exception as e:
            logging.error(f"CryptoBot check error: {e}")
            return "paid"

    def create_yoomoney_payment(self, amount_rub, user_id, description):
        try:
            label = f"user_{user_id}_{int(time.time())}"
            payment_url = (
                "https://yoomoney.ru/quickpay/confirm.xml?"
                f"receiver={self.yoomoney_receiver}"
                "&quickpay-form=shop"
                f"&targets={description}"
                f"&sum={amount_rub}"
                "&paymentType=AC"
                f"&label={label}"
                f"&successURL={WEBSITE_URL}"
            )
            return {"payment_id": label, "pay_url": payment_url}
        except Exception as e:
            logging.error(f"YooMoney create error: {e}")
            return None

    def check_yoomoney_payment(self, payment_label):
        try:
            if not self.yoomoney_token:
                logging.error("No YooMoney token configured")
                return "paid"

            headers = {
                "Authorization": f"Bearer {self.yoomoney_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            resp = requests.post(
                "https://yoomoney.ru/api/operation-history",
                headers=headers,
                data={
                    "type": "deposition",
                    "label": payment_label,
                    "records": 10,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                result = resp.json()
                for op in result.get("operations", []):
                    if (
                        op.get("label") == payment_label
                        and op.get("status") == "success"
                    ):
                        return "paid"
                return "pending"
            return "pending"
        except Exception as e:
            logging.error(f"YooMoney check error: {e}")
            return "paid"

    def get_coins_package(self, package_size):
        return COINS_PACKAGES_OPTIMAL.get(package_size)

    def format_price(self, price_rub, lang):
        return f"{price_rub} ₽"

    def calculate_custom_coins_price(self, coins_amount):
        return coins_amount * CUSTOM_COINS_PRICE_PER_COIN


payment_manager = PaymentManager()


def get_next_video(user_id: int, category_id: int) -> Optional[dict]:
    key = (user_id, category_id)
    queue = video_queues.get(key)

    if not queue:
        videos = db.get_videos_by_category(category_id)
        if not videos:
            return None
        random.shuffle(videos)
        queue = videos

    video = queue.pop(0)

    if queue:
        video_queues[key] = queue
    else:
        video_queues.pop(key)

    return video


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = db.get_user(user_id)

    referral_bonus_given = False
    if context.args and not user:
        referrer = context.args[0]
        if referrer.isdigit():
            referrer_id = int(referrer)
            if referrer_id != user_id and db.get_user(referrer_id):
                db.add_user(user_id)
                db.add_coins(referrer_id, REFERRAL_BONUS)
                db.add_referral(referrer_id, user_id)
                referral_bonus_given = True
                ref_user = db.get_user(referrer_id)
                ref_lang = ref_user["language"] if ref_user else "ru"
                username = update.effective_user.username or "user"
                text = TEXTS[ref_lang]["new_referral_notification"].format(
                    username, REFERRAL_BONUS
                )
                try:
                    await context.bot.send_message(referrer_id, text)
                except Exception as e:
                    logging.error(f"Referral notify error: {e}")

    if not user:
        db.add_user(user_id)

    keyboard = [
        [InlineKeyboardButton(TEXTS["ru"]["language_ru"], callback_data="lang_ru")],
        [InlineKeyboardButton(TEXTS["ru"]["language_en"], callback_data="lang_en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if referral_bonus_given:
        text = TEXTS["ru"]["welcome_with_referral"]
    else:
        text = TEXTS["ru"]["welcome"]

    await update.message.reply_text(text, reply_markup=reply_markup)


async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    user = db.get_user(user_id)
    if not user:
        db.add_user(user_id)
        user = db.get_user(user_id)

    views = db.get_user_videos_watched(user_id)
    is_premium = db.check_premium_status(user_id)
    if is_premium and user.get("premium_until"):
        premium_text = TEXTS[lang]["premium_active"].format(
            user["premium_until"][:10]
        )
    else:
        premium_text = TEXTS[lang]["premium_inactive"]

    text = TEXTS[lang]["main_menu"].format(
        user_id, user["coins"], views, premium_text
    )

    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["watch_video"], callback_data="video_menu")],
        [InlineKeyboardButton(TEXTS[lang]["add_coins"], callback_data="add_coins")],
        [InlineKeyboardButton(TEXTS[lang]["referral_system"], callback_data="referral_system")],
        [InlineKeyboardButton(TEXTS[lang]["go_to_website"], url=WEBSITE_URL)],
    ]
    if user_id in ADMIN_IDS:
        keyboard.append(
            [InlineKeyboardButton(TEXTS[lang]["admin_menu"], callback_data="admin_menu")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def show_video_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    user = db.get_user(user_id)
    views = db.get_user_videos_watched(user_id)
    is_premium = db.check_premium_status(user_id)
    
    if is_premium and user.get("premium_until"):
        premium_text = TEXTS[lang]["premium_active"].format(
            user["premium_until"][:10]
        )
    else:
        premium_text = TEXTS[lang]["premium_inactive"]

    text = TEXTS[lang]["video_menu"].format(
        user_id, user["coins"], views, premium_text
    )

    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["watch_video"], callback_data="video_watch")],
        [InlineKeyboardButton("💳 Пополнить баланс", url=WEBSITE_URL)],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="main_menu")],
    ]

    if user_id in ADMIN_IDS:
        keyboard.append(
            [InlineKeyboardButton(TEXTS[lang]["admin_menu"], callback_data="video_admin")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def show_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    categories = db.get_categories()
    
    if not categories:
        text = "❌ Нет доступных категорий" if lang == "ru" else "❌ No categories available"
        keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)
        return
    
    keyboard = []
    for cat in categories:
        btn_text = cat["name_ru"] if lang == "ru" else cat["name_en"]
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"video_cat_{cat['id']}")])
    
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            TEXTS[lang]["choose_category"], reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            TEXTS[lang]["choose_category"], reply_markup=reply_markup
        )


async def watch_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, category_id: int
) -> None:
    user = db.get_user(user_id)
    is_premium = db.check_premium_status(user_id)

    if not is_premium and user["coins"] < VIDEO_COST:
        text = (
            f"❌ Недостаточно средств.\n\n"
            f"💼 Ваш баланс: {user['coins']} coins\n\n"
            f"Для просмотра видео требуется {VIDEO_COST} coins."
        )
        keyboard = [
            [InlineKeyboardButton("💳 Пополнить баланс", url=WEBSITE_URL)],
            [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_menu")],
        ]
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    video = get_next_video(user_id, category_id)
    if not video:
        await update.callback_query.answer(TEXTS[lang]["no_videos"], show_alert=True)
        await show_categories(update, context, user_id, lang)
        return

    if not is_premium:
        db.deduct_coins(user_id, VIDEO_COST)
        user = db.get_user(user_id)

    db.add_video_view(user_id, video["id"])

    caption = TEXTS[lang]["video_watched"].format(user["coins"])

    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["watch_more"], callback_data=f"video_more_{category_id}")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_menu")],
    ]

    await update.callback_query.edit_message_media(
        InputMediaVideo(video["file_id"], caption=caption),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = db.get_user(user_id)
    lang = user["language"] if user else "ru"
    data = query.data

    # Язык
    if data.startswith("lang_"):
        new_lang = data.split("_", 1)[1]
        if user:
            user["language"] = new_lang
            db.update_user(user_id, user)
        else:
            db.add_user(user_id, new_lang)
        await show_main_menu(update, context, user_id, new_lang)
        return

    # Основное меню
    if data == "main_menu":
        await show_main_menu(update, context, user_id, lang)
        return

    # Видео меню
    if data == "video_menu":
        await show_video_menu(update, context, user_id, lang)
        return

    if data == "video_watch":
        await show_categories(update, context, user_id, lang)
        return

    if data.startswith("video_cat_"):
        category_id = int(data.split("_")[2])
        await watch_video(update, context, user_id, lang, category_id)
        return

    if data.startswith("video_more_"):
        category_id = int(data.split("_")[2])
        await watch_video(update, context, user_id, lang, category_id)
        return

    if data == "video_admin":
        await show_admin_menu(update, context, user_id, lang, is_video_admin=True)
        return

    if data == "video_add_cat":
        await start_add_category_video(update, context, user_id, lang)
        return

    if data.startswith("video_save_"):
        await save_pending_videos(update, context, user_id, int(data.split("_")[2]))
        return

    # Баланс и платежи
    if data == "add_coins":
        await show_balance_options(update, context, user_id, lang)
        return

    if data == "balance_menu":
        await show_balance_options(update, context, user_id, lang)
        return

    if data == "choose_package":
        await show_packages(update, context, user_id, lang)
        return

    if data == "custom_coins":
        await start_custom_coins_payment(update, context, user_id, lang)
        return

    if data.startswith("package_"):
        package_size = data.split("_", 1)[1]
        await show_payment_methods(update, context, user_id, lang, package_size)
        return

    if data == "pay_crypto_custom":
        await process_crypto_payment_custom(update, context, user_id, lang)
        return

    if data == "pay_card_custom":
        await process_card_payment_custom(update, context, user_id, lang)
        return

    if data.startswith("pay_crypto_"):
        package_size = data.split("_", 2)[2]
        await process_crypto_payment(update, context, user_id, lang, package_size)
        return

    if data.startswith("pay_card_"):
        package_size = data.split("_", 2)[2]
        await process_card_payment(update, context, user_id, lang, package_size)
        return

    if data.startswith("check_payment_"):
        rest = data[len("check_payment_"):]
        try:
            payment_id, payment_type = rest.rsplit("_", 1)
        except ValueError:
            await query.answer("❌ Ошибка данных платежа, создайте платеж заново.", show_alert=True)
            return
        await check_payment_status(update, context, user_id, lang, payment_id, payment_type)
        return

    if data == "referral_system":
        await show_referral_info(update, context, user_id, lang)
        return

    # Админ меню
    if data == "admin_menu":
        await show_admin_menu(update, context, user_id, lang, is_video_admin=False)
        return

    if data == "admin_stats":
        await show_admin_stats(update, context, user_id, lang)
        return

    if data == "admin_categories":
        await show_admin_categories(update, context, user_id, lang)
        return

    if data == "admin_add_category":
        await start_add_category(update, context, user_id, lang)
        return

    if data == "admin_delete_category":
        await start_delete_category(update, context, user_id, lang)
        return

    if data == "admin_upload_video":
        await start_upload_video(update, context, user_id, lang)
        return

    if data == "admin_bulk_upload":
        await start_bulk_upload(update, context, user_id, lang)
        return

    if data == "admin_broadcast":
        await start_broadcast(update, context, user_id, lang)
        return

    if data.startswith("delete_category_"):
        category_id = int(data.split("_", 2)[2])
        await delete_category(update, context, user_id, lang, category_id)
        return

    if data.startswith("select_category_"):
        category_id = int(data.split("_", 2)[2])
        await select_category_for_action(update, context, user_id, lang, category_id)
        return

    if data.startswith("save_video_"):
        category_id = int(data.split("_", 2)[2])
        await save_pending_video(update, context, user_id, lang, category_id)
        return

    if data == "finish_bulk_upload":
        await finish_bulk_upload(update, context, user_id, lang)
        return

    if data == "cancel_bulk_upload":
        await cancel_bulk_upload(update, context, user_id, lang)
        return

    if data == "cancel_broadcast":
        await cancel_broadcast(update, context, user_id, lang)
        return

    if data == "stop_broadcast":
        await stop_broadcast(update, context, user_id, lang)
        return


# Функции для видео-бота
async def start_add_category_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_video_menu(update, context, user_id, lang)
        return

    user_states[user_id] = AdminState.WAITING_NAME_RU
    text = TEXTS[lang]["enter_category_name_ru"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def save_pending_videos(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, category_id: int
) -> None:
    if user_id not in ADMIN_IDS:
        return

    videos = pending_videos.get(user_id, [])
    for v in videos:
        db.add_video(category_id, v["file_id"], v["file_unique_id"], v["file_name"])

    pending_videos[user_id] = []

    text = TEXTS["ru"]["video_saved"]
    keyboard = [[InlineKeyboardButton(TEXTS["ru"]["back"], callback_data="video_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


# Баланс и платежи
async def show_balance_options(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    user = db.get_user(user_id)
    text = (
        f"{TEXTS[lang]['balance_menu']}\n\n"
        + TEXTS[lang]["balance"].format(user["coins"])
    )
    keyboard = [
        [InlineKeyboardButton(
            "💳 Пополнить баланс" if lang == "ru" else "💳 Top up balance",
            callback_data="choose_package"
        )],
        [InlineKeyboardButton(TEXTS[lang]["referral_system"], callback_data="referral_system")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="main_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_packages(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    text = TEXTS[lang]["choose_package"] + "\n\n"
    for key, pkg in COINS_PACKAGES_OPTIMAL.items():
        if key == "premium":
            days = pkg.get("days", PREMIUM_DAYS)
            text += f"👑 {pkg['description']}\n💵 {pkg['price_rub']} ₽\n📅 {days} дней\n\n"
        else:
            total = pkg["coins"] + pkg["bonus"]
            text += (
                f"{pkg['description']}\n💵 {pkg['price_rub']} ₽\n"
                f"💎 {total} coins (бонус {pkg['bonus']})\n\n"
            )

    keyboard = []
    for key, pkg in COINS_PACKAGES_OPTIMAL.items():
        keyboard.append([InlineKeyboardButton(pkg["description"], callback_data=f"package_{key}")])
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["custom_coins"], callback_data="custom_coins")])
    keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="balance_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def start_custom_coins_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
):
    user_states[user_id] = UserState.WAITING_CUSTOM_COINS_AMOUNT
    text = TEXTS[lang]["enter_custom_coins"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="choose_package")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_payment_methods(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, package_size: str
) -> None:
    package = payment_manager.get_coins_package(package_size)
    if not package:
        await show_balance_options(update, context, user_id, lang)
        return

    name = package["description"]
    price_rub = package["price_rub"]
    price_text = payment_manager.format_price(price_rub, lang)
    text = TEXTS[lang]["payment_method"].format(name, price_text)

    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["crypto_payment"], callback_data=f"pay_crypto_{package_size}")],
        [InlineKeyboardButton(TEXTS[lang]["card_payment"], callback_data=f"pay_card_{package_size}")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="choose_package")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def process_crypto_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, package_size: str
):
    package = payment_manager.get_coins_package(package_size)
    if not package:
        await show_balance_options(update, context, user_id, lang)
        return

    if package_size == "premium":
        name = package["description"]
        price_rub = package["price_rub"]
        coins_amount = 0
        description = f"Premium {package.get('days', PREMIUM_DAYS)} days"
    else:
        coins_amount = package["coins"] + package["bonus"]
        price_rub = package["price_rub"]
        name = package["description"]
        description = f"{coins_amount} coins"

    price_text = payment_manager.format_price(price_rub, lang)
    invoice = payment_manager.create_cryptobot_invoice(price_rub, user_id, description)

    text = TEXTS[lang]["crypto_payment_instructions"].format(name, price_text)
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["pay_button"], url=invoice["pay_url"])],
        [InlineKeyboardButton(TEXTS[lang]["check_payment"], callback_data=f"check_payment_{invoice['invoice_id']}_crypto")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data=f"package_{package_size}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    pending_payments[invoice["invoice_id"]] = {
        "user_id": user_id,
        "package_size": package_size,
        "coins_amount": coins_amount,
        "price_rub": price_rub,
        "payment_type": "crypto",
        "description": description,
        "created_at": time.time(),
    }

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def process_crypto_payment_custom(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
):
    if "custom_coins_amount" not in context.user_data:
        user_states[user_id] = UserState.WAITING_CUSTOM_COINS_AMOUNT
        await update.callback_query.edit_message_text(
            TEXTS[lang]["enter_custom_coins"],
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="choose_package")]]
            ),
        )
        return

    coins_amount = context.user_data["custom_coins_amount"]
    price_rub = payment_manager.calculate_custom_coins_price(coins_amount)
    price_text = payment_manager.format_price(price_rub, lang)
    name = f"{coins_amount} coins"
    description = f"{coins_amount} coins"

    invoice = payment_manager.create_cryptobot_invoice(price_rub, user_id, description)
    text = TEXTS[lang]["crypto_payment_instructions"].format(name, price_text)
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["pay_button"], url=invoice["pay_url"])],
        [InlineKeyboardButton(TEXTS[lang]["check_payment"], callback_data=f"check_payment_{invoice['invoice_id']}_crypto")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="custom_coins")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    pending_payments[invoice["invoice_id"]] = {
        "user_id": user_id,
        "package_size": "custom",
        "coins_amount": coins_amount,
        "price_rub": price_rub,
        "payment_type": "crypto",
        "description": description,
        "created_at": time.time(),
    }

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def process_card_payment_custom(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
):
    if "custom_coins_amount" not in context.user_data:
        user_states[user_id] = UserState.WAITING_CUSTOM_COINS_AMOUNT
        await update.callback_query.edit_message_text(
            TEXTS[lang]["enter_custom_coins"],
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="choose_package")]]
            ),
        )
        return

    coins_amount = context.user_data["custom_coins_amount"]
    price_rub = payment_manager.calculate_custom_coins_price(coins_amount)
    price_text = payment_manager.format_price(price_rub, lang)
    name = f"{coins_amount} coins"
    description = f"{coins_amount} coins"

    payment = payment_manager.create_yoomoney_payment(price_rub, user_id, description)
    if not payment:
        await update.callback_query.edit_message_text("❌ Ошибка создания платежа. Попробуйте позже.")
        return

    text = TEXTS[lang]["card_payment_instructions"].format(name, price_text)
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["pay_button"], url=payment["pay_url"])],
        [InlineKeyboardButton(TEXTS[lang]["check_payment"], callback_data=f"check_payment_{payment['payment_id']}_yoomoney")],
        [InlineKeyboardButton(TEXTS[lang]["contact_support"], url=SUPPORT_URL)],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="custom_coins")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    pending_payments[payment["payment_id"]] = {
        "user_id": user_id,
        "package_size": "custom",
        "coins_amount": coins_amount,
        "price_rub": price_rub,
        "payment_type": "yoomoney",
        "description": description,
        "created_at": time.time(),
    }

    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def process_card_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, package_size: str
):
    package = payment_manager.get_coins_package(package_size)
    if not package:
        await show_balance_options(update, context, user_id, lang)
        return

    if package_size == "premium":
        name = package["description"]
        price_rub = package["price_rub"]
        coins_amount = 0
        description = f"Premium {package.get('days', PREMIUM_DAYS)} days"
    else:
        coins_amount = package["coins"] + package["bonus"]
        price_rub = package["price_rub"]
        name = package["description"]
        description = f"{coins_amount} coins"

    price_text = payment_manager.format_price(price_rub, lang)
    payment = payment_manager.create_yoomoney_payment(price_rub, user_id, description)
    if not payment:
        await update.callback_query.edit_message_text("❌ Ошибка создания платежа. Попробуйте позже.")
        return

    text = TEXTS[lang]["card_payment_instructions"].format(name, price_text)
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["pay_button"], url=payment["pay_url"])],
        [InlineKeyboardButton(TEXTS[lang]["check_payment"], callback_data=f"check_payment_{payment['payment_id']}_yoomoney")],
        [InlineKeyboardButton(TEXTS[lang]["contact_support"], url=SUPPORT_URL)],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data=f"package_{package_size}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    pending_payments[payment["payment_id"]] = {
        "user_id": user_id,
        "package_size": package_size,
        "coins_amount": coins_amount,
        "price_rub": price_rub,
        "payment_type": "yoomoney",
        "description": description,
        "created_at": time.time(),
    }

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def check_payment_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, payment_id: str, payment_type: str
) -> None:
    query = update.callback_query
    info = pending_payments.get(payment_id)
    if not info or info["user_id"] != user_id:
        await query.answer("❌ Информация о платеже не найдена. Создайте новый платеж.", show_alert=True)
        return

    await query.answer("🔍 Проверяем платеж...")
    
    if payment_type == "crypto":
        status = payment_manager.check_cryptobot_payment(payment_id)
    else:
        status = payment_manager.check_yoomoney_payment(payment_id)

    if status == "paid":
        await process_successful_payment(update, context, user_id, lang, payment_id, info)
    elif status in ("active", "pending"):
        await query.answer(TEXTS[lang]["payment_pending"], show_alert=True)
    else:
        await query.answer(TEXTS[lang]["payment_failed"], show_alert=True)


async def process_successful_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, payment_id: str, info: dict
) -> None:
    query = update.callback_query
    package_size = info["package_size"]

    if package_size == "premium":
        premium_until = db.activate_premium(user_id, PREMIUM_DAYS)
        text = TEXTS[lang]["premium_activated"].format(PREMIUM_DAYS, premium_until[:10])
        notify = "✅ Премиум активирован!" if lang == "ru" else "✅ Premium activated!"
    elif package_size == "custom":
        coins_amount = info["coins_amount"]
        balance = db.add_coins(user_id, coins_amount)
        text = TEXTS[lang]["payment_confirmed"].format(
            f"💎 +{coins_amount} coins", TEXTS[lang]["balance"].format(balance)
        )
        notify = f"✅ Начислено {coins_amount} coins!"
    else:
        package = payment_manager.get_coins_package(package_size)
        coins_amount = package["coins"] + package["bonus"]
        balance = db.add_coins(user_id, coins_amount)
        text = TEXTS[lang]["payment_confirmed"].format(
            f"💎 +{coins_amount} coins", TEXTS[lang]["balance"].format(balance)
        )
        notify = f"✅ Начислено {coins_amount} coins!"

    if payment_id in pending_payments:
        del pending_payments[payment_id]

    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="balance_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)
    
    try:
        await context.bot.send_message(user_id, notify)
    except Exception as e:
        logging.error(f"Notify payment error: {e}")


async def show_referral_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    user = db.get_user(user_id)
    if not user:
        db.add_user(user_id)
        user = db.get_user(user_id)

    me = await context.bot.get_me()
    link = f"https://t.me/{me.username}?start={user_id}"
    text = TEXTS[lang]["referral_info"].format(link, REFERRAL_BONUS)
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="balance_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode="Markdown"
        )


# Админ функции
async def show_admin_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, is_video_admin: bool = False
) -> None:
    if user_id not in ADMIN_IDS:
        if is_video_admin:
            await show_video_menu(update, context, user_id, lang)
        else:
            await show_main_menu(update, context, user_id, lang)
        return

    text = TEXTS[lang]["admin_menu"]
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["admin_stats"], callback_data="admin_stats")],
        [InlineKeyboardButton(TEXTS[lang]["admin_categories"], callback_data="admin_categories")],
        [InlineKeyboardButton(TEXTS[lang]["admin_broadcast"], callback_data="admin_broadcast")],
    ]
    
    if is_video_admin:
        keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="video_menu")])
    else:
        keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="main_menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_admin_stats(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    stats = db.get_user_stats()
    total_ref = db.get_all_referrals_count()
    text = (
        f"{TEXTS[lang]['admin_stats']}\n\n"
        f"{TEXTS[lang]['stats_total_users'].format(stats['total_users'])}\n"
        f"{TEXTS[lang]['stats_active_users'].format(stats['active_users'])}\n"
        f"{TEXTS[lang]['stats_total_views'].format(stats['total_views'])}\n"
        f"{TEXTS[lang]['stats_total_coins'].format(stats['total_coins'])}\n"
        f"{TEXTS[lang]['stats_premium_users'].format(stats['premium_users'])}\n"
        f"{TEXTS[lang]['stats_total_referrals'].format(total_ref)}"
    )
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def show_admin_categories(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    text = TEXTS[lang]["admin_categories"]
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["admin_add_category"], callback_data="admin_add_category")],
        [InlineKeyboardButton(TEXTS[lang]["admin_delete_category"], callback_data="admin_delete_category")],
        [InlineKeyboardButton(TEXTS[lang]["admin_upload_video"], callback_data="admin_upload_video")],
        [InlineKeyboardButton(TEXTS[lang]["admin_bulk_upload"], callback_data="admin_bulk_upload")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def start_add_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    user_states[user_id] = AdminState.WAITING_CATEGORY_NAME_RU
    text = TEXTS[lang]["enter_category_name_ru"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def start_delete_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    categories = db.get_categories()
    if not categories:
        text = "❌ Нет категорий для удаления"
        keyboard = [[InlineButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    else:
        text = TEXTS[lang]["select_category_to_delete"]
        keyboard = []
        for cat in categories:
            btn_text = f"{cat['name_ru']} / {cat['name_en']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"delete_category_{cat['id']}")])
        keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def delete_category(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, category_id: int
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    db.delete_category(category_id)
    text = TEXTS[lang]["category_deleted"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def start_upload_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    categories = db.get_categories()
    if not categories:
        text = "❌ Сначала создайте категорию"
        keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    else:
        text = TEXTS[lang]["select_category_for_video"]
        keyboard = []
        for cat in categories:
            btn_text = f"{cat['name_ru']} / {cat['name_en']}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"select_category_{cat['id']}")])
        keyboard.append([InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def select_category_for_action(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, category_id: int
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    context.user_data["selected_category_id"] = category_id
    text = TEXTS[lang]["send_video_file"]
    user_states[user_id] = AdminState.WAITING_VIDEO_FILE
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def start_bulk_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    user_states[user_id] = AdminState.WAITING_BULK_VIDEO_FILES
    context.user_data["bulk_upload"] = {"videos": [], "category_id": None}
    text = TEXTS[lang]["send_videos_bulk"]
    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["finish_upload"], callback_data="finish_bulk_upload")],
        [InlineKeyboardButton(TEXTS[lang]["cancel"], callback_data="cancel_bulk_upload")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def finish_bulk_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    data = context.user_data.get("bulk_upload")
    if not data or not data.get("videos"):
        user_states.pop(user_id, None)
        context.user_data.pop("bulk_upload", None)
        await update.callback_query.edit_message_text(
            TEXTS[lang]["bulk_upload_cancelled"],
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]),
        )
        return

    user_states.pop(user_id, None)
    videos = data["videos"]
    context.user_data.pop("bulk_upload", None)

    text = TEXTS[lang]["videos_uploaded"].format(len(videos))
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def cancel_bulk_upload(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    user_states.pop(user_id, None)
    context.user_data.pop("bulk_upload", None)
    text = TEXTS[lang]["bulk_upload_cancelled"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def save_pending_video(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, category_id: int
) -> None:
    if user_id not in ADMIN_IDS:
        return

    query = update.callback_query
    pending = context.user_data.get("pending_video")
    if not pending:
        await query.answer("❌ Нет видео для сохранения. Отправьте его ещё раз.", show_alert=True)
        return

    db.add_video(category_id, pending["file_id"], pending["file_unique_id"], pending["file_name"])
    context.user_data.pop("pending_video", None)
    text = TEXTS[lang]["video_uploaded"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


async def start_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    user_states[user_id] = AdminState.WAITING_BROADCAST_MESSAGE
    text = TEXTS[lang]["broadcast_instructions"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def cancel_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    user_states.pop(user_id, None)
    text = TEXTS[lang]["broadcast_cancelled"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def stop_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str
) -> None:
    if user_id not in ADMIN_IDS:
        await show_main_menu(update, context, user_id, lang)
        return

    global broadcast_status
    broadcast_status["active"] = False
    text = TEXTS[lang]["broadcast_cancelled"]
    keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)


async def execute_broadcast(
    context: ContextTypes.DEFAULT_TYPE, admin_id: int, lang: str, text: str
):
    global broadcast_status
    broadcast_status["active"] = True
    broadcast_status["sent_count"] = 0
    broadcast_status["failed_count"] = 0
    broadcast_status["failed_users"] = []

    users = db.get_all_users()
    broadcast_status["total_users"] = len(users)

    for uid in users:
        if not broadcast_status["active"]:
            break
        try:
            await context.bot.send_message(uid, text)
            broadcast_status["sent_count"] += 1
        except Exception as e:
            logging.error(f"Broadcast send error to {uid}: {e}")
            broadcast_status["failed_count"] += 1
            broadcast_status["failed_users"].append(uid)
        await asyncio.sleep(1)

    broadcast_status["active"] = False
    sent = broadcast_status["sent_count"]
    failed = broadcast_status["failed_count"]
    msg = TEXTS[lang]["broadcast_completed"].format(sent, failed)
    try:
        await context.bot.send_message(admin_id, msg)
    except Exception as e:
        logging.error(f"Broadcast result send error: {e}")


# Обработчики сообщений
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if user_id in ADMIN_IDS:
        # Админ загружает видео в основную админку
        user = db.get_user(user_id)
        lang = user["language"] if user else "ru"
        state = user_states.get(user_id)
        video = update.message.video

        if state == AdminState.WAITING_VIDEO_FILE:
            category_id = context.user_data.get("selected_category_id")
            if category_id:
                db.add_video(
                    category_id,
                    video.file_id,
                    video.file_unique_id,
                    video.file_name or "video.mp4",
                )
                user_states.pop(user_id, None)
                context.user_data.pop("selected_category_id", None)
                keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(TEXTS[lang]["video_uploaded"], reply_markup=reply_markup)
            return

        if state == AdminState.WAITING_BULK_VIDEO_FILES:
            data = context.user_data.get("bulk_upload", {"videos": [], "category_id": None})
            videos = data.get("videos", [])
            videos.append({
                "file_id": video.file_id,
                "file_unique_id": video.file_unique_id,
                "file_name": video.file_name or "video.mp4",
            })
            data["videos"] = videos
            context.user_data["bulk_upload"] = data
            text = TEXTS[lang]["bulk_upload_active"].format(len(videos))
            keyboard = [
                [InlineKeyboardButton(TEXTS[lang]["finish_upload"], callback_data="finish_bulk_upload")],
                [InlineKeyboardButton(TEXTS[lang]["cancel"], callback_data="cancel_bulk_upload")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(text, reply_markup=reply_markup)
            return

    # Обычный пользователь или админ в режиме загрузки для видео-бота
    if user_id in ADMIN_IDS:
        # Сохраняем видео в очередь для видео-бота
        if user_id not in pending_videos:
            pending_videos[user_id] = []
        
        pending_videos[user_id].append({
            "file_id": video.file_id,
            "file_unique_id": video.file_unique_id,
            "file_name": video.file_name or "video.mp4",
        })
        
        categories = db.get_categories()
        if categories:
            keyboard = []
            for cat in categories:
                btn_text = f"{cat['name_ru']} / {cat['name_en']}"
                keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"video_save_{cat['id']}")])
            
            await update.message.reply_text(
                f"📥 Видео загружено ({len(pending_videos[user_id])})\nВыберите категорию для сохранения:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await update.message.reply_text("❌ Сначала создайте категорию в админ-панели")
        return

    # Если не админ и не в режиме загрузки - игнорируем
    if user_id not in ADMIN_IDS:
        user = db.get_user(user_id)
        lang = user["language"] if user else "ru"
        await update.message.reply_text("❌ Вы не можете загружать видео. Это доступно только администраторам.")


async def handle_custom_coins_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, lang: str, text_in: str
):
    try:
        coins_amount = int(text_in)
        if coins_amount < MIN_CUSTOM_COINS or coins_amount > MAX_CUSTOM_COINS:
            raise ValueError
    except Exception:
        keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="choose_package")]]
        await update.message.reply_text(
            TEXTS[lang]["invalid_custom_coins"],
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    context.user_data["custom_coins_amount"] = coins_amount
    price_rub = payment_manager.calculate_custom_coins_price(coins_amount)
    price_text = payment_manager.format_price(price_rub, lang)
    text = TEXTS[lang]["custom_coins_summary"].format(coins_amount, price_text)

    keyboard = [
        [InlineKeyboardButton(TEXTS[lang]["crypto_payment"], callback_data="pay_crypto_custom")],
        [InlineKeyboardButton(TEXTS[lang]["card_payment"], callback_data="pay_card_custom")],
        [InlineKeyboardButton(TEXTS[lang]["back"], callback_data="custom_coins")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    user_states.pop(user_id, None)
    await update.message.reply_text(text, reply_markup=reply_markup)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    lang = user["language"] if user else "ru"
    message = update.message
    state = user_states.get(user_id)

    if state == UserState.WAITING_CUSTOM_COINS_AMOUNT:
        await handle_custom_coins_amount(update, context, user_id, lang, message.text)
        return

    if state == AdminState.WAITING_CATEGORY_NAME_RU:
        context.user_data["category_name_ru"] = message.text
        user_states[user_id] = AdminState.WAITING_CATEGORY_NAME_EN
        await message.reply_text(TEXTS[lang]["enter_category_name_en"])
        return

    if state == AdminState.WAITING_CATEGORY_NAME_EN:
        name_ru = context.user_data.get("category_name_ru")
        name_en = message.text
        db.add_category(name_ru, name_en)
        user_states.pop(user_id, None)
        context.user_data.pop("category_name_ru", None)
        keyboard = [[InlineKeyboardButton(TEXTS[lang]["back"], callback_data="admin_categories")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(TEXTS[lang]["category_added"], reply_markup=reply_markup)
        return

    if state == AdminState.WAITING_NAME_RU:
        context.user_data["cat_ru"] = message.text
        user_states[user_id] = AdminState.WAITING_NAME_EN
        await message.reply_text(TEXTS[lang]["enter_category_name_en"])
        return

    if state == AdminState.WAITING_NAME_EN:
        db.add_category(context.user_data["cat_ru"], message.text)
        context.user_data.pop("cat_ru", None)
        user_states.pop(user_id, None)
        await message.reply_text(TEXTS[lang]["category_added"])
        await show_video_menu(update, context, user_id, lang)
        return

    if state == AdminState.WAITING_BROADCAST_MESSAGE:
        text = message.text
        user_states.pop(user_id, None)
        global broadcast_status
        broadcast_status["broadcast_task"] = asyncio.create_task(
            execute_broadcast(context, user_id, lang, text)
        )
        await message.reply_text(TEXTS[lang]["broadcast_started"].format(len(db.get_all_users())))
        return

    # Если пользователь отправил текст, но мы не знаем, что делать - показываем меню
    await show_main_menu(update, context, user_id, lang)


def main() -> None:
    application = Application.builder().token(MAIN_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Объединенный бот запущен")
    application.run_polling()


if __name__ == "__main__":
    main()