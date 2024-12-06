import os
import signal
import time
from rich.table import Table
from tests.tests import run_tests  
from utils.display import Display, console


def signal_handler(sig, frame):
    """CTRL+C sinyali için işleyici."""
    print("Çıkış yapılıyor...")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)


def main():
    """
    Testleri çalıştırır ve sonuçları bir tabloda gösterir.
    """
    display = Display()
    display.print_header()
    time.sleep(2)
    display.print_section_header("Sistem Testleri")

    # Testleri çalıştır ve sonuçları al
    test_results = run_tests()

    # Tabloyu oluştur
    table = Table(title="Test Sonuçları")
    table.add_column("Test Adı", justify="left", style="cyan", no_wrap=True)
    table.add_column("Sonuç", style="green")

    # Test sonuçlarını tabloya ekle
    for result in test_results:
        table.add_row(*result)

    # Tabloyu yazdır
    console.print(table)

    display.print_success("Tüm sistem testleri tamamlandı.")
    display.print_info("Çıkmak için CTRL+C tuşlarına basın...")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()