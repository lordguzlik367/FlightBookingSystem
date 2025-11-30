import unittest
import os
import sys
import hashlib

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import create_database, get_db_connection

class TestUsers(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.test_db = 'test_database.db'
        app.config['DATABASE_FILE'] = self.test_db
        
        self.client = app.test_client()
        
        create_database()

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_user(self):
        """Тест добавления пользователя"""
        response = self.client.post('/add_user', data={
            'fio': 'Иванов Иван Иванович',
            'email': 'ivanov@test.ru',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', ('ivanov@test.ru',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(user)
        self.assertEqual(user['fio'], 'Иванов Иван Иванович')
        
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        self.assertEqual(user['password'], hashed_password)

    def test_edit_user(self):
        """Тест редактирования пользователя"""
        conn = get_db_connection()
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Иванов Иван', 'ivanov@test.ru', hashed_password))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        # Редактируем пользователя
        response = self.client.post('/edit_users/process', data={
            'user_id': user_id,
            'fio': 'Иванов Иван Петрович',
            'email': 'ivanov@test.ru',
            'password': 'newpassword456'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем изменения
        conn = get_db_connection()
        updated_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        self.assertEqual(updated_user['fio'], 'Иванов Иван Петрович')
        
        # Проверяем, что пароль обновлен
        new_hashed_password = hashlib.sha256('newpassword456'.encode()).hexdigest()
        self.assertEqual(updated_user['password'], new_hashed_password)

    def test_delete_user(self):
        """Тест удаления пользователя"""
        conn = get_db_connection()
        hashed_password = hashlib.sha256('password123'.encode()).hexdigest()
        conn.execute('''
            INSERT INTO users (fio, email, password)
            VALUES (?, ?, ?)
        ''', ('Иванов Иван', 'ivanov@test.ru', hashed_password))
        conn.commit()
        user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()

        # Удаляем пользователя
        response = self.client.post('/delete_user/process', data={
            'user_ids': [user_id]
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что пользователь удален
        conn = get_db_connection()
        deleted_user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        self.assertIsNone(deleted_user)

    def test_view_users_pages(self):
        """Тест отображения страниц с пользователями"""
        response = self.client.get('/edit_users')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/delete_user')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()