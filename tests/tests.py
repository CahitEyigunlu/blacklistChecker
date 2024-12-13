from rich.table import Table
from utils.display import Display, console

# Test sınıflarını import et
from tests.test_network import NetworkTests
from tests.test_databases import DatabaseTests
from tests.test_rabbitmq import RabbitMQTests
from tests.test_blacklist import BlacklistTests


def run_tests():
    """
    Tüm testleri çalıştırır ve sonuçları bir liste olarak döndürür.
    """
    display = Display()
    test_results = []

    # Network testleri
    display.print_section_header("Network Testleri")
    network_result = NetworkTests().run()
    test_results.append(["Network Testleri", "Başarılı" if network_result else "Başarısız"])

    # Database testleri
    display.print_section_header("Database Testleri")
    database_tests = DatabaseTests()

    # SQLite bağlantı testi
    display.print_section_header("SQLite Testleri")
    sqlite_result = database_tests.test_sqlite_connection()
    test_results.append(["SQLite Testleri", "Başarılı" if sqlite_result else "Başarısız"])

    # Tüm veritabanı testleri
    database_result = database_tests.run()
    test_results.append(["Database Testleri", "Başarılı" if database_result else "Başarısız"])

    # RabbitMQ testleri
    display.print_section_header("RabbitMQ Testleri")
    rabbitmq_result = RabbitMQTests().run()
    test_results.append(["RabbitMQ Testleri", "Başarılı" if rabbitmq_result else "Başarısız"])

    # Blacklist testleri
    display.print_section_header("Blacklist Testleri")
    blacklist_result = BlacklistTests().run()
    test_results.append(["Blacklist Testleri", "Başarılı" if blacklist_result else "Başarısız"])

    return test_results
