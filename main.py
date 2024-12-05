from tests.test_network import test_internet_connection, test_dns_server
from tests.test_databases import test_mongodb_connection, test_sqlite_connection, test_postgresql_connection
from tests.test_rabbitmq import test_rabbitmq_connection
from tests.test_blacklist import test_blacklist_health
from display import Display

def main():
    """
    Tüm testleri çalıştırır ve sonuçları görüntüler.
    """
    Display.print_info("Sistem testleri başlatılıyor...")

    # Ağ testleri
    test_internet_connection()
    test_dns_server()

    # Veritabanı testleri
    test_mongodb_connection()
    test_sqlite_connection()
    test_postgresql_connection()

    # RabbitMQ testi
    test_rabbitmq_connection()

    # Kara liste testi
    test_blacklist_health()

    Display.print_success("Tüm sistem testleri tamamlandı.")

if __name__ == "__main__":
    main()