import sqlite3
from datetime import date, datetime


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
        self.initialize()

    def initialize(self):
        """
        Ensures the database has the required table.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_check (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT NOT NULL,
                blacklist_name TEXT NOT NULL,
                status TEXT NOT NULL, -- pending, completed, failed
                result TEXT, -- blacklisted, not_blacklisted, error
                check_date DATE NOT NULL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def has_today_records(self):
        """
        Checks if there are records for today's date.

        Returns:
            bool: True if records exist for today, False otherwise.
        """
        self.cursor.execute(
            "SELECT COUNT(*) FROM ip_check WHERE check_date = ?", (self.today,)
        )
        count = self.cursor.fetchone()[0]
        return count > 0

    def insert_tasks(self, tasks):
        """
        Inserts a list of tasks into the database.

        Args:
            tasks (list): List of task dictionaries to be added.
        """
        for task in tasks:
            self.cursor.execute('''
                INSERT INTO ip_check (ip_address, blacklist_name, status, check_date)
                VALUES (?, ?, 'pending', ?)
            ''', (task['ip'], task['blacklist_name'], self.today))
        self.conn.commit()

    def fetch_pending_tasks(self):
        """
        Fetches all pending tasks from the SQLite database.

        Returns:
            list: List of pending task records.
        """
        self.cursor.execute(
            "SELECT id, ip_address, blacklist_name FROM ip_check WHERE status = 'pending'"
        )
        return self.cursor.fetchall()

    def update_task_status(self, task_id, status, result=None):
        """
        Updates the status and result of a specific task.

        Args:
            task_id (int): The ID of the task to update.
            status (str): The new status ('completed', 'failed').
            result (str, optional): The result of the task. Defaults to None.
        """
        self.cursor.execute('''
            UPDATE ip_check
            SET status = ?, result = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, result, task_id))
        self.conn.commit()

    def fetch_completed_tasks(self):
        """
        Fetches all tasks marked as completed.

        Returns:
            list: List of completed task records.
        """
        self.cursor.execute(
            "SELECT * FROM ip_check WHERE status = 'completed'"
        )
        return self.cursor.fetchall()

    def clear_completed_tasks(self):
        """
        Deletes all tasks marked as completed from the database.
        """
        self.cursor.execute(
            "DELETE FROM ip_check WHERE status = 'completed'"
        )
        self.conn.commit()

    def count_tasks_by_status(self):
        """
        Counts tasks grouped by their statuses.

        Returns:
            dict: Dictionary with counts of tasks grouped by their statuses.
        """
        self.cursor.execute(
            "SELECT status, COUNT(*) FROM ip_check GROUP BY status"
        )
        result = {row[0]: row[1] for row in self.cursor.fetchall()}
        return result

    def get_last_updated_tasks(self):
        """
        Fetches the last updated tasks.

        Returns:
            list: List of tasks with their last updated timestamp.
        """
        self.cursor.execute('''
            SELECT id, ip_address, blacklist_name, status, result, last_updated 
            FROM ip_check
            ORDER BY last_updated DESC
            LIMIT 10
        ''')
        return self.cursor.fetchall()

    def reset_pending_tasks(self):
        """
        Resets all pending tasks to allow reprocessing.

        Changes their status to 'pending' and clears their results.
        """
        self.cursor.execute('''
            UPDATE ip_check
            SET status = 'pending', result = NULL, last_updated = CURRENT_TIMESTAMP
            WHERE status != 'pending'
        ''')
        self.conn.commit()

    def close_connection(self):
        """
        Closes the SQLite connection.
        """
        if self.conn:
            self.conn.close()
