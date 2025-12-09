import unittest
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import get_db_connection, create_database

class TestFlights(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.config['DATABASE_FILE'] = self.db_path
        
        self.client = app.test_client()
        
        create_database()

    def tearDown(self):
        """Очистка после тестов"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data['status'], 'ok')
        
        self.assertIn('details', response_data)
        self.assertIn('database', response_data['details'])
        self.assertEqual(response_data['details']['database'], 'OK')

    def test_add_flight_and_verify_db(self):
        conn = get_db_connection()
        initial_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        conn.close()
        
        response = self.client.post('/add_flight', data={
            'departure_city': 'Moscow',
            'arrival_city': 'Saint Petersburg',
            'departure_date': '2026-01-15',
            'arrival_date': '2026-01-15',
            'company': 'Aeroflot',
            'price': '5000'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        
        final_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        self.assertEqual(final_count, initial_count + 1)
        
        flight = conn.execute(
            'SELECT * FROM flights WHERE departure_city = ? AND arrival_city = ?',
            ('Moscow', 'Saint Petersburg')
        ).fetchone()
        
        self.assertIsNotNone(flight)
        self.assertEqual(flight['departure_city'], 'Moscow')
        self.assertEqual(flight['arrival_city'], 'Saint Petersburg')
        self.assertEqual(flight['departure_date'], '2026-01-15')
        self.assertEqual(flight['arrival_date'], '2026-01-15')
        self.assertEqual(flight['company'], 'Aeroflot')
        self.assertEqual(flight['price'], 5000)
        
        conn.close()

    def test_edit_flight_and_verify_db(self):
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO flights (departure_city, arrival_city, departure_date, 
                               arrival_date, company, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Moscow', 'Saint Petersburg', '2026-01-15', 
              '2026-01-15', 'Aeroflot', 5000))
        conn.commit()
        
        flight = conn.execute(
            'SELECT id FROM flights WHERE departure_city = ?', 
            ('Moscow',)
        ).fetchone()
        flight_id = flight['id']
        conn.close()
        
        response = self.client.post('/edit_flights/process', data={
            'flight_id': str(flight_id),
            'departure_city': 'Moscow',
            'arrival_city': 'Kazan',
            'departure_date': '2026-01-16',
            'arrival_date': '2026-01-16',
            'company': 'S7 Airlines',
            'price': '4500'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        updated_flight = conn.execute(
            'SELECT * FROM flights WHERE id = ?', 
            (flight_id,)
        ).fetchone()
        
        self.assertIsNotNone(updated_flight)
        self.assertEqual(updated_flight['departure_city'], 'Moscow')
        self.assertEqual(updated_flight['arrival_city'], 'Kazan')
        self.assertEqual(updated_flight['departure_date'], '2026-01-16')
        self.assertEqual(updated_flight['arrival_date'], '2026-01-16')
        self.assertEqual(updated_flight['company'], 'S7 Airlines')
        self.assertEqual(updated_flight['price'], 4500)
        
        conn.close()

    def test_delete_flight_and_verify_db(self):
        """Тест удаления рейса с проверкой в БД"""
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO flights (departure_city, arrival_city, departure_date, 
                               arrival_date, company, price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Moscow', 'Sochi', '2026-01-20', 
              '2026-01-20', 'Pobeda', 7000))
        conn.commit()
        
        initial_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        
        flight = conn.execute(
            'SELECT id FROM flights WHERE arrival_city = ?', 
            ('Sochi',)
        ).fetchone()
        flight_id = flight['id']
        conn.close()
        
        conn = get_db_connection()
        flight_before = conn.execute(
            'SELECT * FROM flights WHERE id = ?', 
            (flight_id,)
        ).fetchone()
        self.assertIsNotNone(flight_before)
        self.assertEqual(flight_before['arrival_city'], 'Sochi')
        conn.close()
        
        response = self.client.post('/delete_flight/process', data={
            'flight_id': str(flight_id)
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        final_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        self.assertEqual(final_count, initial_count - 1)
        
        deleted_flight = conn.execute(
            'SELECT * FROM flights WHERE id = ?', 
            (flight_id,)
        ).fetchone()
        self.assertIsNone(deleted_flight)
        
        conn.close()

    def test_add_flight_invalid_data(self):
        conn = get_db_connection()
        initial_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        conn.close()
        
        response = self.client.post('/add_flight', data={
            'departure_city': 'Moscow',
            'arrival_city': 'Saint Petersburg',
            'departure_date': '2026-01-15',
            'arrival_date': '2026-01-15',
            'company': 'Aeroflot',
            'price': '-100'  # Отрицательная цена
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        
        flight = conn.execute(
            '''SELECT * FROM flights WHERE departure_city = ? 
            AND arrival_city = ? AND company = ? AND price = ?''',
            ('Moscow', 'Saint Petersburg', 'Aeroflot', -100)
        ).fetchone()
        
        self.assertIsNone(flight)  
        
        final_count = conn.execute('SELECT COUNT(*) FROM flights').fetchone()[0]
        self.assertEqual(final_count, initial_count)  # Количество не должно измениться
        
        conn.close()

if __name__ == '__main__':
    unittest.main()