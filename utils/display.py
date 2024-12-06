import curses
import os
import time

from tests.test_network import test_internet_connection, test_dns_server
from tests.test_databases import (test_mongodb_connection,
                                   test_postgresql_connection,
                                   test_sqlite_connection)
from tests.test_rabbitmq import test_rabbitmq_connection
from tests.test_blacklist import test_blacklist_health


class Display:
    """Curses ile ekran kontrolü ve renkli çıktı için yardımcı sınıf."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.start_color()
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i  + 1, i, -1)
        self.theme = self.get_theme()

    def get_theme(self):
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

    def get_color(self, message_type):
        """Mesaj türüne ve temaya göre uygun rengi seçer."""
        colors = {
            "success": curses.COLOR_GREEN if self.theme == "dark" else curses.COLOR_BLACK,
            "error": curses.COLOR_RED,
            "info": curses.COLOR_CYAN if self.theme == "dark" else curses.COLOR_BLUE,
            "warning": curses.COLOR_YELLOW,
            "debug": curses.COLOR_BLACK
        }
        return colors.get(message_type, curses.COLOR_WHITE)

    def print_header(self):
        """ASCII art başlığını yazdırır."""
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
 SSSSSSSSSSSSSSS   PPPPPPPPPP          DDDDDDDDDDDDD        NNNNNNNN         NNNNNNNEEEEEEEEEEEEEEEEEEEEEE      TTTTTTTTTTT      
                                                                                                                                 
                                                                                                                                 
                                                                                                                                 
"""
        self.stdscr.addstr(0, 0, header)

    def print_message(self, message: str, message_type: str = "info"):
        """Mesajı uygun renkte yazdırır."""
        color = self.get_color(message_type)
        self.stdscr.addstr(message + "\n", curses.color_pair(color + 1))
        self.stdscr.refresh()

    def print_success(self, message: str):
        """Başarılı mesajları yeşil renkte yazdırır."""
        self.print_message(f"✔️ Başarı: {message}", "success")

    def print_error(self, message: str):
        """Hata mesajlarını kırmızı renkte yazdırır."""
        self.print_message(f"❌ Hata: {message}", "error")

    def print_info(self, message: str):
        """Bilgi mesajlarını mavi renkte yazdırır."""
        self.print_message(f"ℹ️ Bilgi: {message}", "info")

    def print_warning(self, message: str):
        """Uyarı mesajlarını sarı renkte yazdırır."""
        self.print_message(f"⚠️ Uyarı: {message}", "warning")

    def print_debug(self, message: str):
        """Debug mesajlarını gri renkte yazdırır."""
        self.print_message(f"🐞 Debug: {message}", "debug")