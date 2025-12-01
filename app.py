from flask import Flask, render_template, request, jsonify
import re
import logging
import os
from database import (
    get_films_with_sessions, 
    get_film_by_id, 
    get_session_by_id, 
    get_available_seats, 
    create_booking,
    get_booking_by_code,
    cancel_booking,
    init_database,
    get_unique_sessions_for_film 
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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], port=5000)