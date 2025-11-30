import unittest
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from createdb import create_database

class TestHealth(unittest.TestCase):
    def setUp(self):
        """Настройка тестового окружения"""
        app.config['TESTING'] = True
        
        # Используем временную базу данных
        self.test_db = 'test_database.db'
        app.config['DATABASE_FILE'] = self.test_db
        
        self.client = app.test_client()
        
        # Создаем тестовую базу данных
        create_database()

    def tearDown(self):
        """Очистка после тестов"""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.get_json()
        self.assertEqual(response_data['status'], 'ok')

if __name__ == '__main__':
    unittest.main()