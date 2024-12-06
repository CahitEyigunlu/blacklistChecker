import time
import curses
import signal
from tests.test_network import test_internet_connection, test_dns_server
from tests.test_databases import (test_mongodb_connection,test_postgresql_connection,test_sqlite_connection)
from tests.test_rabbitmq import test_rabbitmq_connection
from tests.test_blacklist import test_blacklist_health
from utils.display import Display

def signal_handler(sig, frame):
    """CTRL+C sinyali için işleyici."""
    curses.endwin()  # Curses'i sonlandır
    print("Çıkış yapılıyor...")
    exit(0)
signal.signal(signal.SIGINT, signal_handler)

def main(stdscr):
    """
    Testleri çalıştırır ve çıktıyı curses ile konsolda gösterir.
    """
    display = Display(stdscr)
    display.stdscr.clear()
    display.print_header()  # Başlığı ilk olarak göster
    stdscr.refresh()
    time.sleep(2)  # Logoyu 2 saniye göster

    # Ağ testleri
    display.print_info("Sistem testleri başlatılıyor...")
    test_internet_connection(display)
    test_dns_server(display)

    # Veritabanı testleri
    test_mongodb_connection(display)
    test_sqlite_connection(display)
    test_postgresql_connection(display)

    # RabbitMQ testi
    test_rabbitmq_connection(display)

    # Kara liste testi
    test_blacklist_health(display)

    display.print_success("Tüm sistem testleri tamamlandı.")

    display.print_info("Çıkmak için CTRL+C tuşlarına basın...")
    while True:
        try:
            stdscr.getch()  # Bir tuşa basılmasını bekle
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    curses.wrapper(main)