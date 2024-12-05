from psycopg2.pool import ThreadedConnectionPool, PoolError
import time
import logging

class PostgreSQLHandler:
    def __init__(self, db_config):
        self.pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=50,  # Havuz kapasitesini artırın
            dbname=db_config['postgres_db'],
            user=db_config['postgres_user'],
            password=db_config['postgres_password'],
            host=db_config['postgres_host'],
            port=db_config.get('postgres_port', 5432)
        )

    def get_connection_with_retry(self, retry_count=3):
        for attempt in range(retry_count):
            try:
                return self.pool.getconn()
            except PoolError:
                if attempt < retry_count - 1:
                    time.sleep(1)  # Biraz bekleyip tekrar deneyin
                else:
                    raise PoolError("Bağlantı havuzu doldu.")

    def save_to_postgres(self, blacklist_name, ip):
        conn = None
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO blacklisted_ips (blacklist, ip) VALUES (%s, %s)",
                (blacklist_name, ip)
            )
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logging.error(f"PostgreSQL hata: {e}", exc_info=True)
        finally:
            if conn:
                self.pool.putconn(conn)
