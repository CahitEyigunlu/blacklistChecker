import os
import yaml
from display import Display
from logger.logger import Logger

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

from dotenv import load_dotenv
load_dotenv()

def get_config():
  """
  Yapılandırma ayarlarını döndürür.
  """

  config = {
      "mongodb": {
          "url": os.getenv("MONGO_URL"),
          "db_name": os.getenv("MONGO_DB_NAME")
      },
      "rabbitmq": {
          "host": os.getenv("RABBITMQ_HOST"),
          "port": int(os.getenv("RABBITMQ_PORT", 5672)),  # Varsayılan port 5672
          "username": os.getenv("RABBITMQ_USERNAME"),
          "password": os.getenv("RABBITMQ_PASSWORD"),
          "erlang_cookie": os.getenv("RABBITMQ_ERLANG_COOKIE"),
          "web_ui_port": int(os.getenv("RABBITMQ_WEB_UI_PORT", 8003)),  # Varsayılan port 8003
          "amqp_port": int(os.getenv("RABBITMQ_AMQP_PORT", 5672))  # Varsayılan port 5672
      },
      "postgresql": {
          "username": os.getenv("POSTGRES_USERNAME"),
          "password": os.getenv("POSTGRES_PASSWORD"),
          "db": os.getenv("POSTGRES_DB"),
          "host": os.getenv("POSTGRES_HOST"),
          "port": int(os.getenv("POSTGRES_PORT", 5432))  # Varsayılan port 5432
      }
  }

  return config