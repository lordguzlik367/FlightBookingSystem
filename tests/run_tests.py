import unittest
import sys
import os

def run_all_tests():
    """Запуск всех тестов"""
    test_files = [
        'test_health.TestHealth',
        'test_flights.TestFlights',
        'test_users.TestUsers', 
        'test_bookings.TestBookings'
    ]
    
    loader = unittest.TestLoader()
    suites = []
    
    for test_file in test_files:
        try:
            file_name, class_name = test_file.split('.')
            module = __import__(file_name)
            test_class = getattr(module, class_name)
            suite = loader.loadTestsFromTestCase(test_class)
            suites.append(suite)
            print(f"✓ Загружены тесты из {file_name}")
        except Exception as e:
            print(f"✗ Ошибка загрузки {test_file}: {e}")
    
    complete_suite = unittest.TestSuite(suites)
    
    print(f"\nЗапуск {complete_suite.countTestCases()} тестов...")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(complete_suite)
    
    print(f"\n{'='*50}")
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*50}")
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалов: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(run_all_tests())