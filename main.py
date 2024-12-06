import os
import signal
import time

from tests.test_blacklist import BlacklistTests
from tests.test_databases import DatabaseTests
from tests.test_network import NetworkTests
from tests.test_rabbitmq import RabbitMQTests
from utils.display import Display, console


def signal_handler(sig, frame):
    """CTRL+C sinyali için işleyici."""
    print("Çıkış yapılıyor...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main():
    """
    Testleri çalıştırır.
    """
    display = Display()  # Display sınıfını başlat
    display.print_header()  # Başlığı yazdır
    display.print_header()  # Başlığı ilk olarak göster
    time.sleep(2)  # Logoyu 2 saniye göster
    display.print_header()  # Başlığı yazdır
    display.print_section_header("Sistem Testleri") 

    network_tests = NetworkTests()
    display.print_section_header("Network Testleri") 
    network_tests.run()
    database_tests = DatabaseTests()
    display.print_section_header("Database Testleri")
    database_tests.run()
    rabbitmq_tests = RabbitMQTests()
    display.print_section_header("RabbitMQ Testleri") 
    rabbitmq_tests.run()
    blacklist_tests = BlacklistTests()
    display.print_section_header("Blacklist Testleri")
    blacklist_tests.run()

    display.print_success("Tüm sistem testleri tamamlandı.")

    display.print_info("Çıkmak için CTRL+C tuşlarına basın...")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()