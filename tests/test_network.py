import socket

from display import Display
from logger import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")

def test_internet_connection():
    """
    İnternet bağlantısını test eder.
    """
    try:
        Display.print_info("İnternet bağlantısı kontrol ediliyor...")
        socket.create_connection(("www.google.com", 80), timeout=5)
        info_logger.info("İnternet bağlantısı başarılı.")
        Display.print_success("İnternet bağlantısı başarılı.")
    except Exception as e:
        error_logger.error(f"İnternet bağlantısı başarısız: {str(e)}")
        Display.print_error("İnternet bağlantısı başarısız.")

def test_dns_server():
    """
    DNS sunucusunu test eder.
    """
    try:
        Display.print_info("DNS sunucusu kontrol ediliyor...")
        socket.gethostbyname("www.google.com")
        info_logger.info("DNS sunucusu başarılı bir şekilde çalışıyor.")
        Display.print_success("DNS sunucusu başarılı.")
    except Exception as e:
        error_logger.error(f"DNS sunucusu başarısız: {str(e)}")
        Display.print_error("DNS sunucusu başarısız.")