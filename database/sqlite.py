import sqlite3
import aiosqlite
import asyncio
from utils.display import Display
from logB.logger import Logger
from concurrent.futures import ProcessPoolExecutor


class Database:
    """
    Handles SQLite database operations.
    """
    def __init__(self, config):
        self.config = config
        self.db_path = config["sqlite"]["db_path"]
        self.conn = None
        self.executor = ProcessPoolExecutor(max_workers=2)  # 2 paralel süreç
        self.display = Display()
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])

    def connect(self):
        """
        Connects to the SQLite database synchronously.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.logger.info("Connected to SQLite database.")
            self.display.print_success("Connected to SQLite database.")
            return self.conn
        except sqlite3.Error as e:
            self.display.print_error(f"SQLite connection error: {e}")
            self.logger.error(f"SQLite connection error: {e}", extra={"function": "connect", "file": "sqlite.py"})
            return None

    async def async_connect(self):
        """
        Asynchronously connects to the SQLite database.
        """
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            self.logger.info("Connected to SQLite database asynchronously.")
            self.display.print_success("Connected to SQLite database asynchronously.")
        except Exception as e:
            self.display.print_error(f"SQLite async connection error: {e}")
            self.logger.error(f"SQLite async connection error: {e}", extra={"function": "async_connect", "file": "sqlite.py"})

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
            self.logger.error(f"Error creating table: {e}", extra={"function": "create_table", "file": "sqlite.py"})

    async def async_create_table(self):
        """
        Asynchronously creates the table to store IP addresses and check information.
        """
        try:
            async with self.conn.execute('''
                CREATE TABLE IF NOT EXISTS ip_check (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    result TEXT,
                    check_date DATE,
                    last_checked DATETIME)
            ''') as cursor:
                await cursor.close()
            await self.conn.commit()
            self.logger.info("Table created successfully.")
            self.display.print_success("Table created successfully.")
        except Exception as e:
            self.display.print_error(f"Error creating table asynchronously: {e}")
            self.logger.error(f"Error creating table asynchronously: {e}", extra={"function": "async_create_table", "file": "sqlite.py"})

    def bulk_update_tasks_sync(self, tasks):
        """
        Synchronous method to bulk update tasks in SQLite.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:  # Her process için yeni bağlantı
                cursor = conn.cursor()
                for task in tasks:
                    self.display.print_success(f"Updating {task['ip']} with status {task['status']} and result {task['result']}")
                    cursor.execute(
                        "UPDATE ip_check SET status = ?, result = ? , last_checked = DATETIME('now') WHERE ip_address = ?",
                        (task["status"], task["result"],task["ip"])
                    )
                conn.commit()
            self.logger.info(f"Bulk updated {len(tasks)} tasks synchronously.")
        except sqlite3.Error as e:
            self.display.print_error(f"Failed to bulk update tasks: {e}")
            self.logger.error(f"Failed to bulk update tasks: {e}", extra={"function": "bulk_update_tasks_sync", "tasks": tasks})
            raise

    async def bulk_update_tasks(self, tasks):
        """
        Async wrapper for bulk updating tasks using ProcessPoolExecutor.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.bulk_update_tasks_sync, tasks)

    async def async_bulk_update_tasks(self, tasks):
        """
        Asynchronously bulk updates tasks in SQLite database.
        """
        try:
            await self.conn.executemany(
                "UPDATE ip_check SET status = ?, result = ? , last_checked = DATETIME('now') WHERE ip_address = ?",
                [(task["status"],task["result"], task["ip"]) for task in tasks]  # Döngü kaldırıldı
            )
            await self.conn.commit()
            self.logger.info(f"Bulk updated {len(tasks)} tasks asynchronously.")
        except Exception as e:
            self.logger.error(f"Failed to bulk update tasks asynchronously: {e}", extra={"function": "async_bulk_update_tasks", "tasks": tasks})
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

    async def async_close_connection(self):
        """
        Closes the SQLite database connection asynchronously.
        """
        if self.conn:
            await self.conn.close()
            self.logger.info("SQLite async connection closed.")
            self.display.print_success("SQLite async connection closed.")
