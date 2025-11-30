from datetime import datetime, date
from createdb import get_db_connection

def regCheck(fio, email, password, confirm_password):
    if not fio or not password or not confirm_password:
        return False, 'Заполните все обязательные поля'

    fio = fio.strip()
    if len(fio) < 2:
        return False, 'ФИО должно содержать минимум 2 символа'
    if len(fio) > 100:
        return False, 'ФИО не должно превышать 100 символов'
    
    if email:
        email = email.strip()
        if len(email) > 100:
            return False, 'Email не должен превышать 100 символов'
        if '@' not in email or '.' not in email:
            return False, 'Неверный формат email'
    else:
        return False, 'Введите email'
        
    
    if len(password) < 6:
        return False, 'Пароль должен быть не менее 6 символов'
    elif password != confirm_password:
        return False, 'Пароли не совпадают'
    return True, 'Успешно'

def checkFlight(departure_city, arrival_city, departure_date, arrival_date, company, price):
    if not departure_city or not arrival_city or not departure_date or not arrival_date or not company or not price:
        return False, 'Заполните все обязательные поля'
    
    departure_city = departure_city.strip()
    arrival_city = arrival_city.strip()
    
    if len(departure_city) < 2:
        return False, 'Город вылета должен содержать минимум 2 символа'
    if len(arrival_city) < 2:
        return False, 'Город прилета должен содержать минимум 2 символа'
    
    if departure_city == arrival_city:
        return False, 'Города вылета и прилета не должны совпадать'
    
    try:
        dep_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
        arr_date = datetime.strptime(arrival_date, '%Y-%m-%d').date()
        today = date.today()
        
        if dep_date < today:
            return False, 'Дата вылета не может быть в прошлом'
        
        if arr_date < dep_date:
            return False, 'Дата прилета не может быть раньше даты вылета'
            
    except ValueError:
        return False, 'Неверный формат даты'
    
    company = company.strip()
    if len(company) < 2:
        return False, 'Название компании должно содержать минимум 2 символа'
    
    try:
        price_int = int(price)
        if price_int <= 0:
            return False, 'Цена должна быть положительным числом'
        if price_int > 1000000:
            return False, 'Цена не может превышать 1 000 000 рублей'
    except ValueError:
        return False, 'Цена должна быть числом'
    
    return True, 'Данные корректны'

def checkBooking(passenger_fio, user_id, flight_id):

    """Валидация данных бронирования"""
    if not passenger_fio or not user_id or not flight_id:
        return False, 'Все поля обязательны для заполнения'
    
    passenger_fio = passenger_fio.strip()
    if len(passenger_fio) < 2:
        return False, 'ФИО пассажира должно содержать минимум 2 символа'
    if len(passenger_fio) > 100:
        return False, 'ФИО пассажира не должно превышать 100 символов'
    
    try:
        int(user_id)
        int(flight_id)
    except (TypeError, ValueError):
        return False, 'Неверный идентификатор пользователя или рейса'
    
    return True, 'Данные корректны'

def validate_booking_data(passenger_fio, user_id, flight_id):
    """Валидация данных бронирования"""
    if not passenger_fio or not user_id or not flight_id:
        return False, 'Все поля обязательны для заполнения'
    
    passenger_fio = passenger_fio.strip()
    if len(passenger_fio) < 2:
        return False, 'ФИО пассажира должно содержать минимум 2 символа'
    if len(passenger_fio) > 100:
        return False, 'ФИО пассажира не должно превышать 100 символов'
    
    try:
        int(user_id)
        int(flight_id)
    except (TypeError, ValueError):
        return False, 'Неверный идентификатор пользователя или рейса'
    
    return True, 'Данные корректны'

def validate_user_exists(user_id):
    """Проверка существования пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def validate_flight_exists(flight_id):
    """Проверка существования рейса"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM flights WHERE id = ?", (flight_id,))
    flight = cursor.fetchone()
    conn.close()
    return flight is not None

def validate_booking_exists(booking_id):
    """Проверка существования бронирования"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM booking WHERE id = ?", (booking_id,))
    booking = cursor.fetchone()
    conn.close()
    return booking is not None