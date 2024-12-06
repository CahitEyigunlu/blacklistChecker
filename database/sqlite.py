import sqlite3
from utils.display import Display
from logB.logger import Logger


class Database:
    """
    Handles SQLite database operations.
    """

    def __init__(self, db_path):
        """
        Initializes Database with the database path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = None
        self.display = Display()
        self.Logger = Logger(log_file_path="logs/sqlite.log")  # Logger örneği

    def connect(self):
        """
        Connects to the SQLite database.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.Logger.info("Connected to SQLite database.")
            self.display.print_success("Connected to SQLite database.")
            return self.conn
        except sqlite3.Error as e:
            self.display.print_error(f"SQLite connection error: {e}")
            self.Logger.error(f"SQLite connection error: {e}")
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
            self.Logger.info("Table created successfully.")
            self.display.print_success("Table created successfully.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error creating table: {e}")
            self.Logger.error(f"Error creating table: {e}")

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
            self.Logger.info(f"Added IP address: {ip_address}")
            self.display.print_success(f"Added IP address: {ip_address}")
        except sqlite3.Error as e:
            self.display.print_error(f"Error adding IP address: {e}")
            self.Logger.error(f"Error adding IP address: {e}")

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
            self.Logger.info(f"Updated IP address status: {ip_address} - {status}")
            self.display.print_info(f"Updated IP address status: {ip_address} - {status}")
        except sqlite3.Error as e:
            self.display.print_error(f"Error updating IP status: {e}")
            self.Logger.error(f"Error updating IP status: {e}")

    def get_unchecked_ips(self):
        """
        Gets IP addresses that have not been checked yet or were not checked today.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ip_address FROM ip_check WHERE status != 'completed' OR check_date != DATE('now')")
            ips = [row[0] for row in cursor.fetchall()]
            self.Logger.info(f"Retrieved unchecked IP addresses: {len(ips)} addresses")
            self.display.print_info(f"Retrieved {len(ips)} unchecked IP addresses.")
            return ips
        except sqlite3.Error as e:
            self.display.print_error(f"Error getting unchecked IPs: {e}")
            self.Logger.error(f"Error getting unchecked IPs: {e}")
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
            self.Logger.error(f"Error getting last check date: {e}")
            raise

    def clear_pending_tasks(self):
        """
        Clears pending tasks from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ip_check WHERE status = 'pending'")
            self.conn.commit()
            self.Logger.info("Cleared pending tasks from database.")
            self.display.print_info("Cleared pending tasks from database.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error clearing pending tasks: {e}")
            self.Logger.error(f"Error clearing pending tasks: {e}")
            raise

    def close_connection(self):
        """
        Closes the SQLite database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.Logger.info("SQLite connection closed.")
            self.display.print_success("SQLite connection closed.")

    def clear_old_tasks(self):
        """
        Clears tasks with check_date older than today from the database.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM ip_check WHERE check_date < DATE('now')")
            self.conn.commit()
            self.Logger.info("Cleared tasks older than today from database.")
            self.display.print_info("Cleared tasks older than today from database.")
        except sqlite3.Error as e:
            self.display.print_error(f"Error clearing old tasks: {e}")
            self.Logger.error(f"Error clearing old tasks: {e}")
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
            self.logger.error(f"Failed to bulk update tasks: {e}")
            raise
