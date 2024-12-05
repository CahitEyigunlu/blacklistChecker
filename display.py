import os

class Display:
    """Ekran kontrolü ve renkli çıktı için yardımcı sınıf."""

    @staticmethod
    def clear_screen():
        """Ekranı temizler."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    @staticmethod
    def print_success(message: str):
        """Başarılı mesajları yeşil renkte yazdırır."""
        print(f"\033[92m✔️ Başarı: {message}\033[0m")

    @staticmethod
    def print_error(message: str):
        """Hata mesajlarını kırmızı renkte yazdırır."""
        print(f"\033[91m❌ Hata: {message}\033[0m")

    @staticmethod
    def print_info(message: str):
        """Bilgi mesajlarını mavi renkte yazdırır."""
        print(f"\033[94mℹ️ Bilgi: {message}\033[0m")

    @staticmethod
    def print_warning(message: str):
        """Uyarı mesajlarını sarı renkte yazdırır."""
        print(f"\033[93m⚠️ Uyarı: {message}\033[0m")

    @staticmethod
    def print_debug(message: str):
        """Debug mesajlarını gri renkte yazdırır."""
        print(f"\033[90m🐞 Debug: {message}\033[0m")
