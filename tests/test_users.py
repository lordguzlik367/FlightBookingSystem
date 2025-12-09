import unittest
import os
import sys
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import create_database, get_db_connection

class TestUsers(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.test_db = 'test_database.db'
        app.config['DATABASE_FILE'] = self.test_db
        
        self.client = app.test_client()
        
        create_database()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_user_and_verify_db(self):
        conn = get_db_connection()
        initial_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        conn.close()
        
        response = self.client.post('/add_user', data={
            'fio': 'Ivanov Ivan Ivanovich',
            'email': 'ivanov@test.ru',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        html = response.get_data(as_text=True)
        self.assertNotIn('Ошибка', html)
        self.assertNotIn('ошибка', html.lower())
        
        conn = get_db_connection()
        
        final_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        self.assertEqual(final_count, initial_count + 1, 
                        f"Ожидалось {initial_count + 1} пользователей, но получили {final_count}")
        
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', 
            ('ivanov@test.ru',)
        ).fetchone()
        
        self.assertIsNotNone(user, "Пользователь не найден в базе данных")
        self.assertEqual(user['fio'], 'Ivanov Ivan Ivanovich')
        self.assertEqual(user['email'], 'ivanov@test.ru')
        
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        self.assertEqual(user['password'], hashed_password, 
                        f"Пароль не совпадает. Ожидалось: {hashed_password}, получили: {user['password']}")
        
        conn.close()

    def test_edit_user_and_verify_db(self):
        conn = get_db_connection()
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Ivanov Ivan', 'ivanov@test.ru', hashed_password))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        conn = get_db_connection()
        user_before = conn.execute(
            'SELECT * FROM users WHERE id = ?', 
            (user_id,)
        ).fetchone()
        self.assertEqual(user_before['fio'], 'Ivanov Ivan')
        self.assertEqual(user_before['email'], 'ivanov@test.ru')
        conn.close()

        response = self.client.post('/edit_users/process', data={
            'user_id': user_id,
            'fio': 'Ivanov Ivan Petrovich',
            'email': 'ivanov@test.ru',
            'password': 'newpassword456'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        updated_user = conn.execute(
            'SELECT * FROM users WHERE id = ?', 
            (user_id,)
        ).fetchone()
        
        self.assertEqual(updated_user['fio'], 'Ivanov Ivan Petrovich')
        self.assertEqual(updated_user['email'], 'ivanov@test.ru')
        
        new_hashed_password = hashlib.sha256('newpassword456'.encode()).hexdigest()
        self.assertEqual(updated_user['password'], new_hashed_password)
        
        conn.close()

    def test_delete_user_and_verify_db(self):
        conn = get_db_connection()
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Ivanov Ivan', 'ivanov@test.ru', hashed_password))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        initial_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        conn.close()

        conn = get_db_connection()
        user_before = conn.execute(
            'SELECT * FROM users WHERE id = ?', 
            (user_id,)
        ).fetchone()
        self.assertIsNotNone(user_before)
        conn.close()

        response = self.client.post('/delete_user/process', data={
            'user_ids': [user_id]
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        final_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        self.assertEqual(final_count, initial_count - 1)
        
        deleted_user = conn.execute(
            'SELECT * FROM users WHERE id = ?', 
            (user_id,)
        ).fetchone()
        self.assertIsNone(deleted_user)
        
        conn.close()

    def test_add_user_invalid_data(self):
        response = self.client.post('/add_user', data={
            'fio': 'Test User',
            'email': 'test@test.ru',
            'password': '123'  # Слишком короткий пароль
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', 
            ('test@test.ru',)
        ).fetchone()
        self.assertIsNone(user)
        
        conn.close()


    def test_view_users_pages(self):
        response = self.client.get('/edit_users')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/delete_user')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()