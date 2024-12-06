from datetime import date

from database.sqlite import Database
from postgre import PostgreSQL
from rabbitmq import RabbitMQ
from utils import display
from logger import logger


class DBManager:
    """
    Manages database operations and application startup logic.
    """

    def __init__(self, config, sqlite_db, rabbitmq, postgresql):
        """
        Initializes DBManager with configuration and database connections.

        Args:
            config: Application configuration.
            sqlite_db: SQLite database connection.
            rabbitmq: RabbitMQ connection.
            postgresql: PostgreSQL connection.
        """
        self.config = config
        self.sqlite_db = sqlite_db
        self.rabbitmq = rabbitmq
        self.postgresql = postgresql

    def start(self):
        """
        Performs application startup tasks.
        """
        logger.info("Starting application...")

        # A. Get current date
        today = date.today()

        # Clear RabbitMQ queue
        self.rabbitmq.create_queue('task_queue')  # Create queue if it doesn't exist
        self.rabbitmq.purge_queue('task_queue')  # Purge the queue
        logger.info("RabbitMQ queue cleared.")

        # B. Check for pending tasks in SQLite
        pending_ips = self.sqlite_db.get_unchecked_ips()

        if pending_ips:
            # B.1 Pending tasks found
            logger.info(f"Found {len(pending_ips)} pending tasks.")

            # Check if the date is the same (check_date in SQLite vs today's date)
            last_check_date = self.sqlite_db.get_last_check_date()
            if last_check_date == today:
                # Continue with pending tasks
                for ip in pending_ips:
                    self.rabbitmq.publish_message('task_queue', {'ip': ip})
                logger.info("Pending tasks added to RabbitMQ queue.")
            else:
                # Clear pending tasks and RabbitMQ queue
                self.sqlite_db.clear_pending_tasks()
                logger.info("Pending tasks cleared from SQLite and RabbitMQ queue.")

        else:
            # B.2 No pending tasks
            logger.info("No pending tasks found.")

            # Check if already run today in PostgreSQL
            if self._already_run_today():
                display.print_colored("Application already run today. Exiting...", "yellow")
                logger.warning("Application already run today. Exiting...")
                return False

        # C. Prepare tasks
        tasks = self._prepare_tasks()

        # Add tasks to SQLite and RabbitMQ
        for task in tasks:
            self.sqlite_db.add_ip_address(task['ip'])
            self.rabbitmq.publish_message('task_queue', task)
        logger.info("Tasks added to SQLite and RabbitMQ.")

        return True

    def _already_run_today(self):
        """
        Checks if the application has already run today in PostgreSQL.
        """
        try:
            query = "SELECT COUNT(*) FROM ip_check WHERE check_date = %s"
            params = (date.today(),)
            result = self.postgresql.fetch_data(query, params)
            count = result[0][0]
            return count > 0
        except Exception as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise

    def _prepare_tasks(self):
        """
        Converts /24 CIDR IP list to /32 and creates combinations with blacklists.
        """
        # ... (Read CIDR list and convert to /32) ...
        # ... (Create combinations with blacklists) ...
        # ... (Return tasks as a list) ...
        pass  # Fill this part with your own logic