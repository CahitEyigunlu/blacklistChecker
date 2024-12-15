import os
from rich import print
from rich.console import Console

console = Console()

class Display:
    """Ekran kontrolü ve renkli çıktı için yardımcı sınıf."""


    @staticmethod
    def get_theme():
        """Konsol temasını algılar (açık veya koyu)."""
        if os.name == 'nt':
            return "dark"
        try:
            if "dark" in os.environ.get('COLORTERM', '').lower():
                return "dark"
        except:
            pass
        return "light"

    @staticmethod
    def print_header():
        """ASCII art başlığını yazdırır."""
        os.system('cls' if os.name == 'nt' else 'clear')

        # SPDNet logosundaki renk paletine uygun renkler
        colors = [
            "red", "green", "yellow", "blue", "magenta", "cyan", "white"
        ]

        header = """
           SSSSSSSSSSSSSSS PPPPPPPPPPPPPPPPP   DDDDDDDDDDDDD        NNNNNNNN        NNNNNNNNEEEEEEEEEEEEEEEEEEEEEEETTTTTTTTTTTTTTTTTTTTTTT
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

        # Harf ve nokta renklendirme
        styled_header = ""
        color_index = 0
        for char in header:
            if char.isalnum():  # Harf veya rakam için renkli
                styled_header += f"[bold {colors[color_index]}]{char}[/]"
                color_index = (color_index + 1) % len(colors)
            elif char == ":":  # Nokta işaretini özel bir renk ile vurgula
                styled_header += "[bold magenta]:[/]"
            else:  # Diğer karakterler normal şekilde
                styled_header += char

        print(styled_header)
        print("\n\n")

    @staticmethod
    def print_section_header(title):
        console.rule(f"[bold blue]{title}[/]")

    @staticmethod
    def print_success(message: str):
        print(f"[bold green]✔️ Başarı: {message}[/]")

    @staticmethod
    def print_error(message: str):
        print(f"[bold red]❌ Hata: {message}[/]")

    @staticmethod
    def print_info(message: str):
        print(f"[bold blue]ℹ️ Bilgi: {message}[/]")

    @staticmethod
    def print_warning(message: str):
        print(f"[bold yellow]⚠️ Uyarı: {message}[/]")

    @staticmethod
    def print_debug(message: str):
        print(f"[bold grey]🐞 Debug: {message}[/]")

    @staticmethod
    def print_dns_status(worker_id, tasks_done, total_tasks, elapsed_time, remaining_time, ip, dns, result, status, details=None):
        """
        Özelleştirilmiş DNSBL durumu çıktısı.
        """
        status_emoji = {
            "completed": "✅",
            "dns_error": "❌",
            "timed_out": "⏳",
            "no_answer": "⚠️",
            "no_nameservers": "🚫",
            "not_listed": "✅",
            "blacklisted": "❌"
        }

        emoji = status_emoji.get(result, "ℹ️")
        details_text = f"({details})" if details else "(No details)"

        if status == "completed":
            if result == "listed":
                console.print(
                    f"{emoji} [bold yellow][Worker {worker_id}][/bold yellow] - "
                    f"[cyan][{tasks_done}/{total_tasks}][/cyan] - "
                    f"[blue][Elapsed: {elapsed_time}][/blue] - "
                    f"[magenta][Remaining: {remaining_time}][/magenta] - "
                    f"[bold white]{ip}[/bold white] is [bold red]listed[/bold red] in [bold cyan]{dns}[/bold cyan] "
                    f"{details_text}"
                )
            elif result == "not_listed":
                console.print(
                    f"{emoji} [bold green][Worker {worker_id}][/bold green] - "
                    f"[cyan][{tasks_done}/{total_tasks}][/cyan] - "
                    f"[blue][Elapsed: {elapsed_time}][/blue] - "
                    f"[magenta][Remaining: {remaining_time}][/magenta] - "
                    f"[bold white]{ip}[/bold white] is [bold green]not listed[/bold green] in [bold cyan]{dns}[/bold cyan] "
                    f"{details_text}"
                )
            else:
                console.print(
                    f"{emoji} [bold blue][Worker {worker_id}][/bold blue] - "
                    f"[cyan][{tasks_done}/{total_tasks}][/cyan] - "
                    f"[blue][Elapsed: {elapsed_time}][/blue] - "
                    f"[magenta][Remaining: {remaining_time}][/magenta] - "
                    f"[bold white]{ip}[/bold white] status: [bold blue]{result}[/bold blue] "
                    f"{details_text}"
                )
        else:
            console.print(
                f"{emoji} [bold red][Worker {worker_id}][/bold red] - "
                f"[cyan][{tasks_done}/{total_tasks}][/cyan] - "
                f"[blue][Elapsed: {elapsed_time}][/blue] - "
                f"[magenta][Remaining: {remaining_time}][/magenta] - "
                f"[bold white]{ip}[/bold white] encountered an [bold red]error[/bold red] "
                f"{details_text}"
            )
