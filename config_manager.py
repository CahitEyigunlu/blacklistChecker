import os
import yaml
from display import Display
from logging_module.logger import Logger

# Logger ayarları
config_logger = Logger("logs/config.log")

CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "blacklist.yml")

def load_config():
    """
    Config dosyasını yükler. Eğer dosya yoksa oluşturur.
    :return: Config verileri (dict)
    """
    try:
        # Config dizinini oluştur
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Eğer dosya yoksa varsayılan bir config oluştur
        if not os.path.exists(CONFIG_FILE):
            default_config = {'blacklist': ['mongo', 'postgresql', 'sqlite']}
            with open(CONFIG_FILE, 'w') as file:
                yaml.dump(default_config, file)
            config_logger.info("Config dosyası oluşturuldu.")
            Display.print_info("Config dosyası oluşturuldu.")

        # Config dosyasını oku
        with open(CONFIG_FILE, 'r') as file:
            config = yaml.safe_load(file)
            config_logger.info("Config dosyası başarıyla yüklendi.")
            return config

    except Exception as e:
        config_logger.error(f"Config yüklenirken hata oluştu: {str(e)}")
        Display.print_error(f"Config yüklenirken hata oluştu: {str(e)}")
        return None
