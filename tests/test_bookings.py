import unittest
import os
import sys
import hashlib

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import create_database, get_db_connection

class TestBookings(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Используем временную базу данных
        self.test_db = 'test_database.db'
        app.config['DATABASE_FILE'] = self.test_db
        
        self.client = app.test_client()
        
        # Создаем тестовую базу данных
        create_database()
        
        # Добавляем тестовые данные: пользователя и рейс
        conn = get_db_connection()
        
        # Добавляем пользователя
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Иванов Иван', 'ivanov@test.ru', hashed_password))
        
        # Добавляем рейс
        conn.execute('''
            INSERT INTO flights (departure_city, arrival_city, departure_date, arrival_date, company, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Москва', 'Санкт-Петербург', '2026-01-15', '2026-01-15', 'Аэрофлот', 5000))
        
        conn.commit()
        conn.close()

    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_booking(self):
        """Тест добавления бронирования"""
        response = self.client.post('/add_booking', data={
            'user_id': 1,
            'flight_id': 1,
            'passenger_fio': 'Петров Петр Петрович'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что бронирование добавлено в базу
        conn = get_db_connection()
        booking = conn.execute('SELECT * FROM booking WHERE passenger_fio = ?', ('Петров Петр Петрович',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(booking)
        self.assertEqual(booking['user_id'], 1)
        self.assertEqual(booking['flight_id'], 1)

    def test_edit_booking(self):
        """Тест редактирования бронирования"""
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO booking (user_id, flight_id, passenger_fio, booking_date)
            VALUES (?, ?, ?, datetime('now'))
        ''', (1, 1, 'Петров Петр'))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        # Редактируем бронирование
        response = self.client.post('/edit_bookings/process', data={
            'booking_id': booking_id,
            'user_id': 1,
            'flight_id': 1,
            'passenger_fio': 'Петров Петр Иванович'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем изменения
        conn = get_db_connection()
        updated_booking = conn.execute('SELECT * FROM booking WHERE id = ?', (booking_id,)).fetchone()
        conn.close()
        
        self.assertEqual(updated_booking['passenger_fio'], 'Петров Петр Иванович')

    def test_delete_booking(self):
        """Тест удаления бронирования"""
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO booking (user_id, flight_id, passenger_fio, booking_date)
            VALUES (?, ?, ?, datetime('now'))
        ''', (1, 1, 'Петров Петр'))
        conn.commit()
        booking_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        # Удаляем бронирование
        response = self.client.post('/delete_booking/process', data={
            'booking_ids': [booking_id]
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что бронирование удалено
        conn = get_db_connection()
        deleted_booking = conn.execute('SELECT * FROM booking WHERE id = ?', (booking_id,)).fetchone()
        conn.close()
        
        self.assertIsNone(deleted_booking)

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