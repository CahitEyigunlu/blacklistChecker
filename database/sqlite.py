import sqlite3
from utils.display import Display
from logB.logger import Logger


class Database:
    """
    Handles SQLite database operations.
    """

    def __init__(self, config):  # config parametresi eklendi
        """
        Initializes Database with the database path from the configuration.

        Args:
            config: Uygulama yapılandırması.
        """
        self.config = config  # config değişkeni eklendi
        self.db_path = config["sqlite"]["db_path"]  # db_path config'den alınıyor
        self.conn = None
        self.display = Display()
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])  # Logger nesnesi, config dosyasından log yolunu alıyor

    def connect(self):
        """
        Connects to the SQLite database.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.logger.info("Connected to SQLite database.")
            self.display.print_success("Connected to SQLite database.")
            return self.conn
        except sqlite3.Error as e:
            self.display.print_error(f"SQLite connection error: {e}")
            self.logger.error(f"SQLite connection error: {e}", extra={"function": "connect", "file": "sqlite.py"})  # extra bilgisi eklendi
            return None

    def create_table(self):
        """
        Creates the table to store IP addresses and check information.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_check (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    result TEXT,
                    check_date DATE,
                    last_checked DATETIME)
            ''')
            self.conn.commit()
            self.logger.info("Table created successfully.")
            self.display.print_success("Table created successfully.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error creating table: {e}")
            self.logger.error(f"Error creating table: {e}", extra={"function": "create_table", "file": "sqlite.py"})  # extra bilgisi eklendi

    def add_ip_address(self, ip_address):
        """
        Adds a new IP address.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO ip_check (ip_address, status, check_date, last_checked) VALUES (?, ?, DATE('now'), DATETIME('now'))",
                (ip_address, "pending"))
            self.conn.commit()
            self.logger.info(f"Added IP address: {ip_address}")
            self.display.print_success(f"Added IP address: {ip_address}")
        except sqlite3.Error as e:
            self.display.print_error(f"Error adding IP address: {e}")
            self.logger.error(f"Error adding IP address: {e}", extra={"function": "add_ip_address", "file": "sqlite.py", "ip_address": ip_address})  # extra bilgisi eklendi

    def update_ip_status(self, ip_address, status, result=None):
        """
        Updates the status and result of an IP address.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE ip_check SET status = ?, result = ?, last_checked = DATETIME('now') WHERE ip_address = ?",
                (status, result, ip_address))
            self.conn.commit()
            self.logger.info(f"Updated IP address status: {ip_address} - {status}")
            self.display.print_info(f"Updated IP address status: {ip_address} - {status}")
        except sqlite3.Error as e:
            self.display.print_error(f"Error updating IP status: {e}")
            self.logger.error(f"Error updating IP status: {e}", extra={"function": "update_ip_status", "file": "sqlite.py", "ip_address": ip_address, "status": status, "result": result})  # extra bilgisi eklendi

    def get_unchecked_ips(self):
        """
        Gets IP addresses that have not been checked yet or were not checked today.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ip_address FROM ip_check WHERE status != 'completed' OR check_date != DATE('now')")
            ips = [row[0] for row in cursor.fetchall()]
            self.logger.info(f"Retrieved unchecked IP addresses: {len(ips)} addresses")
            self.display.print_info(f"Retrieved {len(ips)} unchecked IP addresses.")
            return ips
        except sqlite3.Error as e:
            self.display.print_error(f"Error getting unchecked IPs: {e}")
            self.logger.error(f"Error getting unchecked IPs: {e}", extra={"function": "get_unchecked_ips", "file": "sqlite.py"})  # extra bilgisi eklendi
            return []

    def get_last_check_date(self):
        """
        Gets the last check date from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT check_date FROM ip_check ORDER BY check_date DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except sqlite3.Error as e:
            self.display.print_error(f"Error getting last check date: {e}")
            self.logger.error(f"Error getting last check date: {e}", extra={"function": "get_last_check_date", "file": "sqlite.py"})  # extra bilgisi eklendi
            raise

    def clear_pending_tasks(self):
        """
        Clears pending tasks from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ip_check WHERE status = 'pending'")
            self.conn.commit()
            self.logger.info("Cleared pending tasks from database.")
            self.display.print_info("Cleared pending tasks from database.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error clearing pending tasks: {e}")
            self.logger.error(f"Error clearing pending tasks: {e}", extra={"function": "clear_pending_tasks", "file": "sqlite.py"})  # extra bilgisi eklendi
            raise

    def close_connection(self):
        """
        Closes the SQLite database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.logger.info("SQLite connection closed.")
            self.display.print_success("SQLite connection closed.")

    def clear_old_tasks(self):
        """
        Clears tasks with check_date older than today from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ip_check WHERE check_date < DATE('now')")
            self.conn.commit()
            self.logger.info("Cleared tasks older than today from database.")
            self.display.print_info("Cleared tasks older than today from database.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error clearing old tasks: {e}")
            self.logger.error(f"Error clearing old tasks: {e}", extra={"function": "clear_old_tasks", "file": "sqlite.py"})  # extra bilgisi eklendi
            raise

    def bulk_update_tasks(self, tasks):
        """
        Bulk updates tasks in SQLite database.

        Args:
            tasks (list): List of processed task dictionaries.
        """
        try:
            cursor = self.conn.cursor()
            for task in tasks:
                cursor.execute(
                    "UPDATE ip_check SET status = ?, last_checked = DATETIME('now') WHERE ip_address = ?",
                    (task["status"], task["ip"])
                )
            self.conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Failed to bulk update tasks: {e}", extra={"function": "bulk_update_tasks", "file": "sqlite.py", "tasks": tasks})  # extra bilgisi eklendi
            raise