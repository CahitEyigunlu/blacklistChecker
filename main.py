import os
import signal
import sys
from utils import runner
from controller import Controller
from display import Display
from distrubutor import TaskDistributer
from config_manager import load_config
from concurrent.futures import as_completed

def handle_exit(signal_received, frame):
    # Çıkış sinyali alındığında çalışacak fonksiyon
    Display.print_warning("Çıkış yapılıyor, lütfen bekleyin...")
    sys.exit(0)

def main():
    try:
        # SIGINT (Ctrl+C) sinyalini yakala
        signal.signal(signal.SIGINT, handle_exit)

        # Main.py dizinini referans al
        base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(base_dir)  # Çalışma dizinini main.py'nin dizinine ayarla

        Display.clear_screen()  # Ekranı temizle
        runner()  # Tüm görevleri çalıştır
        Display.print_info("İş akışı için görevleri kontrol ediyorum...")
        
        # Controller başlat ve görevleri kontrol et
        controller = Controller()
        controller.execute()

        # Config yükle ve TaskDistributer'ı başlat
        config = load_config()
        rabbitmq_config = config.get('rabbitmq', {})
        task_distributer = TaskDistributer(rabbitmq_config)
        task_distributer.run()
        
    except Exception as e:
        Display.print_error(f"Beklenmeyen bir hata oluştu: {str(e)}")

if __name__ == "__main__":
    main()
