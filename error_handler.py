from logB.logger import Logger
from utils.display import Display

# Logger ayarları
error_logger = Logger("logs/error.log")

def handle_exception(exception, context=""):
    """
    Hataları log dosyasına yaz ve kullanıcıya göster.
    :param exception: Yakalanan hata
    :param context: Hatanın oluştuğu bağlam
    """
    error_message = f"[{context}] Hata: {str(exception)}"
    error_logger.error(error_message)
    Display.print_error(error_message)  # Kullanıcıya hata mesajını göster
