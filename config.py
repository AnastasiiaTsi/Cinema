import os

class Config:
    # SQLite налаштування
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'cinema.db')
    
    # Секретний ключ для Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cinema-secret-key-2024')
    
    # Налаштування безпеки
    DEBUG = os.environ.get('DEBUG', False)
    
    # Максимальна кількість місць за бронювання
    MAX_SEATS_PER_BOOKING = 10
    
    # Папка для статичних файлів
    STATIC_FOLDER = 'static'
    UPLOAD_FOLDER = os.path.join(STATIC_FOLDER, 'images', 'posters')