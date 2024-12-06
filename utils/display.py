import os

from rich import print
from rich.console import Console

console = Console()


class Display:
    """Ekran kontrolü ve renkli çıktı için yardımcı sınıf."""

    @staticmethod
    def get_theme():
        """Konsol temasını algılar (açık veya koyu)."""
        # Windows için özel çözüm (varsayılan olarak koyu tema)
        if os.name == 'nt':
            return "dark"
        # Diğer işletim sistemleri için terminal değişkenlerini kontrol et
        try:
            # Xterm uyumlu terminaller için
            if "dark" in os.environ.get('COLORTERM', '').lower():
                return "dark"
        except:
            pass
        return "light"

    @staticmethod
    def get_color(message_type):
        """Mesaj türüne ve temaya göre uygun rengi seçer."""
        theme = Display.get_theme()
        colors = {
            "success": "green" ,
            "error": "red",
            "info": "cyan" if theme == "dark" else "blue",  # Koyu temada daha görünür renk
            "warning": "yellow",
            "debug": "grey"
        }
        return colors.get(message_type, "white")  # Varsayılan renk beyaz

    @staticmethod
    def print_header():
        """ASCII art başlığını yazdırır."""

        # Ekranı temizle
        os.system('cls' if os.name == 'nt' else 'clear')

        header = """
                                                                                                            
                                                                                                            
           SSSSSSSSSSSSSSS PPPPPPPPPPPPPPPPP   DDDDDDDDDDDDD        NNNNNNNN        NNNNNNNNEEEEEEEEEEEEEEEEEEEEEETTTTTTTTTTTTTTTTTTTTTTT
          SS:::::::::::::::SP::::::::::::::::P  D::::::::::::DDD     N:::::::N       N::::::NE::::::::::::::::::::ET:::::::::::::::::::::T
         S:::::SSSSSS::::::SP::::::PPPPPP:::::P D:::::::::::::::DD   N::::::::N      N::::::NE::::::::::::::::::::ET:::::::::::::::::::::T
         S:::::S     SSSSSSSPP:::::P     P:::::PDDD:::::DDDDD:::::D  N:::::::::N     N::::::NEE::::::EEEEEEEEE::::ET:::::TT:::::::TT:::::T
         S:::::S              P::::P     P:::::P  D:::::D    D:::::D N::::::::::N    N::::::N  E:::::E       EEEEEETTTTTT  T:::::T  TTTTTT
         S:::::S              P::::P     P:::::P  D:::::D     D:::::DN:::::::::::N   N::::::N  E:::::E                     T:::::T        
          S::::SSSS           P::::PPPPPP:::::P   D:::::D     D:::::DN:::::::N::::N  N::::::N  E::::::EEEEEEEEEE           T:::::T        
           SS::::::SSSSS      P:::::::::::::PP    D:::::D     D:::::DN::::::N N::::N N::::::N  E:::::::::::::::E           T:::::T        
             SSS::::::::SS    P::::PPPPPPPPP      D:::::D     D:::::DN::::::N  N::::N:::::::N  E:::::::::::::::E           T:::::T        
                SSSSSS::::S   P::::P              D:::::D     D:::::DN::::::N   N:::::::::::N  E::::::EEEEEEEEEE           T:::::T        
                     S:::::S  P::::P              D:::::D     D:::::DN::::::N    N::::::::::N  E:::::E                     T:::::T        
                     S:::::S  P::::P              D:::::D    D:::::D N::::::N     N:::::::::N  E:::::E       EEEEEE        T:::::T        
         SSSSSSS     S:::::SPP::::::PP          DDD:::::DDDDD:::::D  N::::::N      N::::::::NEE::::::EEEEEEEE:::::E      TT:::::::TT      
         S::::::SSSSSS:::::SP::::::::P          D:::::::::::::::DD   N::::::N       N:::::::NE::::::::::::::::::::E      T:::::::::T      
         S:::::::::::::::SS P::::::::P          D::::::::::::DDD     N::::::N        N::::::NE::::::::::::::::::::E      T:::::::::T      
          SSSSSSSSSSSSSS   PPPPPPPPPP          DDDDDDDDDDDDD        NNNNNNNN         NNNNNNNEEEEEEEEEEEEEEEEEEEEEE      TTTTTTTTTTT      


        """
        print(header)  # Logoyu yazdır

        # Altına boşluk ekle
        print("\n\n")

    @staticmethod
    def print_section_header(title):
        """Belirtilen başlıkla bir bölüm başlığı yazdırır."""
        console.rule(f"[bold blue]{title}[/]")

    @staticmethod
    def print_success(message: str):
        """Başarılı mesajları yeşil renkte yazdırır."""
        color = Display.get_color("success")
        print(f"[bold {color}]✔️ Başarı: {message}[/]")

    @staticmethod
    def print_error(message: str):
        """Hata mesajlarını kırmızı renkte yazdırır."""
        color = Display.get_color("error")
        print(f"[bold {color}]❌ Hata: {message}[/]")

    @staticmethod
    def print_info(message: str):
        """Bilgi mesajlarını mavi renkte yazdırır."""
        color = Display.get_color("info")
        print(f"[bold {color}]ℹ️ Bilgi: {message}[/]")

    @staticmethod
    def print_warning(message: str):
        """Uyarı mesajlarını sarı renkte yazdırır."""
        color = Display.get_color("warning")
        print(f"[bold {color}]⚠️ Uyarı: {message}[/]")

    @staticmethod
    def print_debug(message: str):
        """Debug mesajlarını gri renkte yazdırır."""
        color = Display.get_color("debug")
        print(f"[bold {color}]🐞 Debug: {message}[/]")