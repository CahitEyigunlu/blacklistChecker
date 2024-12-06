import sqlite3
from datetime import date, datetime
from utils.display import Display
from logB.logger import Logger


class TaskManager:
    """
    Manages task lifecycle in SQLite for IP and blacklist processing.
    """

    def __init__(self, conn):
        """
        Initializes the TaskManager with an existing SQLite connection.

        Args:
            conn (sqlite3.Connection): Existing SQLite connection object.
        """
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.today = date.today().strftime("%Y-%m-%d")
        self.display = Display()
        self.logger = Logger(log_file_path="logs/task_manager.log")
        self.initialize()

    def initialize(self):
        """
        Ensures the database has the required table.
        """
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_check (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    dns TEXT NOT NULL,
                    status TEXT NOT NULL, -- pending, completed, failed
                    result TEXT, -- blacklisted, not_blacklisted, error
                    check_date DATE NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            self.conn.commit()
            self.logger.info("Table initialized successfully.")
            self.display.print_success("Table initialized successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing table: {e}")
            self.display.print_error(f"Error initializing table: {e}")

    def has_today_records(self):
        """
        Checks if there are records for today's date.

        Returns:
            bool: True if records exist for today, False otherwise.
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM ip_check WHERE check_date = ?", (self.today,)
            )
            count = self.cursor.fetchone()[0]
            self.logger.info(f"Found {count} records for today ({self.today}).")
            self.display.print_info(f"Found {count} records for today ({self.today}).")
            return count > 0
        except sqlite3.Error as e:
            self.logger.error(f"Error checking today's records: {e}")
            self.display.print_error(f"Error checking today's records: {e}")
            return False

    def insert_tasks(self, tasks):
        """
        Inserts a list of tasks into the database.

        Args:
            tasks (list): List of task dictionaries to be added.
        """
        try:
            for task in tasks:
                self.cursor.execute('''
                    INSERT INTO ip_check (ip_address, dns, status, check_date)
                    VALUES (?, ?, 'pending', ?)
                ''', (task['ip'], task['dns'], self.today))
            self.conn.commit()
            self.logger.info(f"Inserted {len(tasks)} tasks successfully.")
            self.display.print_success(f"Inserted {len(tasks)} tasks successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Error inserting tasks: {e}")
            self.display.print_error(f"Error inserting tasks: {e}")

    def fetch_pending_tasks(self):
        """
        Fetches all pending tasks from the SQLite database.

        Returns:
            list: List of pending task records.
        """
        try:
            self.cursor.execute(
                "SELECT id, ip_address, dns FROM ip_check WHERE status = 'pending'"
            )
            tasks = self.cursor.fetchall()
            self.logger.info(f"Fetched {len(tasks)} pending tasks.")
            self.display.print_info(f"Fetched {len(tasks)} pending tasks.")
            return tasks
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching pending tasks: {e}")
            self.display.print_error(f"Error fetching pending tasks: {e}")
            return []

    def update_task_status(self, task_id, status, result=None):
        """
        Updates the status and result of a specific task.

        Args:
            task_id (int): The ID of the task to update.
            status (str): The new status ('completed', 'failed').
            result (str, optional): The result of the task. Defaults to None.
        """
        try:
            self.cursor.execute('''
                UPDATE ip_check
                SET status = ?, result = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, result, task_id))
            self.conn.commit()
            self.logger.info(f"Task {task_id} updated to status '{status}' with result '{result}'.")
            self.display.print_success(f"Task {task_id} updated to status '{status}'.")
        except sqlite3.Error as e:
            self.logger.error(f"Error updating task {task_id}: {e}")
            self.display.print_error(f"Error updating task {task_id}: {e}")

    def fetch_tasks_by_date(self, date):
        """
        Fetches tasks from the database for the specified date.

        Args:
            date (str): The date to filter tasks (format: YYYY-MM-DD).

        Returns:
            list[dict]: List of tasks with their details.
        """
        try:
            self.cursor.execute(
                "SELECT ip_address, dns, status, result, check_date, last_updated FROM ip_check WHERE check_date = ?",
                (date,)
            )
            rows = self.cursor.fetchall()
            tasks = [
                {
                    "ip": row[0],
                    "dns": row[1],
                    "status": row[2],
                    "result": row[3],
                    "check_date": row[4],
                    "last_updated": row[5]
                }
                for row in rows
            ]
            self.logger.info(f"Fetched {len(tasks)} tasks for date {date}.")
            self.display.print_info(f"Fetched {len(tasks)} tasks for date {date}.")
            return tasks
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching tasks for date {date}: {e}")
            self.display.print_error(f"Error fetching tasks for date {date}: {e}")
            return []

    def close_connection(self):
        """
        Closes the SQLite connection.
        """
        try:
            if self.conn:
                self.conn.close()
                self.logger.info("SQLite connection closed.")
                self.display.print_success("SQLite connection closed.")
        except sqlite3.Error as e:
            self.logger.error(f"Error closing SQLite connection: {e}")
            self.display.print_error(f"Error closing SQLite connection: {e}")
