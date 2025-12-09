import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from validate import *

class TestValidators(unittest.TestCase):
    
    def test_regCheck_valid(self):
        result, message = regCheck(
            "Ivanov Ivan Ivanovich", 
            "ivan@example.com", 
            "password123", 
            "password123"
        )
        self.assertTrue(result)
        self.assertEqual(message, "Успешно")
    
    def test_regCheck_empty_fields(self):
        result, message = regCheck("", "", "", "")
        self.assertFalse(result)
        self.assertIn("Заполните все обязательные поля", message)
    
    def test_regCheck_short_fio(self):
        result, message = regCheck(
            "I", 
            "ivan@example.com", 
            "password123", 
            "password123"
        )
        self.assertFalse(result)
        self.assertIn("ФИО должно содержать минимум 2 символа", message)
    
    def test_regCheck_invalid_email(self):
        result, message = regCheck(
            "Ivanov Ivan", 
            "invalid-email", 
            "password123", 
            "password123"
        )
        self.assertFalse(result)
        self.assertIn("Неверный формат email", message)
    
    def test_regCheck_short_password(self):
        result, message = regCheck(
            "Ivanov Ivan", 
            "ivan@example.com", 
            "12345", 
            "12345"
        )
        self.assertFalse(result)
        self.assertIn("Пароль должен быть не менее 6 символов", message)
    
    def test_regCheck_password_mismatch(self):
        result, message = regCheck(
            "Ivanov Ivan", 
            "ivan@example.com", 
            "password123", 
            "password456"
        )
        self.assertFalse(result)
        self.assertIn("Пароли не совпадают", message)
    
    def test_checkFlight_valid(self):
        result, message = checkFlight(
            "Moscow",
            "Saint Petersburg",
            "2025-12-31",
            "2025-12-31",
            "Aeroflot",
            "5000"
        )
        self.assertTrue(result)
        self.assertEqual(message, "Данные корректны") 
    
    def test_checkFlight_same_cities(self):
        result, message = checkFlight(
            "Moscow",
            "Moscow",
            "2025-12-31",
            "2025-12-31",
            "Aeroflot",
            "5000"
        )
        self.assertFalse(result)
        self.assertIn("Города вылета и прилета не должны совпадать", message)
    
    def test_checkFlight_invalid_price(self):
        result, message = checkFlight(
            "Moscow",
            "Saint Petersburg",
            "2025-12-31",
            "2025-12-31",
            "Aeroflot",
            "-100"
        )
        self.assertFalse(result)
        self.assertIn("Цена должна быть положительным числом", message)  
    
    def test_validate_booking_data_valid(self):
        result, message = validate_booking_data(
            "Ivanov Ivan Ivanovich",
            "1",
            "1"
        )
        self.assertTrue(result)
        self.assertEqual(message, "Данные корректны")  
    
    def test_validate_booking_data_empty(self):
        result, message = validate_booking_data("", "", "")
        self.assertFalse(result)
        self.assertIn("Все поля обязательны для заполнения", message)
    
    def test_validate_booking_data_short_passenger(self):
        result, message = validate_booking_data(
            "I",
            "1",
            "1"
        )
        self.assertFalse(result)
        self.assertIn("ФИО пассажира должно содержать минимум 2 символа", message)