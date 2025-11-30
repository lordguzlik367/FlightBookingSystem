from flask import request, render_template, redirect, url_for, flash, session
import sqlite3
import hashlib
from validate import *
from createdb import get_db_connection

# ===== ОБЩИЕ ФУНКЦИИ ПАГИНАЦИИ =====

def get_flights_page(page=0, per_page=10):
    """Получить рейсы с пагинацией"""
    conn = get_db_connection()
    cursor = conn.cursor()
    offset = page * per_page
    
    cursor.execute('SELECT * FROM flights ORDER BY departure_date, departure_city LIMIT ? OFFSET ?', 
                   (per_page, offset))
    flights = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) as total FROM flights')
    total_flights = cursor.fetchone()['total']
    total_pages = (total_flights + per_page - 1) // per_page
    
    conn.close()
    return flights, total_pages

def get_users_page(page=0, per_page=10):
    """Получить пользователей с пагинацией"""
    conn = get_db_connection()
    cursor = conn.cursor()
    offset = page * per_page
    
    cursor.execute('SELECT * FROM users ORDER BY fio LIMIT ? OFFSET ?', 
                   (per_page, offset))
    users = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total']
    total_pages = (total_users + per_page - 1) // per_page
    
    conn.close()
    return users, total_pages

def get_bookings_page(page=0, per_page=10):
    """Получить бронирования с пагинацией"""
    conn = get_db_connection()
    cursor = conn.cursor()
    offset = page * per_page
    
    cursor.execute('''
        SELECT 
            b.id, 
            b.passenger_fio, 
            b.booking_date,
            u.fio as user_fio, 
            u.email as user_email,
            f.departure_city, 
            f.arrival_city, 
            f.departure_date, 
            f.arrival_date, 
            f.company, 
            f.price
        FROM booking b
        JOIN users u ON b.user_id = u.id
        JOIN flights f ON b.flight_id = f.id
        ORDER BY b.booking_date DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    bookings = cursor.fetchall()
    
    cursor.execute('SELECT COUNT(*) as total FROM booking')
    total_bookings = cursor.fetchone()['total']
    total_pages = (total_bookings + per_page - 1) // per_page
    
    conn.close()
    return bookings, total_pages

# ===== КОНТРОЛЛЕРЫ ДЛЯ РЕЙСОВ =====

def controller_add_flight():
    """Добавление нового рейса"""
    if request.method == 'POST':
        departure_city = request.form.get('departure_city', '')
        arrival_city = request.form.get('arrival_city', '')
        departure_date = request.form.get('departure_date', '')
        arrival_date = request.form.get('arrival_date', '')
        company = request.form.get('company', '')
        price = request.form.get('price', '')
        
        is_valid, error_message = checkFlight(
            departure_city, arrival_city, departure_date, arrival_date, company, price
        )
        
        if not is_valid:
            return render_template('add_flight.html', error=error_message)
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO flights 
                   (departure_city, arrival_city, departure_date, arrival_date, company, price) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (departure_city, arrival_city, departure_date, arrival_date, company, int(price))
            )
            conn.commit()
            flash('Рейс успешно добавлен', 'success')
            return redirect('/')
        except Exception as e:
            return render_template('add_flight.html', error=f'Ошибка при сохранении: {str(e)}')
        finally:
            conn.close()
    
    return render_template('add_flight.html')

def controller_edit_flights():
    """Редактирование рейсов с пагинацией"""
    page = request.args.get('page', 0, type=int)
    flights, total_pages = get_flights_page(page)
    return render_template('edit_flights.html', 
                         flights=flights, 
                         current_page=page,
                         total_pages=total_pages)

def controller_process_edit_flights():
    """Обработка редактирования рейсов"""
    if request.method == 'POST':
        flight_id = request.form.get('flight_id')
        departure_city = request.form.get('departure_city')
        arrival_city = request.form.get('arrival_city')
        departure_date = request.form.get('departure_date')
        arrival_date = request.form.get('arrival_date')
        company = request.form.get('company')
        price = request.form.get('price')
        
        # Валидация входных данных
        if not flight_id:
            flash('Ошибка: ID рейса не указан', 'error')
            return redirect(url_for('edit_flights_page'))
        
        if not validate_flight_exists(flight_id):
            flash('Ошибка: рейс не существует', 'error')
            return redirect(url_for('edit_flights_page'))
        
        is_valid, error_message = checkFlight(
            departure_city, arrival_city, departure_date, arrival_date, company, price
        )
        
        if not is_valid:
            flash(f'Ошибка валидации: {error_message}', 'error')
            return redirect(url_for('edit_flights_page'))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                '''UPDATE flights SET 
                   departure_city=?, arrival_city=?, departure_date=?, 
                   arrival_date=?, company=?, price=?
                   WHERE id=?''',
                (departure_city, arrival_city, departure_date, arrival_date, company, int(price), flight_id)
            )
            conn.commit()
            
            flash('Рейс успешно обновлен', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении: {str(e)}', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('edit_flights_page'))

def controller_delete_flights():
    """Удаление рейсов с пагинацией"""
    page = request.args.get('page', 0, type=int)
    flights, total_pages = get_flights_page(page)
    return render_template('delete_flights.html', 
                         flights=flights, 
                         current_page=page,
                         total_pages=total_pages)

def controller_process_delete_flights():
    """Обработка удаления рейса"""
    try:
        flight_id = request.form.get('flight_id')
        
        if not flight_id:
            flash('Ошибка: ID рейса не указан', 'error')
            return redirect(url_for('delete_flights_page'))
        
        # Проверяем существование рейса
        if not validate_flight_exists(flight_id):
            flash('Ошибка: рейс не существует', 'error')
            return redirect(url_for('delete_flights_page'))
        
        conn = get_db_connection()
        
        # Проверяем, есть ли связанные бронирования
        booking_count = conn.execute(
            "SELECT COUNT(*) FROM booking WHERE flight_id = ?", 
            (flight_id,)
        ).fetchone()[0]
        
        if booking_count > 0:
            flash(f'Невозможно удалить рейс. Существует {booking_count} связанных бронирований', 'error')
            conn.close()
            return redirect(url_for('delete_flights_page'))
        
        # Удаляем рейс
        conn.execute("DELETE FROM flights WHERE id = ?", (flight_id,))
        conn.commit()
        conn.close()
        
        flash('Рейс успешно удален', 'success')
        
    except Exception as e:
        flash(f'Ошибка при удалении рейса: {str(e)}', 'error')
    
    return redirect(url_for('delete_flights_page'))

# ===== КОНТРОЛЛЕРЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ =====

def controller_add_user():
    """Добавление нового пользователя"""
    if request.method == 'POST':
        fio = request.form.get('fio', '')
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        is_valid, error_message = regCheck(fio, email, password, password)
        
        if not is_valid:
            return render_template('add_user.html', error=error_message)
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                'INSERT INTO users (fio, email, password) VALUES (?, ?, ?)',
                (fio, email, hashed_password)
            )
            conn.commit()
            flash('Пользователь успешно добавлен', 'success')
            return redirect('/')
        except sqlite3.IntegrityError:
            return render_template('add_user.html', error='Пользователь с таким email уже существует')
        except Exception as e:
            return render_template('add_user.html', error=f'Ошибка при сохранении: {str(e)}')
        finally:
            conn.close()
    
    return render_template('add_user.html')

def controller_edit_users():
    """Редактирование пользователей с пагинацией"""
    page = request.args.get('page', 0, type=int)
    users, total_pages = get_users_page(page)
    return render_template('edit_users.html', 
                         users=users, 
                         current_page=page,
                         total_pages=total_pages)

def controller_process_edit_users():
    """Обработка редактирования пользователей"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        fio = request.form.get('fio')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Валидация входных данных
        if not user_id:
            flash('Ошибка: ID пользователя не указан', 'error')
            return redirect(url_for('edit_users_page'))
        
        if not validate_user_exists(user_id):
            flash('Ошибка: пользователь не существует', 'error')
            return redirect(url_for('edit_users_page'))
        
        # Базовая валидация полей
        if not fio or not email:
            flash('ФИО и email обязательны для заполнения', 'error')
            return redirect(url_for('edit_users_page'))
        
        fio = fio.strip()
        if len(fio) < 2:
            flash('ФИО должно содержать минимум 2 символа', 'error')
            return redirect(url_for('edit_users_page'))
        
        email = email.strip()
        if '@' not in email or '.' not in email:
            flash('Неверный формат email', 'error')
            return redirect(url_for('edit_users_page'))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if password:
                if len(password) < 6:
                    flash('Пароль должен быть не менее 6 символов', 'error')
                    return redirect(url_for('edit_users_page'))
                
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    'UPDATE users SET fio=?, email=?, password=? WHERE id=?',
                    (fio, email, hashed_password, user_id)
                )
            else:
                cursor.execute(
                    'UPDATE users SET fio=?, email=? WHERE id=?',
                    (fio, email, user_id)
                )
            conn.commit()
            flash('Пользователь успешно обновлен', 'success')
        except sqlite3.IntegrityError:
            flash('Пользователь с таким email уже существует', 'error')
        except Exception as e:
            flash(f'Ошибка при обновлении: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('edit_users_page'))

def controller_delete_users():
    """Удаление пользователей с пагинацией"""
    page = request.args.get('page', 0, type=int)
    users, total_pages = get_users_page(page)
    return render_template('delete_users.html', 
                         users=users, 
                         current_page=page,
                         total_pages=total_pages)

def controller_process_delete_users():
    """Обработка удаления пользователей"""
    if request.method == 'POST':
        user_ids = request.form.getlist('user_ids')
        
        if not user_ids:
            flash('Не выбрано ни одного пользователя для удаления', 'error')
            return redirect(url_for('delete_users_page'))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            deleted_count = 0
            
            for user_id in user_ids:
                # Проверяем существование пользователя
                if not validate_user_exists(user_id):
                    flash(f'Пользователь с ID {user_id} не существует', 'error')
                    continue
                
                # Проверяем, есть ли бронирования у пользователя
                cursor.execute("SELECT COUNT(*) as count FROM booking WHERE user_id=?", (user_id,))
                booking_count = cursor.fetchone()['count']
                
                if booking_count > 0:
                    flash(f'Невозможно удалить пользователя ID {user_id} - есть связанные бронирования', 'error')
                    continue
                
                cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
                deleted_count += 1
            
            conn.commit()
            
            if deleted_count > 0:
                flash(f'Успешно удалено пользователей: {deleted_count}', 'success')
            else:
                flash('Не удалось удалить ни одного пользователя', 'error')
                
        except Exception as e:
            flash(f'Ошибка при удалении: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('delete_users_page'))

# ===== КОНТРОЛЛЕРЫ ДЛЯ БРОНИРОВАНИЙ =====

def controller_view_bookings():
    """Просмотр бронирований с пагинацией"""
    page = request.args.get('page', 0, type=int)
    bookings, total_pages = get_bookings_page(page)
    return render_template('view_bookings.html', 
                         bookings=bookings, 
                         current_page=page,
                         total_pages=total_pages)

def controller_add_booking():
    """Добавление нового бронирования"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        flight_id = request.form.get('flight_id')
        passenger_fio = request.form.get('passenger_fio')
        
        # Валидация данных
        is_valid, error_message = validate_booking_data(passenger_fio, user_id, flight_id)
        if not is_valid:
            return render_template('add_booking.html', error=error_message)
        
        # Проверяем существование пользователя и рейса
        if not validate_user_exists(user_id):
            return render_template('add_booking.html', error='Пользователь не найден')
        if not validate_flight_exists(flight_id):
            return render_template('add_booking.html', error='Рейс не найден')
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute(
                '''INSERT INTO booking (user_id, flight_id, passenger_fio, booking_date) 
                   VALUES (?, ?, ?, datetime('now'))''',
                (user_id, flight_id, passenger_fio)
            )
            conn.commit()
            flash('Бронирование успешно добавлено', 'success')
            return redirect('/')
        except Exception as e:
            return render_template('add_booking.html', error=f'Ошибка при сохранении: {str(e)}')
        finally:
            conn.close()
    
    # Получаем списки пользователей и рейсов для формы
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    conn.close()
    
    return render_template('add_booking.html', users=users, flights=flights)

def controller_edit_bookings():
    """Редактирование бронирований с пагинацией"""
    page = request.args.get('page', 0, type=int)
    bookings, total_pages = get_bookings_page(page)
    
    # Получаем списки пользователей и рейсов для выпадающих списков
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM flights")
    flights = cursor.fetchall()
    conn.close()
    
    return render_template('edit_bookings.html', 
                         bookings=bookings, 
                         users=users,
                         flights=flights,
                         current_page=page,
                         total_pages=total_pages)

def controller_process_edit_bookings():
    """Обработка редактирования бронирований"""
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        user_id = request.form.get('user_id')
        flight_id = request.form.get('flight_id')
        passenger_fio = request.form.get('passenger_fio')
        
        # Валидация входных данных
        if not booking_id:
            flash('Ошибка: ID бронирования не указан', 'error')
            return redirect(url_for('edit_bookings_page'))
        
        if not validate_booking_exists(booking_id):
            flash('Ошибка: бронирование не существует', 'error')
            return redirect(url_for('edit_bookings_page'))
        
        is_valid, error_message = validate_booking_data(passenger_fio, user_id, flight_id)
        if not is_valid:
            flash(f'Ошибка валидации: {error_message}', 'error')
            return redirect(url_for('edit_bookings_page'))
        
        # Проверяем существование пользователя и рейса
        if not validate_user_exists(user_id):
            flash('Пользователь не найден', 'error')
            return redirect(url_for('edit_bookings_page'))
        if not validate_flight_exists(flight_id):
            flash('Рейс не найден', 'error')
            return redirect(url_for('edit_bookings_page'))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE booking SET user_id=?, flight_id=?, passenger_fio=? WHERE id=?',
                (user_id, flight_id, passenger_fio, booking_id)
            )
            conn.commit()
            flash('Бронирование успешно обновлено', 'success')
        except Exception as e:
            flash(f'Ошибка при обновлении: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('edit_bookings_page'))

def controller_delete_bookings():
    """Удаление бронирований с пагинацией"""
    page = request.args.get('page', 0, type=int)
    bookings, total_pages = get_bookings_page(page)
    return render_template('delete_bookings.html', 
                         bookings=bookings, 
                         current_page=page,
                         total_pages=total_pages)

def controller_process_delete_bookings():
    """Обработка удаления бронирований"""
    if request.method == 'POST':
        booking_ids = request.form.getlist('booking_ids')
        
        if not booking_ids:
            flash('Не выбрано ни одного бронирования для удаления', 'error')
            return redirect(url_for('delete_bookings_page'))
        
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            deleted_count = 0
            
            for booking_id in booking_ids:
                # Проверяем существование бронирования
                if not validate_booking_exists(booking_id):
                    flash(f'Бронирование с ID {booking_id} не существует', 'error')
                    continue
                
                cursor.execute("DELETE FROM booking WHERE id=?", (booking_id,))
                deleted_count += 1
            
            conn.commit()
            
            if deleted_count > 0:
                flash(f'Успешно удалено бронирований: {deleted_count}', 'success')
            else:
                flash('Не удалось удалить ни одного бронирования', 'error')
                
        except Exception as e:
            flash(f'Ошибка при удалении: {str(e)}', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('delete_bookings_page'))