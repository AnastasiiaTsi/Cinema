import sqlite3
import os
import random
import string
from config import Config
import logging
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

def get_db_connection():
    """Підключення до SQLite бази даних"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Щоб результати були як словники
    return conn

def init_database():
    """Ініціалізація бази даних з усіма таблицями"""
    conn = get_db_connection()
    
    try:
        # Створюємо таблиці
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                duration INTEGER NOT NULL,
                genre TEXT,
                poster_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS halls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                seats_count INTEGER NOT NULL,
                hall_type TEXT DEFAULT '2D'
            );

            CREATE TABLE IF NOT EXISTS seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hall_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                seat_number INTEGER NOT NULL,
                FOREIGN KEY (hall_id) REFERENCES halls (id)
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                film_id INTEGER NOT NULL,
                hall_id INTEGER NOT NULL,
                session_date TEXT NOT NULL,
                session_time TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (film_id) REFERENCES films (id),
                FOREIGN KEY (hall_id) REFERENCES halls (id)
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                customer_email TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                booking_code TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );

            CREATE TABLE IF NOT EXISTS booked_seats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                seat_id INTEGER NOT NULL,
                FOREIGN KEY (booking_id) REFERENCES bookings (id),
                FOREIGN KEY (seat_id) REFERENCES seats (id),
                UNIQUE(booking_id, seat_id)
            );
           
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                avatar_url TEXT DEFAULT '/static/img/default-avatar.png',
                email_verified BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_last_four TEXT,
                card_brand TEXT,
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'booking', 'system', 'promo'
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        ''')
        
        # Додаємо тестові дані
        conn.executescript('''
            INSERT OR IGNORE INTO films (id, title, description, duration, genre, poster_url) VALUES
            (1, 'Дюна: Частина друга', 'Пол Атрідіс об''єднується з Чані та фременами на шляху помсти тим, хто знищив його родину. Зіткнувшись з вибором між коханням та долею всесвіту, він намагається запобігти страшному майбутньому.', 166, 'Фантастика', '/static/img/dune2.jpg'),
            (2, 'Оппенгеймер', 'Історія фізика-теоретика Джуліуса Роберта Оппенгеймера, творця атомної бомби, та його моральних страждань після створення зброї масового ураження.', 180, 'Драма', '/static/img/oppenheimer.jpg'),
            (3, 'Місія нездійсненна 7', 'Ітан Хант та його команда намагаються зупинити штучний інтелект, що загрожує людству у новому трилері з неймовірними трюками.', 163, 'Екшн', '/static/img/mission_impossible.jpg'),
            (4, 'Трансформери: Епоха звірів', 'Оптимус Прайм та Автоботи об''єднуються з звірними трансформерами, щоб протистояти новій космічній загрозі.', 127, 'Фантастика', '/static/img/transformers.jpg'),
            (5, 'Людина-павук: Крізь всесвіти', 'Майлз Моралес подорожує мультивсесвітом, де зустрічає команду Людей-павуків, які мають зупинити нову загрозу.', 140, 'Мультфільм', '/static/img/spiderman.jpg'),
            (6, 'Джон Уік 4', 'Джон Уік бореться з Таємною організацією кілерів, щоб здобути свободу у наймасштабнішій та найнебезпечнішій частині франшизи.', 169, 'Екшн', '/static/img/johnwick4.jpg'),
            (7, 'Годзіла та Конг: Нова імперія', 'Годзіла та Конг об''єднують сили проти спільного ворога, який загрожує їхньому існуванню та існуванню людства.', 115, 'Фантастика', '/static/img/godzilla_kong.jpg'),
            (8, 'Форсаж 10', 'Доміник Торетто та його родина зіткнуться з найнебезпечнішим ворогом, який використовує минуле Дома проти нього.', 141, 'Екшн', '/static/img/fast10.jpg'),
            (9, 'Вартові галактики 3', 'Команда Пітера Квілла рятує Всесвіт та розкриває таємниці Рокета у останній частині епічної космічної саги.', 150, 'Фантастика', '/static/img/gotg3.jpg'),
            (10, 'Індиана Джонс і Реліквія долі', 'Індиана Джонс вирушає у чергову пригоду за артефактом, що змінює долю у заключній частині легендарної серії.', 154, 'Пригоди', '/static/img/indiana_jones.jpg');
            -- Зали
            INSERT OR IGNORE INTO halls (id, name, seats_count, hall_type) VALUES
            (1, 'Зал 1 (2D)', 100, '2D'),
            (2, 'Зал 2 (3D)', 80, '3D'),
            (3, 'Зал 3 (IMAX)', 120, 'IMAX'),
            (4, 'Зал 4 (VIP)', 50, 'VIP');
        ''')
        
        # Створюємо правильну схему місць
        create_proper_seats_schema(conn)
        
        # Додаємо унікальні сеанси (без дублікатів)
        conn.executescript('''
            -- Сеанси (тільки унікальні комбінації дата-час-зал)
            INSERT OR IGNORE INTO sessions (film_id, hall_id, session_date, session_time, price) VALUES
            (1, 1, date('now'), '10:00:00', 120.00),
            (1, 2, date('now'), '13:30:00', 150.00),
            (2, 3, date('now'), '11:00:00', 180.00),
            (3, 1, date('now'), '14:00:00', 130.00),
            (4, 2, date('now'), '16:30:00', 140.00),
            (5, 4, date('now'), '19:00:00', 200.00),
            (6, 1, date('now'), '21:00:00', 160.00),
            (1, 3, date('now', '+1 day'), '12:00:00', 190.00),
            (2, 1, date('now', '+1 day'), '15:00:00', 120.00),
            (3, 2, date('now', '+1 day'), '17:30:00', 150.00),
            (7, 3, date('now', '+1 day'), '20:00:00', 180.00),
            (8, 4, date('now', '+1 day'), '22:00:00', 170.00),
            (4, 1, date('now', '+2 day'), '11:30:00', 120.00),
            (5, 2, date('now', '+2 day'), '14:00:00', 140.00),
            (9, 3, date('now', '+2 day'), '16:30:00', 180.00),
            (10, 1, date('now', '+2 day'), '19:00:00', 130.00),
            (1, 4, date('now', '+2 day'), '21:30:00', 220.00);

            -- Тестові бронювання
            INSERT OR IGNORE INTO bookings (session_id, customer_email, customer_name, booking_code, status) VALUES
            (1, 'anna.petrova@gmail.com', 'Анна Петрова', 'CINEMA001', 'active'),
            (3, 'oleg.shevchenko@ukr.net', 'Олег Шевченко', 'CINEMA002', 'active'),
            (5, 'maria.ivanova@gmail.com', 'Марія Іванова', 'CINEMA003', 'completed');

            -- Заброньовані місця
            INSERT OR IGNORE INTO booked_seats (booking_id, seat_id) VALUES
            (1, 5), (1, 6), (2, 25), (3, 45);
        ''')
        
        # Перевіряємо, чи є вже користувачі
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Додаємо адміністратора
            cursor.execute("""
            INSERT INTO users (email, username, password_hash, full_name, phone, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'admin@cinema.com',
                'admin',
                generate_password_hash('admin123'),
                'Адміністратор Системи',
                '+380001112233',
                True
            ))
            
            # Додаємо звичайного користувача
            cursor.execute("""
            INSERT INTO users (email, username, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
            """, (
                'user@test.com',
                'user',
                generate_password_hash('user123'),
                'Тестовий Користувач',
                '+380991112233'
            ))
            
            # Додаємо ще одного користувача
            cursor.execute("""
            INSERT INTO users (email, username, password_hash, full_name, phone)
            VALUES (?, ?, ?, ?, ?)
            """, (
                'anna.petrova@gmail.com',
                'anna',
                generate_password_hash('anna123'),
                'Анна Петрова',
                '+380501112233'
            ))
            
            # Додаємо тестові сповіщення
            cursor.execute("""
            INSERT INTO notifications (user_id, type, title, message, is_read)
            VALUES 
            (1, 'system', 'Ласкаво просимо!', 'Дякуємо за використання нашого кінотеатру.', FALSE),
            (2, 'promo', 'Спеціальна пропозиція', 'Цього тижня - знижка 20% на всі сеанси після 18:00.', FALSE),
            (3, 'booking', 'Бронювання підтверджено', 'Ваше бронювання CINEMA001 успішно створено.', TRUE)
            """)
            
            print("Тестові користувачі додані!")
        
        conn.commit()
        logger.info("SQLite база даних створена та заповнена!")
        
    except Exception as e:
        logger.error(f"Помилка ініціалізації бази даних: {str(e)}")
        raise e
    finally:
        conn.close()

def create_proper_seats_schema(conn):
    """Створити правильну схему місць з нумерацією 1,2,3,4..."""
    try:
        # Видалити старі місця
        conn.execute("DELETE FROM seats")
        
        # Конфігурація залів: (id залу, кількість місць, місць у ряду)
        halls_config = [
            (1, 100, 10),   # Зал 1: 100 місць, 10 у ряду
            (2, 80, 8),     # Зал 2: 80 місць, 8 у ряду
            (3, 120, 12),   # Зал 3: 120 місць, 12 у ряду
            (4, 50, 5)      # Зал 4: 50 місць, 5 у ряду
        ]
        
        for hall_id, total_seats, seats_per_row in halls_config:
            rows = (total_seats + seats_per_row - 1) // seats_per_row  # Округлення вгору
            
            for row in range(1, rows + 1):
                seats_in_this_row = min(seats_per_row, total_seats - (row - 1) * seats_per_row)
                
                for seat_num in range(1, seats_in_this_row + 1):
                    conn.execute(
                        "INSERT INTO seats (hall_id, row_number, seat_number) VALUES (?, ?, ?)",
                        (hall_id, row, seat_num)
                    )
        
        logger.info("✅ Правильна схема місць створена!")
        
    except Exception as e:
        logger.error(f"Помилка створення схеми місць: {str(e)}")
        raise e

def ensure_database():
    """Перевіряє чи база даних існує, якщо ні - створює"""
    if not os.path.exists(Config.DATABASE_PATH):
        init_database()

def generate_unique_booking_code(conn, max_attempts=10):
    """Генерує унікальний код бронювання"""
    for _ in range(max_attempts):
        code = 'CINEMA' + ''.join(random.choices(string.digits, k=6))
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM bookings WHERE booking_code = ?", (code,))
        if not cursor.fetchone():
            return code
    raise Exception("Не вдалося згенерувати унікальний код бронювання")

# Функції для роботи з даними
def get_films_with_sessions():
    """Отримати фільми з найближчими сеансами"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT DISTINCT f.* 
        FROM films f 
        JOIN sessions s ON f.id = s.film_id 
        WHERE s.session_date >= date('now') 
        ORDER BY s.session_date 
        LIMIT 8
        """
        cursor.execute(sql)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Помилка отримання фільмів: {str(e)}")
        return []
    finally:
        conn.close()

def get_film_by_id(film_id):
    """Отримати деталі фільму по ID"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Отримуємо інформацію про фільм
        sql_film = "SELECT * FROM films WHERE id = ?"
        cursor.execute(sql_film, (film_id,))
        film = cursor.fetchone()
        
        if film:
            film = dict(film)
            # Отримуємо унікальні сеанси для цього фільму
            film['sessions'] = get_unique_sessions_for_film(film_id)
        
        return film
    except Exception as e:
        logger.error(f"Помилка отримання фільму {film_id}: {str(e)}")
        return None
    finally:
        conn.close()

def get_session_by_id(session_id):
    """Отримати деталі сеансу по ID"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT s.*, f.title as film_title, f.duration, f.genre as film_genre,
               h.name as hall_name, h.hall_type
        FROM sessions s
        JOIN films f ON s.film_id = f.id
        JOIN halls h ON s.hall_id = h.id
        WHERE s.id = ?
        """
        cursor.execute(sql, (session_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Помилка отримання сеансу {session_id}: {str(e)}")
        return None
    finally:
        conn.close()

def get_available_seats(session_id):
    """Отримати вільні місця для сеансу"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Отримуємо всі місця залу для цього сеансу
        sql_seats = """
        SELECT st.* 
        FROM seats st
        JOIN sessions s ON st.hall_id = s.hall_id
        WHERE s.id = ?
        ORDER BY st.row_number, st.seat_number
        """
        cursor.execute(sql_seats, (session_id,))
        all_seats = [dict(row) for row in cursor.fetchall()]
        
        # Отримуємо заброньовані місця для цього сеансу
        sql_booked = """
        SELECT bs.seat_id 
        FROM booked_seats bs
        JOIN bookings b ON bs.booking_id = b.id
        WHERE b.session_id = ? AND b.status = 'active'
        """
        cursor.execute(sql_booked, (session_id,))
        booked_seats = [row['seat_id'] for row in cursor.fetchall()]
        
        # Позначаємо місця як вільні/зайняті
        for seat in all_seats:
            seat['is_available'] = seat['id'] not in booked_seats
        
        return all_seats
    except Exception as e:
        logger.error(f"Помилка отримання місць для сеансу {session_id}: {str(e)}")
        return []
    finally:
        conn.close()

def create_booking(session_id, customer_email, customer_name, selected_seats):
    """Створити бронювання"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Перевірити чи місця все ще вільні
        available_seats = get_available_seats(session_id)
        available_seat_ids = {seat['id'] for seat in available_seats if seat['is_available']}
        
        for seat_id in selected_seats:
            if seat_id not in available_seat_ids:
                raise Exception(f"Місце {seat_id} вже зайняте")
        
        # Генеруємо унікальний код бронювання
        booking_code = generate_unique_booking_code(conn)
        
        # Створюємо бронювання
        sql_booking = """
        INSERT INTO bookings (session_id, customer_email, customer_name, booking_code, status)
        VALUES (?, ?, ?, ?, 'active')
        """
        cursor.execute(sql_booking, (session_id, customer_email, customer_name, booking_code))
        booking_id = cursor.lastrowid
        
        # Додаємо заброньовані місця
        for seat_id in selected_seats:
            sql_seat = "INSERT INTO booked_seats (booking_id, seat_id) VALUES (?, ?)"
            cursor.execute(sql_seat, (booking_id, seat_id))
        
        conn.commit()
        return booking_code
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.error(f"Помилка цілісності бази даних: {str(e)}")
        raise Exception("Помилка бази даних при бронюванні")
    except Exception as e:
        conn.rollback()
        logger.error(f"Помилка створення бронювання: {str(e)}")
        raise e
    finally:
        conn.close()

def get_booking_by_code(booking_code):
    """Отримати інформацію про бронювання за кодом"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT b.*, s.session_date, s.session_time, f.title as film_title, s.film_id,
               h.name as hall_name, GROUP_CONCAT(st.row_number || '-' || st.seat_number) as seats
        FROM bookings b
        JOIN sessions s ON b.session_id = s.id
        JOIN films f ON s.film_id = f.id
        JOIN halls h ON s.hall_id = h.id
        JOIN booked_seats bs ON b.id = bs.booking_id
        JOIN seats st ON bs.seat_id = st.id
        WHERE b.booking_code = ?
        GROUP BY b.id
        """
        cursor.execute(sql, (booking_code,))
        result = cursor.fetchone()
        return dict(result) if result else None
    except Exception as e:
        logger.error(f"Помилка отримання бронювання {booking_code}: {str(e)}")
        return None
    finally:
        conn.close()

def cancel_booking(booking_code):
    """Скасувати бронювання"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_code = ?", (booking_code,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Помилка скасування бронювання {booking_code}: {str(e)}")
        return False
    finally:
        conn.close()

def get_bookings_by_email(email):
    """Отримати всі бронювання за email"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT b.*, f.title as film_title, s.session_date, s.session_time,
               h.name as hall_name, GROUP_CONCAT(st.row_number || '-' || st.seat_number) as seats
        FROM bookings b
        JOIN sessions s ON b.session_id = s.id
        JOIN films f ON s.film_id = f.id
        JOIN halls h ON s.hall_id = h.id
        JOIN booked_seats bs ON b.id = bs.booking_id
        JOIN seats st ON bs.seat_id = st.id
        WHERE b.customer_email = ?
        GROUP BY b.id
        ORDER BY b.created_at DESC
        """
        cursor.execute(sql, (email,))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Помилка отримання бронювань для {email}: {str(e)}")
        return []
    finally:
        conn.close()

def get_unique_sessions_for_film(film_id):
    """Отримати унікальні сеанси для фільму (без дублікатів)"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT DISTINCT 
            s.id,
            s.session_date,
            s.session_time,
            s.price,
            h.name as hall_name,
            h.hall_type
        FROM sessions s
        JOIN halls h ON s.hall_id = h.id
        WHERE s.film_id = ? AND s.session_date >= date('now')
        ORDER BY s.session_date, s.session_time
        """
        cursor.execute(sql, (film_id,))
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Помилка отримання унікальних сеансів для фільму {film_id}: {str(e)}")
        return []
    finally:
        conn.close()

def update_films_data():
    """Функція для оновлення фільмів (можна викликати окремо)"""
    conn = get_db_connection()
    try:
        # Очистити старі дані
        conn.executescript('''
            DELETE FROM booked_seats;
            DELETE FROM bookings;
            DELETE FROM sessions;
            DELETE FROM films;
        ''')
        
        # Додати нові фільми
        conn.executescript('''
            INSERT INTO films (id, title, description, duration, genre, poster_url) VALUES
            (1, 'Дюна: Частина друга', 'Пол Атрідіс об''єднується з Чані та фременами на шляху помсти тим, хто знищив його родину. Зіткнувшись з вибором між коханням та долею всесвіту, він намагається запобігти страшному майбутньому.', 166, 'Фантастика', '/static/images/posters/dune2.jpg'),
            (2, 'Оппенгеймер', 'Історія фізика-теоретика Джуліуса Роберта Оппенгеймера, творця атомної бомби, та його моральних страждань після створення зброї масового ураження.', 180, 'Драма', '/static/images/posters/oppenheimer.jpg'),
            (3, 'Місія нездійсненна 7', 'Ітан Хант та його команда намагаються зупинити штучний інтелект, що загрожує людству у новому трилері з неймовірними трюками.', 163, 'Екшн', '/static/images/posters/mission_impossible.jpg'),
            (4, 'Трансформери: Епоха звірів', 'Оптимус Прайм та Автоботи об''єднуються з звірними трансформерами, щоб протистояти новій космічній загрозі.', 127, 'Фантастика', '/static/images/posters/transformers.jpg'),
            (5, 'Людина-павук: Крізь всесвіти', 'Майлз Моралес подорожує мультивсесвітом, де зустрічає команду Людей-павуків, які мають зупинити нову загрозу.', 140, 'Мультфільм', '/static/images/posters/spiderman.jpg'),
            (6, 'Джон Уік 4', 'Джон Уік бореться з Таємною організацією кілерів, щоб здобути свободу у наймасштабнішій та найнебезпечнішій частині франшизи.', 169, 'Екшн', '/static/images/posters/johnwick4.jpg'),
            (7, 'Годзіла та Конг: Нова імперія', 'Годзіла та Конг об''єднують сили проти спільного ворога, який загрожує їхньому існуванню та існуванню людства.', 115, 'Фантастика', '/static/images/posters/godzilla_kong.jpg'),
            (8, 'Форсаж 10', 'Доміник Торетто та його родина зіткнуться з найнебезпечнішим ворогом, який використовує минуле Дома проти нього.', 141, 'Екшн', '/static/images/posters/fast10.jpg'),
            (9, 'Вартові галактики 3', 'Команда Пітера Квілла рятує Всесвіт та розкриває таємниці Рокета у останній частині епічної космічної саги.', 150, 'Фантастика', '/static/images/posters/gotg3.jpg'),
            (10, 'Індиана Джонс і Реліквія долі', 'Індиана Джонс вирушає у чергову пригоду за артефактом, що змінює долю у заключній частині легендарної серії.', 154, 'Пригоди', '/static/images/posters/indiana_jones.jpg');
        ''')
        
        # Додати унікальні сеанси
        conn.executescript('''
            INSERT INTO sessions (film_id, hall_id, session_date, session_time, price) VALUES
            (1, 1, date('now'), '10:00:00', 120.00),
            (1, 2, date('now'), '13:30:00', 150.00),
            (2, 3, date('now'), '11:00:00', 180.00),
            (3, 1, date('now'), '14:00:00', 130.00),
            (4, 2, date('now'), '16:30:00', 140.00),
            (5, 4, date('now'), '19:00:00', 200.00),
            (6, 1, date('now'), '21:00:00', 160.00),
            (1, 3, date('now', '+1 day'), '12:00:00', 190.00),
            (2, 1, date('now', '+1 day'), '15:00:00', 120.00),
            (3, 2, date('now', '+1 day'), '17:30:00', 150.00),
            (7, 3, date('now', '+1 day'), '20:00:00', 180.00),
            (8, 4, date('now', '+1 day'), '22:00:00', 170.00),
            (4, 1, date('now', '+2 day'), '11:30:00', 120.00),
            (5, 2, date('now', '+2 day'), '14:00:00', 140.00),
            (9, 3, date('now', '+2 day'), '16:30:00', 180.00),
            (10, 1, date('now', '+2 day'), '19:00:00', 130.00),
            (1, 4, date('now', '+2 day'), '21:30:00', 220.00);
        ''')
        
        # Оновити схему місць
        create_proper_seats_schema(conn)
        
        conn.commit()
        logger.info("✅ Фільми оновлені!")
    except Exception as e:
        logger.error(f"Помилка оновлення фільмів: {str(e)}")
        raise e
    finally:
        conn.close()

def recreate_database():
    """Перестворити базу даних з оновленими шляхами"""
    if os.path.exists(Config.DATABASE_PATH):
        os.remove(Config.DATABASE_PATH)
    init_database()
    print("✅ База даних перестворена з оновленими шляхами до афіш!")


# Додати ці функції в database.py

def create_user(email, username, password_hash, full_name=None, phone=None):
    """Створити нового користувача"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO users (email, username, password_hash, full_name, phone)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (email, username, password_hash, full_name, phone))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: users.email" in str(e):
            raise Exception("Користувач з таким email вже існує")
        elif "UNIQUE constraint failed: users.username" in str(e):
            raise Exception("Користувач з таким іменем вже існує")
        raise e
    finally:
        conn.close()

def get_user_by_email(email):
    """Отримати користувача за email"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM users WHERE email = ?"
        cursor.execute(sql, (email,))
        result = cursor.fetchone()
        return dict(result) if result else None
    finally:
        conn.close()

def get_user_by_id(user_id):
    """Отримати користувача за ID"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM users WHERE id = ?"
        cursor.execute(sql, (user_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    finally:
        conn.close()

def update_user_profile(user_id, full_name=None, phone=None):
    """Оновити профіль користувача"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        updates = []
        params = []
        
        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)
        if phone is not None:
            updates.append("phone = ?")
            params.append(phone)
        
        if not updates:
            return False
            
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def add_user_payment_method(user_id, card_last_four, card_brand, is_default=False):
    """Додати спосіб оплати"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Якщо це метод за замовчуванням, зніміть прапор з інших
        if is_default:
            cursor.execute("UPDATE user_payment_methods SET is_default = FALSE WHERE user_id = ?", (user_id,))
        
        sql = """
        INSERT INTO user_payment_methods (user_id, card_last_four, card_brand, is_default)
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql, (user_id, card_last_four, card_brand, is_default))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_user_payment_methods(user_id):
    """Отримати способи оплати користувача"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM user_payment_methods WHERE user_id = ? ORDER BY is_default DESC, created_at DESC"
        cursor.execute(sql, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_user_bookings(user_id):
    """Отримати всі бронювання користувача"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        SELECT b.*, f.title as film_title, s.session_date, s.session_time,
               h.name as hall_name, GROUP_CONCAT(st.row_number || '-' || st.seat_number) as seats
        FROM bookings b
        JOIN sessions s ON b.session_id = s.id
        JOIN films f ON s.film_id = f.id
        JOIN halls h ON s.hall_id = h.id
        JOIN booked_seats bs ON b.id = bs.booking_id
        JOIN seats st ON bs.seat_id = st.id
        WHERE b.customer_email = (
            SELECT email FROM users WHERE id = ?
        )
        GROUP BY b.id
        ORDER BY b.created_at DESC
        """
        cursor.execute(sql, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def add_notification(user_id, type, title, message):
    """Додати сповіщення"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = """
        INSERT INTO notifications (user_id, type, title, message)
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql, (user_id, type, title, message))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_user_notifications(user_id, unread_only=False):
    """Отримати сповіщення користувача"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        if unread_only:
            sql = "SELECT * FROM notifications WHERE user_id = ? AND is_read = FALSE ORDER BY created_at DESC"
            cursor.execute(sql, (user_id,))
        else:
            sql = "SELECT * FROM notifications WHERE user_id = ? ORDER BY is_read ASC, created_at DESC LIMIT 50"
            cursor.execute(sql, (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def mark_notification_read(notification_id):
    """Позначити сповіщення як прочитане"""
    ensure_database()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "UPDATE notifications SET is_read = TRUE WHERE id = ?"
        cursor.execute(sql, (notification_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

if __name__ == "__main__":
    recreate_database()