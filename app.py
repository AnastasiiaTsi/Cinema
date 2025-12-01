from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import re
import logging
import os
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    get_films_with_sessions, 
    get_film_by_id, 
    get_session_by_id, 
    get_available_seats, 
    create_booking,
    get_booking_by_code,
    cancel_booking,
    init_database,
    get_unique_sessions_for_film,
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_profile,
    get_user_bookings,
    add_notification,
    get_user_notifications,
    mark_notification_read
)

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'cinema-secret-key-2024')
app.config['DEBUG'] = os.environ.get('DEBUG', False)

# Ініціалізація бази даних при запуску
init_database()

def validate_email(email):
    """Валідація email формату"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name(name):
    """Валідація імені"""
    if not name or len(name.strip()) < 2:
        return False
    return True

@app.route('/')
def index():
    """Головна сторінка з афішею"""
    films = get_films_with_sessions()
    return render_template('index.html', films=films)

@app.route('/film/<int:film_id>')
def film_details(film_id):
    """Сторінка деталей фільму"""
    film = get_film_by_id(film_id)
    if not film:
        return render_template('404.html'), 404
    
    # Використовуємо функцію для унікальних сеансів
    film['sessions'] = get_unique_sessions_for_film(film_id)
    
    return render_template('film.html', film=film)

@app.route('/booking/<int:session_id>')
def booking_seats(session_id):
    """Сторінка вибору місць"""
    session = get_session_by_id(session_id)
    if not session:
        return render_template('404.html'), 404
    
    seats = get_available_seats(session_id)
    return render_template('booking.html', session=session, seats=seats)

@app.route('/booking/<booking_code>')
def booking_details(booking_code):
    """Сторінка перегляду деталей бронювання"""
    booking = get_booking_by_code(booking_code)
    if not booking:
        return render_template('404.html'), 404
    return render_template('booking_details.html', booking=booking)

@app.route('/api/book', methods=['POST'])
def book_tickets():
    """API для бронювання квитків"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Некоректний формат даних'
            }), 400
        
        # Валідація обов'язкових полів
        required_fields = ['session_id', 'customer_email', 'customer_name', 'selected_seats']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Відсутнє обов\'язкове поле: {field}'
                }), 400
        
        # Валідація email
        if not validate_email(data['customer_email']):
            return jsonify({
                'success': False,
                'message': 'Некоректний формат email'
            }), 400
        
        # Валідація імені
        if not validate_name(data['customer_name']):
            return jsonify({
                'success': False,
                'message': 'Ім\'я повинно містити принаймні 2 символи'
            }), 400
        
        # Перевірка кількості місць
        if not data['selected_seats']:
            return jsonify({
                'success': False,
                'message': 'Оберіть хоча б одне місце'
            }), 400
        
        max_seats = 10  # Максимальна кількість місць за бронювання
        if len(data['selected_seats']) > max_seats:
            return jsonify({
                'success': False,
                'message': f'Максимум {max_seats} місць за бронювання'
            }), 400
        
        # Перетворення ID місць в числа
        try:
            selected_seats = [int(seat_id) for seat_id in data['selected_seats']]
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Некоректний формат ID місць'
            }), 400
        
        # Створення бронювання
        booking_code = create_booking(
            data['session_id'], 
            data['customer_email'], 
            data['customer_name'], 
            selected_seats
        )
        
        logger.info(f"Створено бронювання {booking_code} для {data['customer_email']}")
        
        return jsonify({
            'success': True,
            'booking_code': booking_code,
            'message': 'Бронювання успішне!'
        })
        
    except Exception as e:
        logger.error(f"Помилка бронювання: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Помилка бронювання: {str(e)}'
        }), 400

@app.route('/api/cancel-booking/<booking_code>', methods=['POST'])
def api_cancel_booking(booking_code):
    """API для скасування бронювання"""
    try:
        success = cancel_booking(booking_code)
        if success:
            logger.info(f"Скасовано бронювання {booking_code}")
            return jsonify({
                'success': True,
                'message': 'Бронювання успішно скасовано'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Бронювання не знайдено або вже скасовано'
            }), 404
            
    except Exception as e:
        logger.error(f"Помилка скасування бронювання {booking_code}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Помилка скасування: {str(e)}'
        }), 400

@app.route('/api/films')
def api_films():
    """API для отримання фільмів"""
    try:
        films = get_films_with_sessions()
        return jsonify(films)
    except Exception as e:
        logger.error(f"Помилка отримання фільмів: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Помилка отримання даних фільмів'
        }), 500

@app.route('/api/sessions/<int:session_id>/seats')
def api_session_seats(session_id):
    """API для отримання місць сеансу"""
    try:
        seats = get_available_seats(session_id)
        return jsonify(seats)
    except Exception as e:
        logger.error(f"Помилка отримання місць для сеансу {session_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Помилка отримання даних місць'
        }), 500

# === КОРИСТУВАЧСЬКИЙ КАБІНЕТ ===

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Реєстрація користувача"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        # Валідація
        if not validate_email(email):
            return render_template('register.html', error='Некоректний email')
        
        if not username or len(username) < 3:
            return render_template('register.html', error='Ім\'я користувача повинно містити мінімум 3 символи')
        
        if not password or len(password) < 6:
            return render_template('register.html', error='Пароль повинен містити мінімум 6 символів')
        
        try:
            password_hash = generate_password_hash(password)
            user_id = create_user(email, username, password_hash, full_name, phone)
            
            # Автоматичний вхід після реєстрації
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            # Додати привітальне сповіщення
            add_notification(user_id, 'system', 'Ласкаво просимо!', 'Дякуємо за реєстрацію в нашому кінотеатрі!')
            
            return redirect(url_for('profile'))
        except Exception as e:
            return render_template('register.html', error=str(e))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вхід користувача"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            
            if remember:
                session.permanent = True
            else:
                session.permanent = False
            
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error='Невірний email або пароль')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Вихід користувача"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    """Профіль користувача"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    bookings = get_user_bookings(user['id'])
    notifications = get_user_notifications(user['id'], unread_only=True)
    
    return render_template('profile.html', 
                         user=user, 
                         bookings=bookings,
                         notifications=notifications)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    """Оновити профіль"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Необхідно увійти в систему'}), 401
    
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    
    success = update_user_profile(session['user_id'], full_name, phone)
    
    if success:
        return jsonify({'success': True, 'message': 'Профіль оновлено'})
    else:
        return jsonify({'success': False, 'message': 'Помилка оновлення профілю'})

@app.route('/api/notifications')
def api_get_notifications():
    """API для отримання сповіщень"""
    if 'user_id' not in session:
        return jsonify([])
    
    notifications = get_user_notifications(session['user_id'])
    return jsonify(notifications)

@app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
def api_mark_notification_as_read(notification_id):
    """API для позначення сповіщення як прочитаного"""
    if 'user_id' not in session:
        return jsonify({'success': False}), 401
    
    success = mark_notification_read(notification_id)
    return jsonify({'success': success})

# Додати middleware для перевірки авторизації
@app.before_request
def check_auth():
    # Список публічних маршрутів
    public_routes = ['index', 'film_details', 'booking_seats', 
                    'booking_details', 'login', 'register', 'static',
                    'api_films', 'api_session_seats', 'book_tickets',
                    'api_cancel_booking', 'api_get_notifications', 
                    'api_mark_notification_as_read']
    
    if request.endpoint not in public_routes and 'user_id' not in session:
        return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=5000)