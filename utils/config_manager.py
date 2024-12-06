import os

from dotenv import load_dotenv
import yaml

def load_config():
    """
    .env ve blacklist.yml dosyalarından yapılandırma ayarlarını yükler ve döndürür.
    """
    try:
        # .env dosyasını yükle
        load_dotenv()

        # blacklist.yml dosyasını oku
        with open("blacklist.yml", "r") as f:
            config = yaml.safe_load(f)

        # .env dosyasından okunan değerleri config'e ekle
        config['mongodb'] = {
            "url": os.getenv("MONGO_URL"),
            "db_name": os.getenv("MONGO_DB_NAME")
        }
        config['rabbitmq'] = {
            "host": os.getenv("RABBITMQ_HOST"),
            "port": int(os.getenv("RABBITMQ_PORT", 5672)),
            "username": os.getenv("RABBITMQ_USERNAME"),
            "password": os.getenv("RABBITMQ_PASSWORD"),
            "erlang_cookie": os.getenv("RABBITMQ_ERLANG_COOKIE"),
            "web_ui_port": int(os.getenv("RABBITMQ_WEB_UI_PORT", 8003)),
            "amqp_port": int(os.getenv("RABBITMQ_AMQP_PORT", 5672))
        }
        config['postgresql'] = {
            "postgres_user": os.getenv("POSTGRES_USERNAME"),
            "postgres_password": os.getenv("POSTGRES_PASSWORD"),
            "postgres_db": os.getenv("POSTGRES_DB"),
            "postgres_host": os.getenv("POSTGRES_HOST"),
            "postgres_port": int(os.getenv("POSTGRES_PORT", 5432))
        }

        return config

    except FileNotFoundError:
        print("Hata: blacklist.yml dosyası bulunamadı.")
        return None
    except Exception as e:
        print(f"Hata: Yapılandırma dosyası yüklenirken bir hata oluştu: {e}")
        return None