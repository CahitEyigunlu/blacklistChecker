import signal
from datetime import date
import sqlite3
from database.sqlite import Database
from database.postgre import PostgreSQL
from database.rabbitMQ import RabbitMQ
from database.mongoDB import MongoDB
from logB.logger import Logger
from database.task_manager import TaskManager


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
        self.logger = Logger(log_file_path="logs/db_manager.log")  # Logger instance
        self.active_connections = {}  # Stores active connections
        self.today = date.today().strftime("%Y-%m-%d")  # Today's date

        # Connect to databases
        self.connect_to_databases()

        # SIGINT (CTRL+C) signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def connect_to_databases(self):
        """
        Connects to databases based on the configuration.
        """
        # SQLite için TaskManager kullanılıyor
        sqlite_connection = sqlite3.connect(self.config["sqlite"]["db_path"])
        self.sqlite_db = TaskManager(sqlite_connection)
        self.sqlite_db.initialize()  # Eğer tablo yoksa oluşturacak
        self.active_connections["SQLite"] = self.sqlite_db
        self.logger.info("Connected to SQLite database.")
        print("✔️ Connected to SQLite database.")

        # RabbitMQ
        self.rabbitmq = RabbitMQ(
            host=self.config["rabbitmq"]["host"],
            username=self.config["rabbitmq"]["username"],
            password=self.config["rabbitmq"]["password"]
        )
        self.rabbitmq.connect()
        self.active_connections["RabbitMQ"] = self.rabbitmq
        self.logger.info("Connected to RabbitMQ server.")
        print("✔️ Connected to RabbitMQ server.")

        # Optional databases
        db_config = self.config.get("database", {}).get("recorded_dbs", {})

        # PostgreSQL
        if db_config.get("postgresql", False):
            self.postgresql = PostgreSQL(
                host=self.config["postgresql"]["postgres_host"],
                database=self.config["postgresql"]["postgres_db"],
                user=self.config["postgresql"]["postgres_user"],
                password=self.config["postgresql"]["postgres_password"]
            )
            self.postgresql.connect()
            self.active_connections["PostgreSQL"] = self.postgresql
            self.logger.info("Connected to PostgreSQL database.")
            print("✔️ Connected to PostgreSQL database.")

        # MongoDB
        if db_config.get("mongodb", False):
            self.mongodb = MongoDB(self.config["mongodb"]["url"])
            self.mongodb.connect(self.config["mongodb"]["db_name"])
            self.active_connections["MongoDB"] = self.mongodb
            self.logger.info("Connected to MongoDB database.")
            print("✔️ Connected to MongoDB database.")

    def manage_tasks(self):
        """
        Manages the tasks based on today's records.
        """
        pending_tasks = self.sqlite_db.get_pending_tasks(self.today)
        if not pending_tasks:
            print("🚀 No tasks found for today. Initializing tasks.")
            self.rabbitmq.create_task_queue()  # Ensure RabbitMQ queue exists
            tasks = self.sqlite_db.initialize_tasks(self.today)  # Initialize new tasks in SQLite
            for task in tasks:
                self.rabbitmq.publish_task(task)  # Publish each task to RabbitMQ
            print(f"✔️ Total new tasks initialized: {len(tasks)}")
        else:
            print(f"🔄 Pending tasks for today: {len(pending_tasks)}")
            for task in pending_tasks:
                self.rabbitmq.publish_task(task)  # Republish pending tasks

    def signal_handler(self, sig, frame):
        """
        Handles SIGINT (CTRL+C) signal to close connections gracefully.
        """
        print("\n🔴 CTRL+C detected! Closing all connections...")
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
                print(f"🔒 Closed connection to {db_name}.")
            except Exception as e:
                self.logger.error(f"Error closing connection to {db_name}: {e}")
                print(f"❌ Error closing connection to {db_name}: {e}")

    def start(self):
        """
        Starts the application logic.
        """
        self.logger.info("Starting application...")
        print("🚀 Application is running. Press CTRL+C to exit.")
        self.manage_tasks()
