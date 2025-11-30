import sqlite3
import hashlib
from config import DATABASE_FILE

def get_db_connection():
    """Получить соединение с базой данных"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_database():
    """Создание базы данных и таблиц"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fio TEXT,
                password TEXT,
                email TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                departure_city TEXT,    
                arrival_city TEXT,       
                departure_date TEXT,
                arrival_date TEXT,    
                company TEXT,
                price INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS booking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,        
                flight_id INTEGER,     
                passenger_fio TEXT,     
                booking_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (flight_id) REFERENCES flights(id)
            )
        ''')
        
        # Проверяем и добавляем тестовых пользователей
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        
        if user_count == 0:
            add_sample_users(cursor)
            print("✓ Добавлены тестовые пользователи")

        # Проверяем и добавляем тестовые рейсы
        cursor.execute("SELECT COUNT(*) as count FROM flights")
        flight_count = cursor.fetchone()['count']

        if flight_count == 0:
            add_sample_flights(cursor)
            print("✓ Добавлены тестовые рейсы")
        
        conn.commit()
        conn.close()
        
        print("✓ База данных успешно инициализирована")
        return True
        
    except Exception as e:
        print(f"✗ Ошибка при создании базы данных: {e}")
        return False

def add_sample_users(cursor):
    """Добавление тестовых пользователей (без role)"""
    users = [
        ('Админ Админов', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin@mail.ru'),
        ('Иван Иванов', hashlib.sha256('password123'.encode()).hexdigest(), 'ivan@mail.ru'),
        ('Мария Петрова', hashlib.sha256('password123'.encode()).hexdigest(), 'maria@mail.ru'),
        ('Петр Сидоров', hashlib.sha256('password123'.encode()).hexdigest(), 'petr@mail.ru')
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO users (fio, password, email) VALUES (?, ?, ?)',
        users
    )

def add_sample_flights(cursor):
    """Добавление тестовых рейсов"""
    flights = [
        ('Москва', 'Санкт-Петербург', '2026-12-20', '2026-12-20', 'Аэрофлот', 5000),
        ('Москва', 'Сочи', '2026-12-21', '2026-12-21', 'S7 Airlines', 7000),
        ('Санкт-Петербург', 'Москва', '2026-12-22', '2026-12-22', 'Победа', 4500)
    ]
    
    cursor.executemany(
        'INSERT OR IGNORE INTO flights (departure_city, arrival_city, departure_date, arrival_date, company, price) VALUES (?, ?, ?, ?, ?, ?)',
        flights
    )

if __name__ == "__main__":
    create_database()