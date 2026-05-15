# database.py
import sqlite3
import datetime

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE,
                language TEXT DEFAULT 'ru',
                coins INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE,
                premium_until TEXT,
                created_at TEXT,
                last_active TEXT
            )
        ''')
        
        # Таблица категорий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_ru TEXT,
                name_en TEXT,
                created_at TEXT
            )
        ''')
        
        # Таблица видео
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                file_id TEXT,
                file_unique_id TEXT UNIQUE,
                file_name TEXT,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')
        
        # Таблица просмотров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                video_id INTEGER,
                watched_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (video_id) REFERENCES videos (id)
            )
        ''')
        
        # Таблица рефералов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER UNIQUE,
                bonus_given BOOLEAN DEFAULT FALSE,
                created_at TEXT,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def add_user(self, user_id, language='ru'):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, language, coins, created_at, last_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, language, 30, now, now))
        
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'user_id': user[1],
                'language': user[2],
                'coins': user[3],
                'is_premium': bool(user[4]),
                'premium_until': user[5],
                'created_at': user[6],
                'last_active': user[7]
            }
        return None

    def update_user(self, user_id, user_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET language = ?, coins = ?, is_premium = ?, premium_until = ?, last_active = ?
            WHERE user_id = ?
        ''', (user_data['language'], user_data['coins'], user_data['is_premium'], 
              user_data['premium_until'], datetime.datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()

    def add_coins(self, user_id, coins):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (coins, user_id))
        cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
        new_balance = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        return new_balance

    def deduct_coins(self, user_id, coins):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET coins = coins - ? WHERE user_id = ?', (coins, user_id))
        
        conn.commit()
        conn.close()

    def activate_premium(self, user_id, days):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        premium_until = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
        
        cursor.execute('''
            UPDATE users 
            SET is_premium = TRUE, premium_until = ?
            WHERE user_id = ?
        ''', (premium_until, user_id))
        
        conn.commit()
        conn.close()
        return premium_until

    def check_premium_status(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT is_premium, premium_until FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result and result[0]:  # is_premium is True
            premium_until = datetime.datetime.fromisoformat(result[1])
            if premium_until < datetime.datetime.now():
                # Premium expired
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = FALSE, premium_until = NULL
                    WHERE user_id = ?
                ''', (user_id,))
                conn.commit()
                conn.close()
                return False
            conn.close()
            return True
        conn.close()
        return False

    def add_category(self, name_ru, name_en):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO categories (name_ru, name_en, created_at)
            VALUES (?, ?, ?)
        ''', (name_ru, name_en, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_categories(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categories ORDER BY id')
        categories = cursor.fetchall()
        
        conn.close()
        
        result = []
        for category in categories:
            result.append({
                'id': category[0],
                'name_ru': category[1],
                'name_en': category[2],
                'created_at': category[3]
            })
        return result

    def get_category(self, category_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM categories WHERE id = ?', (category_id,))
        category = cursor.fetchone()
        
        conn.close()
        
        if category:
            return {
                'id': category[0],
                'name_ru': category[1],
                'name_en': category[2],
                'created_at': category[3]
            }
        return None

    def delete_category(self, category_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        
        conn.commit()
        conn.close()

    def add_video(self, category_id, file_id, file_unique_id, file_name):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO videos (category_id, file_id, file_unique_id, file_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (category_id, file_id, file_unique_id, file_name, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_videos_by_category(self, category_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM videos WHERE category_id = ? ORDER BY id', (category_id,))
        videos = cursor.fetchall()
        
        conn.close()
        
        result = []
        for video in videos:
            result.append({
                'id': video[0],
                'category_id': video[1],
                'file_id': video[2],
                'file_unique_id': video[3],
                'file_name': video[4],
                'created_at': video[5]
            })
        return result

    def get_random_video_from_category(self, category_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM videos WHERE category_id = ? ORDER BY RANDOM() LIMIT 1', (category_id,))
        video = cursor.fetchone()
        
        conn.close()
        
        if video:
            return {
                'id': video[0],
                'category_id': video[1],
                'file_id': video[2],
                'file_unique_id': video[3],
                'file_name': video[4],
                'created_at': video[5]
            }
        return None

    def get_video_count_by_category(self, category_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM videos WHERE category_id = ?', (category_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

    def add_video_view(self, user_id, video_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO video_views (user_id, video_id, watched_at)
            VALUES (?, ?, ?)
        ''', (user_id, video_id, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_user_videos_watched(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM video_views WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

    def add_referral(self, referrer_id, referred_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referrals (referrer_id, referred_id, created_at)
            VALUES (?, ?, ?)
        ''', (referrer_id, referred_id, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()

    def get_referral_stats(self, user_id):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Количество рефералов
        cursor.execute('SELECT COUNT(*) FROM referrals WHERE referrer_id = ?', (user_id,))
        referrals_count = cursor.fetchone()[0]
        
        # Всего заработано
        from config import REFERRAL_BONUS
        total_earned = referrals_count * REFERRAL_BONUS
        
        conn.close()
        
        return {
            'referrals_count': referrals_count,
            'total_earned': total_earned
        }

    def get_all_referrals_count(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM referrals')
        total_referrals = cursor.fetchone()[0]
        
        conn.close()
        return total_referrals

    def get_user_stats(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Всего пользователей
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Активные пользователи (за последние 7 дней)
        week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM users WHERE last_active > ?', (week_ago,))
        active_users = cursor.fetchone()[0]
        
        # Всего просмотров
        cursor.execute('SELECT COUNT(*) FROM video_views')
        total_views = cursor.fetchone()[0]
        
        # Всего coins
        cursor.execute('SELECT SUM(coins) FROM users')
        total_coins = cursor.fetchone()[0] or 0
        
        # Премиум пользователи
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_premium = TRUE')
        premium_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_views': total_views,
            'total_coins': total_coins,
            'premium_users': premium_users
        }

    def get_all_users(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return users