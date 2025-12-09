from flask import Flask, render_template, session
import logging
import os
import json
from validate import *
from createdb import create_database, get_db_connection
from controllers import *

def load_config():
    config_path = 'config.json'
    
    default_config = {
        "SECRET_KEY": "447174713812837124717",
        "DATABASE_FILE": "database.db",
        "HOST": "0.0.0.0",
        "PORT": 5000,
        "DEBUG": True,
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "logs/app.log",
        "LOG_ENCODING": "utf-8",
        "ITEMS_PER_PAGE": 10
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                for key, value in loaded_config.items():
                    if key in default_config:
                        default_config[key] = value
                print(f"✓ Конфигурация загружена из {config_path}")
        except Exception as e:
            print(f"✗ Ошибка загрузки конфигурации: {e}")
    else:
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"✓ Создан файл конфигурации {config_path}")
        except Exception as e:
            print(f"✗ Ошибка создания конфигурации: {e}")
    
    return default_config

config = load_config()

app = Flask(__name__)

app.secret_key = config['SECRET_KEY']
app.config['DATABASE_FILE'] = config['DATABASE_FILE']
app.config['HOST'] = config['HOST']
app.config['PORT'] = config['PORT']
app.config['DEBUG'] = config['DEBUG']

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=getattr(logging, config['LOG_LEVEL']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config['LOG_FILE'], encoding=config['LOG_ENCODING']),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    create_database()
    logger.info("Database initialized")
except Exception as e:
    logger.error(f"Database initialization error: {e}")

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
            logger.debug(f"Auto login for user {admin['fio']}")

@app.route('/')
def index():
    conn = get_db_connection()
    
    try:
        flights_count = conn.execute("SELECT COUNT(*) FROM flights").fetchone()[0]
        users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bookings_count = conn.execute("SELECT COUNT(*) FROM booking").fetchone()[0]
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT b.id, b.passenger_fio, f.departure_city, f.arrival_city, 
                   f.departure_date, b.booking_date
            FROM booking b
            JOIN flights f ON b.flight_id = f.id
            ORDER BY b.booking_date DESC
            LIMIT 5
        ''')
        recent_bookings = cursor.fetchall()
        
        conn.close()
        
        return render_template('admin_panel.html',
                             flights_count=flights_count,
                             users_count=users_count,
                             bookings_count=bookings_count,
                             recent_bookings=recent_bookings)
    except Exception as e:
        logger.error(f"Error loading main page data: {e}")
        conn.close()
        return render_template('admin_panel.html',
                             flights_count=0,
                             users_count=0,
                             bookings_count=0,
                             recent_bookings=[])

@app.route('/add_flight', methods=['GET', 'POST'])
def add_flight_page():
    return controller_add_flight()

@app.route('/edit_flights', methods=['GET'])
def edit_flights_page():
    return controller_edit_flights()

@app.route('/edit_flights/process', methods=['POST'])
def edit_flights_process():
    return controller_process_edit_flights()

@app.route('/delete_flight', methods=['GET'])
def delete_flights_page():
    return controller_delete_flights()

@app.route('/delete_flight/process', methods=['POST'])
def delete_flights_process():
    return controller_process_delete_flights()

# User routes
@app.route('/add_user', methods=['GET', 'POST'])
def add_user_page():
    return controller_add_user()

@app.route('/edit_users', methods=['GET']) 
def edit_users_page():
    return controller_edit_users()

@app.route('/edit_users/process', methods=['POST'])
def edit_users_process():
    return controller_process_edit_users()

@app.route('/delete_user', methods=['GET'])
def delete_users_page():
    return controller_delete_users()

@app.route('/delete_user/process', methods=['POST'])
def delete_users_process():
    return controller_process_delete_users()

# Booking routes
@app.route('/view_bookings')
def view_bookings_page():
    return controller_view_bookings()

@app.route('/add_booking', methods=['GET', 'POST'])
def add_booking_page():
    return controller_add_booking()

@app.route('/edit_bookings', methods=['GET'])
def edit_bookings_page():
    return controller_edit_bookings()

@app.route('/edit_bookings/process', methods=['POST'])
def edit_bookings_process():
    return controller_process_edit_bookings()

@app.route('/delete_booking', methods=['GET'])
def delete_bookings_page():
    return controller_delete_bookings()

@app.route('/delete_booking/process', methods=['POST'])
def delete_bookings_process():
    return controller_process_delete_bookings()

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        
        tables = ['users', 'flights', 'booking']
        status = {'database': 'OK', 'tables': {}}
        
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                status['tables'][table] = f'OK ({count} records)'
            except Exception as e:
                status['tables'][table] = f'ERROR: {str(e)}'
                status['database'] = 'PARTIAL'
        
        conn.close()
        return {'status': 'ok', 'details': status}, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {'status': 'error', 'message': str(e)}, 500

if __name__ == '__main__':
    app.run()