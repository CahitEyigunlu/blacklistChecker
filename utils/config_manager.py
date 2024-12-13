import os
from dotenv import load_dotenv
import yaml
from logB.logger import Logger
from utils.display import Display

def load_secret(file_path, fallback=None):
    """
    Reads a secret value from a file. If the file doesn't exist or path is None, returns the fallback value.
    """
    if not file_path:
        return fallback  # Eğer dosya yolu None veya boşsa, fallback değeri döndür
    try:
        with open(file_path, 'r') as secret_file:
            return secret_file.read().strip()
    except FileNotFoundError:
        return fallback

def load_config():
    """
    Loads configuration settings based on the environment.
    """
    # Logger initialization
    app_log_path = os.getenv("APP_LOG_PATH", "logs/application.log")
    error_log_path = os.getenv("ERROR_LOG_PATH", "logs/error.log")
    logger = Logger(log_file_path=app_log_path)
    error_logger = Logger(log_file_path=error_log_path)
    display = Display()

    try:
        # Detect environment
        run_env = os.getenv("RUN_ENV", "local")  # Default to "local"
        display.print_info(f"ℹ️ Current environment: {run_env}")

        # Load appropriate env file
        if run_env == "local":
            load_dotenv(".env")
            logger.info(".env file loaded successfully.")
            display.print_success("✔️ Loaded environment variables from .env")
        else:
            load_dotenv("config.env")
            logger.info("config.env file loaded successfully.")
            display.print_success("✔️ Loaded environment variables from config.env")

        # Load blacklist.yml
        try:
            with open("blacklist.yml", "r") as f:
                config = yaml.safe_load(f)
            logger.info("blacklist.yml loaded successfully.")
        except FileNotFoundError:
            error_message = "blacklist.yml file not found."
            error_logger.error(error_message, extra={"function": "load_config", "file": "config_manager.py"})
            display.print_error(f"❌ {error_message}")
            return None

        # Load MongoDB settings
        config['mongodb'] = {
            "url": os.getenv("MONGO_URL"),
            "db_name": os.getenv("MONGO_DB_NAME")
        }

        # Load RabbitMQ settings
        config['rabbitmq'] = {
            "host": os.getenv("RABBITMQ_HOST"),
            "port": int(os.getenv("RABBITMQ_PORT", 5672)),
            "username": os.getenv("RABBITMQ_USERNAME"),
            "password": os.getenv("RABBITMQ_PASSWORD", load_secret(os.getenv("RABBITMQ_PASSWORD_FILE"))),
            "erlang_cookie": os.getenv("RABBITMQ_ERLANG_COOKIE", load_secret(os.getenv("RABBITMQ_ERLANG_COOKIE_FILE"))),
            "web_ui_port": int(os.getenv("RABBITMQ_WEB_UI_PORT", 8003)),
            "amqp_port": int(os.getenv("RABBITMQ_AMQP_PORT", 5672)),
            "default_queue": os.getenv("RABBITMQ_DEFAULT_QUEUE", "default_queue"),
            "concurrency_limit": int(os.getenv("RABBITMQ_CONCURRENCY_LIMIT", 5))
        }

        # Load PostgreSQL settings
        config['postgresql'] = {
            "postgres_user": os.getenv("POSTGRES_USERNAME"),
            "postgres_password": os.getenv("POSTGRES_PASSWORD", load_secret(os.getenv("POSTGRES_PASSWORD_FILE"))),
            "postgres_db": os.getenv("POSTGRES_DB"),
            "postgres_host": os.getenv("POSTGRES_HOST"),
            "postgres_port": int(os.getenv("POSTGRES_PORT", 5432))
        }

        # Logging paths
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
