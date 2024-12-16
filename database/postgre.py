import psycopg2
import sqlite3
from logB.logger import Logger
from utils.display import Display

class PostgreSQL:
    """
    PostgreSQL bağlantısı ve işlemleri için bir sınıf.
    """

    def __init__(self, config):
        """
        PostgreSQL nesnesini başlatır.

        Args:
            config: Uygulama yapılandırması.
        """
        self.config = config
        self.host = config["postgresql"]["postgres_host"]
        self.database = config["postgresql"]["postgres_db"]
        self.user = config["postgresql"]["postgres_user"]
        self.password = config["postgresql"]["postgres_password"]
        self.connection = None
        self.cursor = None
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.display = Display()

    def connect(self):
        """
        PostgreSQL sunucusuna bağlanır.
        """
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()
            self.logger.info("PostgreSQL sunucusuna başarıyla bağlanıldı.")
            self.display.print_success("✔️ PostgreSQL sunucusuna başarıyla bağlanıldı.")
        except psycopg2.Error as e:
            error_message = f"PostgreSQL bağlantı hatası: {e}"
            self.logger.error(error_message, extra={"function": "connect", "file": "postgre.py"})
            self.display.print_error(f"❌ {error_message}")
            raise

    def execute_query(self, query, params=None):
        """
        Belirtilen sorguyu çalıştırır.

        Args:
            query: Çalıştırılacak SQL sorgusu.
            params: Sorgu parametreleri (isteğe bağlı).
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            self.display.print_success("✔️ Query : " + query + " executed successfully")
        except psycopg2.Error as e:
            error_message = f"Query çalıştırma hatası: {e}"
            self.logger.error(error_message, extra={"function": "execute_query", "file": "postgre.py", "query": query, "params": params})
            self.display.print_error(f"❌ {error_message}")
            raise

    def fetch_data(self, query, params=None):
        """
        Belirtilen sorguyu çalıştırır ve sonuçları döndürür.

        Args:
            query: Çalıştırılacak SQL sorgusu.
            params: Sorgu parametreleri (isteğe bağlı).

        Returns:
            Sorgu sonuçlarının listesi.
        """
        try:
            self.cursor.execute(query, params)
            data = self.cursor.fetchall()
            self.logger.info(f"Sorgudan {len(data)} satır veri alındı.")
            self.display.print_success(f"✔️ Sorgudan {len(data)} satır veri alındı.")
            return data
        except psycopg2.Error as e:
            error_message = f"Veri alma hatası: {e}"
            self.logger.error(error_message, extra={"function": "fetch_data", "file": "postgre.py", "query": query, "params": params})
            self.display.print_error(f"❌ {error_message}")
            raise

    def close_connection(self):
        """
        PostgreSQL bağlantısını kapatır.
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                self.logger.info("PostgreSQL bağlantısı kapatıldı.")
                self.display.print_success("✔️ PostgreSQL bağlantısı kapatıldı.")
        except psycopg2.Error as e:
            error_message = f"PostgreSQL bağlantı kapatma hatası: {e}"
            self.logger.error(error_message, extra={"function": "close_connection", "file": "postgre.py"})
            self.display.print_error(f"❌ {error_message}")
            raise

    def process_queue_and_exit(self, queue_fetch_func):
        """
        Kuyruk işlemleri bittikten sonra veritabanını kapatır.

        Args:
            queue_fetch_func: Kuyrukta veri olup olmadığını kontrol eden fonksiyon.
        """
        try:
            self.connect()
            while True:
                tasks = queue_fetch_func()
                if not tasks:
                    self.logger.info("Kuyrukta iş kalmadı. İşlem tamamlandı.")
                    self.display.print_success("✔️ Kuyrukta iş kalmadı. İşlem tamamlandı.")
                    break
                for task in tasks:
                    self.execute_query(task['query'], task.get('params'))
            self.logger.info("Tüm işler başarıyla işlendi.")
            self.display.print_success("✔️ Tüm işler başarıyla işlendi.")
        except Exception as e:
            error_message = f"Kuyruk işlemleri sırasında hata: {e}"
            self.logger.error(error_message, extra={"function": "process_queue_and_exit", "file": "postgre.py"})
            self.display.print_error(f"❌ {error_message}")
            raise
        finally:
            self.close_connection()

    def ensure_blacklisted_tasks_table_exists(self):
        """
        Ensures that the 'blacklisted_tasks' table exists in the PostgreSQL database.
        Creates the table if it does not exist or updates it with the UNIQUE constraint.
        """
        try:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS blacklisted_tasks (
                id SERIAL PRIMARY KEY,
                ip_address TEXT NOT NULL,
                dns TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                check_date DATE NOT NULL,
                last_updated TIMESTAMP NOT NULL,
                UNIQUE (ip_address, dns, check_date) -- Prevent duplicate entries
            );
            """
            self.execute_query(create_table_query)
            self.logger.info("Ensured 'blacklisted_tasks' table exists with UNIQUE constraint.")
            self.display.print_success("✔️ Ensured 'blacklisted_tasks' table exists with UNIQUE constraint.")
        except Exception as e:
            error_message = f"Error ensuring 'blacklisted_tasks' table exists: {e}"
            self.logger.error(error_message, extra={"function": "ensure_blacklisted_tasks_table_exists", "file": "postgre.py"})
            self.display.print_error(f"❌ {error_message}")
            raise
    
    def process_sqlite_to_postgres_and_exit(self, sqlite_manager):
        """
        Processes 'blacklisted' tasks from SQLite for the latest date and inserts them into PostgreSQL.
        Closes the connection after processing.
        
        Args:
            sqlite_manager: The SQLite TaskManager instance to fetch tasks.
        """
        try:
            self.connect()  # Connect to PostgreSQL
            
            # Ensure the table exists before proceeding
            self.ensure_blacklisted_tasks_table_exists()

            # Fetch 'blacklisted' tasks from SQLite for the latest date
            blacklisted_tasks = sqlite_manager.fetch_tasks_by_latest_date("listed")
            if not blacklisted_tasks:
                self.logger.info("No 'blacklisted' tasks found in SQLite.")
                self.display.print_info("ℹ️ No 'blacklisted' tasks found in SQLite.")
                return
            
            self.logger.info(f"Found {len(blacklisted_tasks)} 'blacklisted' tasks to transfer.")
            self.display.print_info(f"ℹ️ Transferring {len(blacklisted_tasks)} 'blacklisted' tasks to PostgreSQL.")

            # Insert tasks into PostgreSQL
            for task in blacklisted_tasks:
                try:
                    query = """
                    INSERT INTO blacklisted_tasks (ip_address, dns, status, result, check_date, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ip_address, dns, check_date) DO UPDATE
                    SET status = EXCLUDED.status, result = EXCLUDED.result, last_updated = EXCLUDED.last_updated;
                    """
                    params = (
                        task["ip"], task["dns"], task["status"], task["result"], task["check_date"], task["last_updated"]
                    )
                    self.execute_query(query, params)
                except Exception as e:
                    if "relation" in str(e) and "does not exist" in str(e):
                        self.logger.warning("Table 'blacklisted_tasks' not found. Attempting to create it.")
                        self.ensure_blacklisted_tasks_table_exists()
                        self.logger.info("Retrying insertion after table creation.")
                        self.execute_query(query, params)  # Retry the insertion
                    else:
                        raise e  # Re-raise unexpected exceptions
            
            self.logger.info(f"Transferred {len(blacklisted_tasks)} 'blacklisted' tasks successfully.")
            self.display.print_success(f"✔️ Transferred {len(blacklisted_tasks)} 'blacklisted' tasks successfully.")
        except Exception as e:
            error_message = f"Error during SQLite to PostgreSQL transfer: {e}"
            self.logger.error(error_message, extra={"function": "process_sqlite_to_postgres_and_exit", "file": "postgre.py"})
            self.display.print_error(f"❌ {error_message}")
            raise
        finally:
            self.close_connection()  # Ensure PostgreSQL connection is closed
