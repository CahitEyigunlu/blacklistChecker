import psycopg2
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
            self.logger.info("Sorgu başarıyla çalıştırıldı.")
            self.display.print_success("✔️ Sorgu başarıyla çalıştırıldı.")
        except psycopg2.Error as e:
            error_message = f"Sorgu çalıştırma hatası: {e}"
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
