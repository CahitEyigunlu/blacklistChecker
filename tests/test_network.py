import socket

from utils.display import Display
from logB import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")

class NetworkTests:
    def __init__(self):
        pass

    def run(self):
        """
        İnternet bağlantısı ve DNS sunucusu testlerini çalıştırır ve sonucu döndürür.
        """
        internet_connection_result = self.test_internet_connection()
        dns_server_result = self.test_dns_server()
        return internet_connection_result and dns_server_result  # İki test de başarılıysa True döndür

    def test_internet_connection(self):
        """
        İnternet bağlantısını test eder ve sonucu döndürür.
        """
        try:
            Display.print_info("İnternet bağlantısı kontrol ediliyor...")
            socket.create_connection(("www.google.com", 80), timeout=5)
            info_logger.info("İnternet bağlantısı başarılı.")
            Display.print_success("İnternet bağlantısı başarılı.")
            return True  # Başarılı ise True döndür
        except Exception as e:
            error_logger.error(f"İnternet bağlantısı başarısız: {str(e)}")
            Display.print_error("İnternet bağlantısı başarısız.")
            return False  # Başarısız ise False döndür

    def test_dns_server(self):
        """
        DNS sunucusunu test eder ve sonucu döndürür.
        """
        try:
            Display.print_info("DNS sunucusu kontrol ediliyor...")
            socket.gethostbyname("www.google.com")
            info_logger.info("DNS sunucusu başarılı bir şekilde çalışıyor.")
            Display.print_success("DNS sunucusu başarılı.")
            return True  # Başarılı ise True döndür
        except Exception as e:
            error_logger.error(f"DNS sunucusu başarısız: {str(e)}")
            Display.print_error("DNS sunucusu başarısız.")
            return False  # Başarısız ise False döndür