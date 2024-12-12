import psycopg2
from logB.logger import Logger

class PostgreSQL:
    """
    PostgreSQL bağlantısı ve işlemleri için bir sınıf.
    """

    def __init__(self, config):  # config parametresi eklendi
        """
        PostgreSQL nesnesini başlatır.

        Args:
            config: Uygulama yapılandırması.
        """
        self.config = config  # config değişkeni eklendi
        self.host = config["postgresql"]["postgres_host"]  # host bilgisi config'den alınıyor
        self.database = config["postgresql"]["postgres_db"]  # database bilgisi config'den alınıyor
        self.user = config["postgresql"]["postgres_user"]  # user bilgisi config'den alınıyor
        self.password = config["postgresql"]["postgres_password"]  # password bilgisi config'den alınıyor
        self.connection = None
        self.cursor = None
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])  # Logger nesnesi, config dosyasından log yolunu alıyor

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
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL bağlantı hatası: {e}", extra={"function": "connect", "file": "postgre.py"})  # extra bilgisi eklendi
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
        except psycopg2.Error as e:
            self.logger.error(f"Sorgu çalıştırma hatası: {e}", extra={"function": "execute_query", "file": "postgre.py", "query": query, "params": params})  # extra bilgisi eklendi
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
            return data
        except psycopg2.Error as e:
            self.logger.error(f"Veri alma hatası: {e}", extra={"function": "fetch_data", "file": "postgre.py", "query": query, "params": params})  # extra bilgisi eklendi
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
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL bağlantı kapatma hatası: {e}", extra={"function": "close_connection", "file": "postgre.py"})  # extra bilgisi eklendi
            raise