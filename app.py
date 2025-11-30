from flask import Flask, render_template, redirect, url_for, session
import logging
import config
from validate import *
from createdb import create_database, get_db_connection
from controllers import *

logging.basicConfig(
    level=config.LOG_LEVEL, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

create_database()

# Автоматически логиним админа для упрощения
@app.before_request
def auto_login():
    if 'user_id' not in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, fio FROM users WHERE email = 'admin@mail.ru'")
        admin = cursor.fetchone()
        conn.close()
        if admin:
            session['user_id'] = admin['id']
            session['fio'] = admin['fio']

@app.route('/')
def index():
    """Главная страница"""
    conn = get_db_connection()
    
    # Получаем счетчики для админ-панели
    flights_count = conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    bookings_count = conn.execute("SELECT COUNT(*) FROM booking").fetchone()[0]
    
    conn.close()
    
    return render_template('admin_panel.html',
                         flights_count=flights_count,
                         users_count=users_count,
                         bookings_count=bookings_count)


# Рейсы
@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight_page():
    from controllers import controller_add_flight
    return controller_add_flight()

@app.route('/edit_flights', methods=['GET'])
def edit_flights_page():
    from controllers import controller_edit_flights
    return controller_edit_flights()

@app.route('/edit_flights/process', methods=['POST'])
def edit_flights_process():
    from controllers import controller_process_edit_flights
    return controller_process_edit_flights()

@app.route('/delete_flight', methods=['GET'])
def delete_flights_page():
    from controllers import controller_delete_flights
    return controller_delete_flights()

@app.route('/delete_flight/process', methods=['POST'])
def delete_flights_process():
    from controllers import controller_process_delete_flights
    return controller_process_delete_flights()

# Пользователи
@app.route('/add_user', methods=['GET', 'POST'])
def add_user_page():
    from controllers import controller_add_user
    return controller_add_user()

@app.route('/edit_users', methods=['GET']) 
def edit_users_page():
    from controllers import controller_edit_users
    return controller_edit_users()

@app.route('/edit_users/process', methods=['POST'])
def edit_users_process():
    from controllers import controller_process_edit_users
    return controller_process_edit_users()

@app.route('/delete_user', methods=['GET'])
def delete_users_page():
    from controllers import controller_delete_users
    return controller_delete_users()

@app.route('/delete_user/process', methods=['POST'])
def delete_users_process():
    from controllers import controller_process_delete_users
    return controller_process_delete_users()

# Бронирования
@app.route('/view_bookings')
def view_bookings_page():
    from controllers import controller_view_bookings
    return controller_view_bookings()

@app.route('/add_booking', methods=['GET', 'POST'])
def add_booking_page():
    from controllers import controller_add_booking
    return controller_add_booking()

@app.route('/edit_bookings', methods=['GET'])
def edit_bookings_page():
    from controllers import controller_edit_bookings
    return controller_edit_bookings()

@app.route('/edit_bookings/process', methods=['POST'])
def edit_bookings_process():
    from controllers import controller_process_edit_bookings
    return controller_process_edit_bookings()

@app.route('/delete_booking', methods=['GET'])
def delete_bookings_page():
    from controllers import controller_delete_bookings
    return controller_delete_bookings()

@app.route('/delete_booking/process', methods=['POST'])
def delete_bookings_process():
    from controllers import controller_process_delete_bookings
    return controller_process_delete_bookings()

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return {'status': 'ok'}, 200
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


if __name__ == '__main__':
    logger.info(f"Запуск приложения на {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)