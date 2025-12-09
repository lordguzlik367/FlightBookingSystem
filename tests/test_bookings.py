import unittest
import os
import sys
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import create_database, get_db_connection

class TestBookings(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.test_db = 'test_database.db'
        app.config['DATABASE_FILE'] = self.test_db
        
        self.client = app.test_client()
        
        create_database()
        
        conn = get_db_connection()
        
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Ivanov Ivan', 'ivanov@test.ru', hashed_password))
        
        conn.execute('''
            INSERT INTO flights (departure_city, arrival_city, departure_date, arrival_date, company, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Moscow', 'Saint Petersburg', '2026-01-15', '2026-01-15', 'Aeroflot', 5000))
        
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_booking_and_verify_db(self):
        conn = get_db_connection()
        initial_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        conn.close()
        
        response = self.client.post('/add_booking', data={
            'user_id': 1,
            'flight_id': 1,
            'passenger_fio': 'Petrov Petr Petrovich'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        
        final_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        self.assertEqual(final_count, initial_count + 1)
        
        booking = conn.execute(
            'SELECT * FROM booking WHERE passenger_fio = ?', 
            ('Petrov Petr Petrovich',)
        ).fetchone()
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking['user_id'], 1)
        self.assertEqual(booking['flight_id'], 1)
        self.assertEqual(booking['passenger_fio'], 'Petrov Petr Petrovich')
        self.assertIsNotNone(booking['booking_date'])  # Дата должна быть установлена
        
        conn.close()

    def test_edit_booking_and_verify_db(self):
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO booking (user_id, flight_id, passenger_fio, booking_date)
            VALUES (?, ?, ?, datetime("now"))
        ''', (1, 1, 'Petrov Petr'))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        booking_before = conn.execute(
            'SELECT * FROM booking WHERE id = ?', 
            (booking_id,)
        ).fetchone()
        old_booking_date = booking_before['booking_date']
        conn.close()

        self.assertEqual(booking_before['passenger_fio'], 'Petrov Petr')

        response = self.client.post('/edit_bookings/process', data={
            'booking_id': booking_id,
            'user_id': 1,
            'flight_id': 1,
            'passenger_fio': 'Petrov Petr Ivanovich'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        updated_booking = conn.execute(
            'SELECT * FROM booking WHERE id = ?', 
            (booking_id,)
        ).fetchone()
        
        self.assertEqual(updated_booking['passenger_fio'], 'Petrov Petr Ivanovich')
        self.assertEqual(updated_booking['user_id'], 1)
        self.assertEqual(updated_booking['flight_id'], 1)
        self.assertEqual(updated_booking['booking_date'], old_booking_date)  # Дата не должна измениться
        
        conn.close()

    def test_delete_booking_and_verify_db(self):
        """Тест удаления бронирования с проверкой в БД"""
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO booking (user_id, flight_id, passenger_fio, booking_date)
            VALUES (?, ?, ?, datetime("now"))
        ''', (1, 1, 'Petrov Petr'))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        initial_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        conn.close()

        conn = get_db_connection()
        booking_before = conn.execute(
            'SELECT * FROM booking WHERE id = ?', 
            (booking_id,)
        ).fetchone()
        self.assertIsNotNone(booking_before)
        conn.close()

        response = self.client.post('/delete_booking/process', data={
            'booking_ids': [booking_id]
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        final_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        self.assertEqual(final_count, initial_count - 1)
        
        deleted_booking = conn.execute(
            'SELECT * FROM booking WHERE id = ?', 
            (booking_id,)
        ).fetchone()
        self.assertIsNone(deleted_booking)
        
        conn.close()

    def test_add_booking_invalid_data(self):
        conn = get_db_connection()
        initial_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        conn.close()
        
        response = self.client.post('/add_booking', data={
            'user_id': 999,  # Несуществующий пользователь
            'flight_id': 1,
            'passenger_fio': 'Test Passenger'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        booking = conn.execute(
            'SELECT * FROM booking WHERE passenger_fio = ?', 
            ('Test Passenger',)
        ).fetchone()
        self.assertIsNone(booking)
        
        final_count = conn.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
        self.assertEqual(final_count, initial_count)  # Не должно быть изменений
        
        conn.close()

    def test_view_bookings_pages(self):
        """Тест отображения страниц с бронированиями"""
        response = self.client.get('/view_bookings')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/edit_bookings')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/delete_booking')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()