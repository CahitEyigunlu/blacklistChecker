# __init__.py
from .logger import Logger
from .log_levels import DEBUG, INFO, WARNING, ERROR, CRITICAL
from .log_formatter import format_log
from .log_rotator import manage_logs
from .access_control import check_access, log_access, request_access
from .log_security import mask_data, encrypt_data, decrypt_data

# Yeni fonksiyon: init_logging
def init_logging(log_file_path='app.log'):
    """
    Loglama modülünü başlatan fonksiyon. Tüm loglama yapılandırmalarını burada yapabilirsiniz.
    log_file_path: Logların kaydedileceği dosya yolu. Varsayılan: 'app.log'
    """
    print("Logging system initialized.")
    # Logger'ı doğru parametrelerle başlat
    logger = Logger(log_file_path=log_file_path)
    logger.set_level(INFO)  # Örneğin log seviyesini INFO yapma
    
__all__ = [
    "Logger",
    "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL",
    "format_log",
    "manage_logs",
    "check_access",
    "log_access",
    "request_access",
    "mask_data",
    "encrypt_data",
    "decrypt_data",
    "init_logging"  # init_logging fonksiyonunu da dışa aktarıyoruz
]
