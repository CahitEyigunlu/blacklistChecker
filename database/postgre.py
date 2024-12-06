import psycopg2
from logger import logger

class PostgreSQL:
    """
    PostgreSQL bağlantısı ve işlemleri için bir sınıf.
    """

    def __init__(self, host, database, user, password):
        """
        PostgreSQL nesnesini başlatır.

        Args:
            host: PostgreSQL sunucusunun host adı veya IP adresi.
            database: Bağlanılacak veritabanının adı.
            user: PostgreSQL kullanıcı adı.
            password: PostgreSQL kullanıcı şifresi.
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None

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
            logger.info("PostgreSQL sunucusuna başarıyla bağlanıldı.")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL bağlantı hatası: {e}")
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
            logger.info("Sorgu başarıyla çalıştırıldı.")
        except psycopg2.Error as e:
            logger.error(f"Sorgu çalıştırma hatası: {e}")
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
            logger.info(f"Sorgudan {len(data)} satır veri alındı.")
            return data
        except psycopg2.Error as e:
            logger.error(f"Veri alma hatası: {e}")
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
                logger.info("PostgreSQL bağlantısı kapatıldı.")
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL bağlantı kapatma hatası: {e}")
            raise