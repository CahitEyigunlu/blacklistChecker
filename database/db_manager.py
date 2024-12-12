import signal
from datetime import date
import sqlite3
from database.sqlite import Database
from database.postgre import PostgreSQL
from database.rabbitMQ import RabbitMQ
from database.mongoDB import MongoDB
from logB.logger import Logger
from database.task_manager import TaskManager
from utils.display import Display


class DBManager:
    """
    Manages database connections and performs application startup logic.
    """

    def __init__(self, config):
        """
        Initializes DBManager with configuration and establishes connections to required databases.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.display = Display()  # Display örneği oluştur
        self.active_connections = {}
        self.today = date.today().strftime("%Y-%m-%d")

        try:
            self.connect_to_databases()
        except Exception as e:
            self.logger.error(f"Error initializing DBManager: {e}", extra={"function": "__init__", "file": "db_manager.py"})
            self.display.print_error(f"❌ Error initializing DBManager: {e}")
            raise  # Hata mesajından sonra hatayı tekrar yükselt

        # SIGINT handling for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)

    def connect_to_databases(self):
        """
        Connects to databases based on the configuration.
        """

        # SQLite için TaskManager kullanılıyor
        try:
            sqlite_connection = sqlite3.connect(self.config["sqlite"]["db_path"])
            self.sqlite_db = TaskManager(sqlite_connection, self.config)  # config parametresini ekle
            self.sqlite_db.initialize()
            self.active_connections["SQLite"] = self.sqlite_db
            self.logger.info("Connected to SQLite database.")
            self.display.print_success("✔️ Connected to SQLite database.")  # display.print_success kullan

        except Exception as e:
            self.logger.error(f"Error connecting to SQLite: {e}", extra={"function": "connect_to_databases", "file": "db_manager.py"})
            self.display.print_error(f"❌ Error connecting to SQLite: {e}")
            raise  # Hata mesajından sonra hatayı tekrar yükselt

        # RabbitMQ
        try:
            self.rabbitmq = RabbitMQ(self.config)  # config parametresini ekle
            self.rabbitmq.connect()
            self.active_connections["RabbitMQ"] = self.rabbitmq
            self.logger.info("Connected to RabbitMQ server.")
            self.display.print_success("✔️ Connected to RabbitMQ server.")  # display.print_success kullan
        except Exception as e:
            self.logger.error(f"Error connecting to RabbitMQ: {e}", extra={"function": "connect_to_databases", "file": "db_manager.py"})
            self.display.print_error(f"❌ Error connecting to RabbitMQ: {e}")
            raise  # Hata mesajından sonra hatayı tekrar yükselt

        # Optional databases
        db_config = self.config.get("database", {}).get("recorded_dbs", {})

        # PostgreSQL
        if db_config.get("postgresql", False):
            try:
                self.postgresql = PostgreSQL(self.config)  # config parametresini ekle
                self.postgresql.connect()
                self.active_connections["PostgreSQL"] = self.postgresql
                self.logger.info("Connected to PostgreSQL database.")
                self.display.print_success("✔️ Connected to PostgreSQL database.")  # display.print_success kullan
            except Exception as e:
                self.logger.error(f"Error connecting to PostgreSQL: {e}", extra={"function": "connect_to_databases", "file": "db_manager.py"})
                self.display.print_error(f"❌ Error connecting to PostgreSQL: {e}")
                raise  # Hata mesajından sonra hatayı tekrar yükselt

        # MongoDB
        if db_config.get("mongodb", False):
            try:
                self.mongodb = MongoDB(self.config)  # config parametresini ekle
                self.mongodb.connect()  # db_name config dosyasından alınıyor
                self.active_connections["MongoDB"] = self.mongodb
                self.logger.info("Connected to MongoDB database.")
                self.display.print_success("✔️ Connected to MongoDB database.")  # display.print_success kullan
            except Exception as e:
                self.logger.error(f"Error connecting to MongoDB: {e}", extra={"function": "connect_to_databases", "file": "db_manager.py"})
                self.display.print_error(f"❌ Error connecting to MongoDB: {e}")
                raise  # Hata mesajından sonra hatayı tekrar yükselt

    def manage_tasks(self):
        """
        Manages the tasks based on today's records.
        """
        try:
            pending_tasks = self.sqlite_db.fetch_tasks_by_date(self.today)  # fetch_tasks_by_date kullan
            if not pending_tasks:
                self.display.print_info("🚀 No tasks found for today. Initializing tasks.")  # display.print_info kullan
                self.rabbitmq.create_task_queue()
                tasks = self.sqlite_db.initialize_tasks(self.today)
                for task in tasks:
                    self.rabbitmq.publish_task(task)
                self.display.print_success(f"✔️ Total new tasks initialized: {len(tasks)}")  # display.print_success kullan
            else:
                self.display.print_info(f"🔄 Pending tasks for today: {len(pending_tasks)}")  # display.print_info kullan
                for task in pending_tasks:
                    self.rabbitmq.publish_task(task)
        except Exception as e:
            self.logger.error(f"Error managing tasks: {e}", extra={"function": "manage_tasks", "file": "db_manager.py"})
            self.display.print_error(f"❌ Error managing tasks: {e}")
            raise  # Hata mesajından sonra hatayı tekrar yükselt

    def signal_handler(self, sig, frame):
        """
        Handles SIGINT (CTRL+C) signal to close connections gracefully.
        """
        self.display.print_warning("\n🔴 CTRL+C detected! Closing all connections...")  # display.print_warning kullan
        self.close_connections()
        exit(0)

    def close_connections(self):
        """
        Closes all active database connections.
        """
        for db_name, connection in self.active_connections.items():
            try:
                connection.close_connection()
                self.logger.info(f"Closed connection to {db_name}.")
                self.display.print_success(f"🔒 Closed connection to {db_name}.")  # display.print_success kullan
            except Exception as e:
                self.logger.error(f"Error closing connection to {db_name}: {e}", extra={"function": "close_connections", "file": "db_manager.py", "db_name": db_name})
                self.display.print_error(f"❌ Error closing connection to {db_name}: {e}")
                raise  # Hata mesajından sonra hatayı tekrar yükselt

    def start(self):
        """
        Starts the application logic.
        """
        self.logger.info("Starting application...")
        self.display.print_info("🚀 Application is running. Press CTRL+C to exit.")  # display.print_info kullan
        self.manage_tasks()