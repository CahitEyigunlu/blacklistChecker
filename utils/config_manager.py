import os
from dotenv import load_dotenv
import yaml

def load_config():
    """
    Yapılandırma ayarlarını yükler ve döndürür.
    """
    try:
        # .env dosyasını yükle
        load_dotenv()

        # config.yml dosyasını oku
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)

        # Ortam değişkenlerini config'e ekle
        config['mongodb']['url'] = os.getenv("MONGO_URL")
        config['mongodb']['db_name'] = os.getenv("MONGO_DB_NAME")
        config['rabbitmq']['host'] = os.getenv("RABBITMQ_HOST")
        config['rabbitmq']['port'] = int(os.getenv("RABBITMQ_PORT", 5672))
        config['rabbitmq']['username'] = os.getenv("RABBITMQ_USERNAME")
        config['rabbitmq']['password'] = os.getenv("RABBITMQ_PASSWORD")
        config['rabbitmq']['erlang_cookie'] = os.getenv("RABBITMQ_ERLANG_COOKIE")
        config['rabbitmq']['web_ui_port'] = int(os.getenv("RABBITMQ_WEB_UI_PORT", 15672))
        config['rabbitmq']['amqp_port'] = int(os.getenv("RABBITMQ_AMQP_PORT", 5672))
        config['postgresql']['postgres_user'] = os.getenv("POSTGRES_USERNAME")
        config['postgresql']['postgres_password'] = os.getenv("POSTGRES_PASSWORD")
        config['postgresql']['postgres_db'] = os.getenv("POSTGRES_DB")
        config['postgresql']['postgres_host'] = os.getenv("POSTGRES_HOST")
        config['postgresql']['postgres_port'] = int(os.getenv("POSTGRES_PORT", 5432))

        return config

    except FileNotFoundError:
        print("Hata: config.yml dosyası bulunamadı.")
        return None
    except Exception as e:
        print(f"Hata: Yapılandırma dosyası yüklenirken bir hata oluştu: {e}")
        return None