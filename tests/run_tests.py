import unittest
import sys
import os

def run_all_tests():
    test_files = [
        'test_health.TestHealth',
        'test_flights.TestFlights',
        'test_users.TestUsers', 
        'test_bookings.TestBookings',
        'test_validators.TestValidators'
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
        except ImportError as e:
            print(f"✗ Ошибка импорта {test_file}: {e}")
        except AttributeError as e:
            print(f"✗ Ошибка загрузки класса {test_file}: {e}")
        except Exception as e:
            print(f"✗ Ошибка загрузки {test_file}: {e}")
    
    if not suites:
        print("✗ Не удалось загрузить ни одного теста")
        return 1
    
    complete_suite = unittest.TestSuite(suites)
    
    print(f"\nЗапуск {complete_suite.countTestCases()} тестов...")
    print("=" * 60)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(complete_suite)
    
    print(f"\n{'='*50}")
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*50}")
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалов: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    
    if result.failures:
        print("\nПроваленные тесты:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nТесты с ошибками:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    
    exit_code = run_all_tests()
    sys.exit(exit_code)