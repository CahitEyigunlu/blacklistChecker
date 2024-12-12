import os
from dotenv import load_dotenv
import yaml
from logB.logger import Logger
from utils.display import Display

def load_config():
    """
    .env ve blacklist.yml dosyalarından yapılandırma ayarlarını yükler ve döndürür.
    """
    # Logger initialization with dynamic paths from .env
    app_log_path = os.getenv("APP_LOG_PATH", "logs/application.log")
    error_log_path = os.getenv("ERROR_LOG_PATH", "logs/error.log")
    logger = Logger(log_file_path=app_log_path)
    error_logger = Logger(log_file_path=error_log_path)
    display = Display()

    try:
        # .env dosyasını yükle
        load_dotenv()
        logger.info(".env file loaded successfully.")

        # blacklist.yml dosyasını oku
        try:
            with open("blacklist.yml", "r") as f:
                config = yaml.safe_load(f)
            logger.info("blacklist.yml loaded successfully.")
        except FileNotFoundError:
            error_message = "blacklist.yml file not found."
            error_logger.error(error_message, extra={"function": "load_config", "file": "config_manager.py"})
            display.print_error(f"❌ {error_message}")
            return None

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
            "amqp_port": int(os.getenv("RABBITMQ_AMQP_PORT", 5672)),
            "default_queue": os.getenv("RABBITMQ_DEFAULT_QUEUE", "default_queue"),
            "concurrency_limit": int(os.getenv("RABBITMQ_CONCURRENCY_LIMIT", 5))
        }
        config['postgresql'] = {
            "postgres_user": os.getenv("POSTGRES_USERNAME"),
            "postgres_password": os.getenv("POSTGRES_PASSWORD"),
            "postgres_db": os.getenv("POSTGRES_DB"),
            "postgres_host": os.getenv("POSTGRES_HOST"),
            "postgres_port": int(os.getenv("POSTGRES_PORT", 5432))
        }
        config['logging'] = {
            "app_log_path": app_log_path,
            "error_log_path": error_log_path
        }

        logger.info("Configuration loaded successfully.")
        display.print_success("✔️ Configuration loaded successfully.")

        return config

    except Exception as e:
        error_message = f"An error occurred while loading the configuration: {e}"
        error_logger.error(error_message, extra={"function": "load_config", "file": "config_manager.py"})
        display.print_error(f"❌ {error_message}")
        return None