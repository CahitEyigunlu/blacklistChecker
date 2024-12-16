import sqlite3
from datetime import date, datetime
from utils.display import Display
from logB.logger import Logger


class TaskManager:
    """
    Manages task lifecycle in SQLite for IP and blacklist processing.
    """

    def __init__(self, conn, config):  # config parametresi eklendi
        """
        Initializes the TaskManager with an existing SQLite connection.

        Args:
            conn (sqlite3.Connection): Existing SQLite connection object.
            config: Uygulama yapılandırması.
        """
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.today = date.today().strftime("%Y-%m-%d")
        self.display = Display()
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])  # Logger nesnesi, config dosyasından log yolunu alıyor
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
            self.logger.error(f"Error initializing table: {e}", extra={"function": "initialize", "file": "task_manager.py"})  # extra bilgisi eklendi
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
            self.logger.error(f"Error checking today's records: {e}", extra={"function": "has_today_records", "file": "task_manager.py"})  # extra bilgisi eklendi
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
            self.logger.error(f"Error inserting tasks: {e}", extra={"function": "insert_tasks", "file": "task_manager.py", "tasks": tasks})  # extra bilgisi eklendi
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
            self.logger.error(f"Error fetching pending tasks: {e}", extra={"function": "fetch_pending_tasks", "file": "task_manager.py"})  # extra bilgisi eklendi
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
            self.logger.error(f"Error updating task {task_id}: {e}", extra={"function": "update_task_status", "file": "task_manager.py", "task_id": task_id, "status": status, "result": result})  # extra bilgisi eklendi
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
            self.logger.error(f"Error fetching tasks for date {date}: {e}", extra={"function": "fetch_tasks_by_date", "file": "task_manager.py", "date": date})  # extra bilgisi eklendi
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
            self.logger.error(f"Error closing SQLite connection: {e}", extra={"function": "close_connection", "file": "task_manager.py"})  # extra bilgisi eklendi
            self.display.print_error(f"Error closing SQLite connection: {e}")

    def bulk_update_tasks(self, tasks):
        """
        Bulk updates the status of tasks in the SQLite database.

        Args:
            tasks (list): A list of task dictionaries with 'ip', 'dns', and 'status' keys.

        Example:
            tasks = [
                {"ip": "192.168.1.1", "dns": "example.com", "status": "completed"},
                {"ip": "192.168.1.2", "dns": "test.com", "status": "failed"},
            ]
        """
        query = """
        UPDATE ip_check
        SET status = :status , result = :result , last_updated = CURRENT_TIMESTAMP
        WHERE ip_address = :ip AND dns = :dns
        """
        try:
            with self.conn:
                self.cursor.executemany(query, tasks)
            self.logger.info(f"Bulk updated {len(tasks)} tasks successfully.")
            self.display.print_success(f"Bulk updated {len(tasks)} tasks successfully.")
        except sqlite3.Error as e:
            self.logger.error(f"Failed to bulk update tasks: {e}", extra={"function": "bulk_update_tasks", "file": "task_manager.py", "tasks": tasks})  # extra bilgisi eklendi
            self.display.print_error(f"Failed to bulk update tasks: {e}")

    def fetch_tasks_by_latest_date(self, result="listed"):
        """
        Fetches tasks with a specific status for the latest check_date.

        Args:
            status (str): The status of the tasks to fetch (default: "blacklisted").

        Returns:
            list[dict]: List of tasks with their details.
        """
        try:
            latest_date = self.get_latest_check_date()
            if not latest_date:
                self.logger.info("No latest check_date available.")
                self.display.print_info("ℹ️ No latest check_date available.")
                return []

            self.cursor.execute(
                "SELECT ip_address, dns, status, result, check_date, last_updated FROM ip_check WHERE check_date = ? AND result = ?",
                (latest_date, result)
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
            self.logger.info(f"Fetched {len(tasks)} tasks with status '{status}' for date {latest_date}.")
            self.display.print_info(f"ℹ️ Fetched {len(tasks)} tasks with status '{status}' for date {latest_date}.")
            return tasks
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching tasks by latest date: {e}", extra={"function": "fetch_tasks_by_latest_date", "file": "task_manager.py", "status": status})
            self.display.print_error(f"❌ Error fetching tasks by latest date: {e}")
            return []

    def get_latest_check_date(self):
        """
        Fetches the latest check_date from the database.

        Returns:
            str: The latest check_date as a string (format: YYYY-MM-DD).
        """
        try:
            self.cursor.execute("SELECT MAX(check_date) FROM ip_check")
            result = self.cursor.fetchone()
            if result and result[0]:
                self.logger.info(f"Latest check_date: {result[0]}")
                self.display.print_info(f"ℹ️ Latest check_date: {result[0]}")
                return result[0]
            else:
                self.logger.info("No records found in ip_check table.")
                self.display.print_info("ℹ️ No records found in ip_check table.")
                return None
        except sqlite3.Error as e:
            self.logger.error(f"Error fetching latest check_date: {e}", extra={"function": "get_latest_check_date", "file": "task_manager.py"})
            self.display.print_error(f"❌ Error fetching latest check_date: {e}")
            raise
