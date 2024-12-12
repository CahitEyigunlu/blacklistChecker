import os
import logging
from logging.handlers import RotatingFileHandler
from logB.log_formatter import format_log
from logB.log_security import encrypt_data, mask_data
from logB.log_levels import DEBUG, INFO, WARNING, ERROR, CRITICAL


class Logger:
    def __init__(self, log_file_path, level=DEBUG, max_bytes=10 * 1024 * 1024, backup_count=5):
        self.log_file_path = log_file_path
        self.level = level  # Varsayılan seviye DEBUG

        # Log seviyesini ayarlıyoruz
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.level)

        # RotatingFileHandler ile dosya yönetimi
        handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=max_bytes,  # Maksimum boyut (10 MB)
            backupCount=backup_count  # Yedek dosya sayısı
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def set_level(self, level):
        """
        Log seviyesini ayarlar.
        Seviyeler: DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        level_dict = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        if level in level_dict:
            self.level = level_dict[level]
            self.logger.setLevel(self.level)
            print(f"Log level set to: {level}")
        else:
            print(f"Invalid log level: {level}")

    def log(self, level, message, details=None, encrypt=False, extra=None):
        """
        Loglama fonksiyonu.
        """
        log_entry = format_log(level, message, details, extra=extra)

        if encrypt:
            log_entry = encrypt_data(log_entry)

        if extra is None:
            extra = {}

        if self._should_log(level):
            self.logger.log(self._get_numeric_level(level), log_entry, extra=extra)

    def _should_log(self, level):
        """
        Bu fonksiyon, verilen log seviyesinin mevcut log seviyesinden daha yüksek olup olmadığını kontrol eder.
        """
        level_priority = {
            'DEBUG': 10,
            'INFO': 20,
            'WARNING': 30,
            'ERROR': 40,
            'CRITICAL': 50
        }

        return level_priority[level] >= level_priority[self._get_level_name(self.level)]

    def _get_level_name(self, level):
        """
        Sayısal seviyeyi, log seviyesinin ismine çevirir.
        """
        level_dict = {
            logging.DEBUG: 'DEBUG',
            logging.INFO: 'INFO',
            logging.WARNING: 'WARNING',
            logging.ERROR: 'ERROR',
            logging.CRITICAL: 'CRITICAL'
        }
        return level_dict.get(level, 'DEBUG')

    def _get_numeric_level(self, level_name):
        """
        İsim seviyesini sayısal seviyeye çevirir.
        """
        level_dict = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_dict.get(level_name, logging.DEBUG)

    def debug(self, message, details=None, encrypt=False, extra=None):
        self.log("DEBUG", message, details, encrypt, extra)

    def info(self, message, details=None, encrypt=False, extra=None):
        self.log("INFO", message, details, encrypt, extra)

    def warning(self, message, details=None, encrypt=False, extra=None):
        self.log("WARNING", message, details, encrypt, extra)

    def error(self, message, details=None, encrypt=False, extra=None):
        self.log("ERROR", message, details, encrypt, extra)

    def critical(self, message, details=None, encrypt=False, extra=None):
        self.log("CRITICAL", message, details, encrypt, extra)

    # Proxy metodlar ekleyerek diğer modüllerin doğrudan kullanmasını sağlıyoruz
    def get_logger(self):
        return self.logger

    def close_handlers(self):
        """
        Açık olan tüm handler'ları kapatır.
        """
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()


# Logger nesnesi oluşturuluyor
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger_instance = Logger(os.path.join(base_dir, 'logs', 'app_logs.json'))

def setup_logger():
    """Logger nesnesini döndüren yapılandırma fonksiyonu."""
    return logger_instance.get_logger()
