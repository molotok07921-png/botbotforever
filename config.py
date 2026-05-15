# config.py

# === ОСНОВНОЙ БОТ (ФИНАНСЫ) ===
MAIN_BOT_TOKEN = "8565366731:AAHvZzapi6Q8I1x_z8Kxzseu1jnZgVLkg1s"  # Токен основного бота

# === ВИДЕО БОТ ===  
VIDEO_BOT_TOKEN = "8299985455:AAHv44S86aHDPD_zskmwqv99XwByd0RxwiU"  # Токен видео бота (получите у @BotFather)

# Настройки
VIDEO_COST = 5
ADMIN_IDS = [8075802187]  # Замените на ваш ID администратора
REFERRAL_BONUS = 30
PREMIUM_DAYS = 30
MIN_CUSTOM_COINS = 150
MAX_CUSTOM_COINS = 1000

# Настройки базы данных
DB_NAME = "bot_database.db"

# === НАСТРОЙКИ ПЛАТЕЖЕЙ ===

# CryptoBot (https://t.me/CryptoBot)
CRYPTOBOT_TOKEN = "475371:AAvqwqtTJstFL0xOKiaQpKI5XSYy0DC2aZA"  # Получите у @CryptoBot
CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"

# YooMoney настройки (ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ)
YOOMONEY_TOKEN = "4100116937965525.753A4F3883B2AE419D7410D0D4B2CC06C7EBEDA8FD54C998199F1D518040C4D9C748F3B665517A6D2AF34D9204E5C4331B7F9E38334E454822A47AF40C836370DBB4CDB1D8C7B212C97703C9909A6D3A4E9E6AEF2448A8F523A6582F7FA7284FE9065ED87A8FC05C10FE9BB599D044B044FDCD691684AD33ED4E8B55DF400D4B"  # Токен из шага 5
YOOMONEY_WALLET = "4100116937965525"  # Например: 4100118107652345
YOOMONEY_RECEIVER = "4100116937965525"  # Тот же номер кошелька

# 🏆 ОПТИМАЛЬНАЯ СТРУКТУРА ПАКЕТОВ ДЛЯ МАКСИМАЛЬНЫХ ПОКУПОК
COINS_PACKAGES_OPTIMAL = {
    'popular': {
        'coins': 150,
        'price_rub': 399,
        'bonus': 50,
        'value_per_coin': 1.00,
        'description': '🔥 САМЫЙ ВЫГОДНЫЙ ⭐',
        'popularity': 'high'
    },
    'mega': {
        'coins': 800,
        'price_rub': 1250,
        'bonus': 200,
        'value_per_coin': 0.50,
        'description': '💎 МЕГА пакет',
        'popularity': 'medium'
    },
    'premium': {
        'coins': 0,
        'price_rub': 449,
        'bonus': 0,
        'value_per_coin': 0.0,
        'description': '👑 Premium 30 дней',
        'popularity': 'medium',
        'days': 30
    }
}

# Стоимость произвольного количества coins
CUSTOM_COINS_PRICE_PER_COIN = 1  # 4 рубля за 1 coin

# Ссылки для платежей
WEBSITE_URL = "https://sites.google.com/view/expvid"
SUPPORT_URL = "https://t.me/plusexploit"

# Ссылка на видео бота (замените на реальную ссылку после создания бота)
VIDEO_BOT_LINK = "https://sites.google.com/view/expvid"  # Замените на реальную ссылку
