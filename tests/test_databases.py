import os
import sqlite3
import urllib.parse

import psycopg2
from pymongo import MongoClient

from utils.config_manager import load_config
from utils.display import Display
from logB import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")

class DatabaseTests:
    def __init__(self):
        pass

    def run(self):
        """
        Veritabanı bağlantı testlerini çalıştırır ve sonucu döndürür.
        """
        mongodb_result = self.test_mongodb_connection()
        sqlite_result = self.test_sqlite_connection()
        postgresql_result = self.test_postgresql_connection()
        return mongodb_result and sqlite_result and postgresql_result  # Tüm testler başarılıysa True döndür

    def test_mongodb_connection(self):
        """
        MongoDB bağlantısını test eder ve sonucu döndürür.
        Config dosyasından alınan bağlantı detaylarını kullanır.
        """
        mongo_uri = None
        database_name = None
        try:
            # Config dosyasını yükle
            config = load_config()

            if not config or 'mongodb' not in config:
                raise ValueError("MongoDB bağlantı ayarları 'mongodb' altında bulunamadı.")

            # MongoDB bağlantı detaylarını al
            mongo_config = config['mongodb']
            mongo_uri = mongo_config.get('url')
            database_name = mongo_config.get('db_name')

            if not mongo_uri or not database_name:
                raise ValueError("MongoDB URI veya veritabanı adı eksik.")

            # Bağlantı bilgilerini ekrana yazdır (şifre maskelenmiş)
            Display.print_info("MongoDB Bağlantı Bilgileri:")
            Display.print_info(f"  URI: {mask_password(mongo_uri)}")
            Display.print_info(f"  Veritabanı: {database_name}")

            # MongoDB'ye bağlan
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.server_info()

            # Veritabanına bağlan
            db = client[database_name]
            db.list_collection_names()

            # Bağlantı başarılı
            info_logger.info(f"MongoDB bağlantısı başarılı: {mongo_uri}, Veritabanı: {database_name}")
            Display.print_success("MongoDB bağlantısı başarılı.")
            return True

        except Exception as e:
            # Hata loglama ve kullanıcıya gösterim
            error_logger.error(f"MongoDB bağlantısı başarısız: {str(e)}")
            Display.print_error("MongoDB bağlantısı başarısız.")
            # Bağlantı başarısız olursa, bağlantı bilgilerini göster
            Display.print_info("MongoDB Bağlantı Bilgileri:")
            Display.print_info(f"  URI: {mongo_uri or 'Bulunamadı'}")
            Display.print_info(f"  Veritabanı: {database_name or 'Bulunamadı'}")
            return False

    def test_sqlite_connection(self):
        """
        SQLite bağlantısını test eder ve sonucu döndürür.
        Config dosyasından alınan veritabanı dosya yolunu kullanır.
        """
        try:
            # Config dosyasını yükle
            config = load_config()

            if not config or 'sqlite' not in config:
                raise ValueError("SQLite ayarları 'sqlite' altında bulunamadı.")

            # SQLite veritabanı dosya yolunu al
            sqlite_config = config['sqlite']
            db_path = sqlite_config.get('db_path')

            if not db_path:
                raise ValueError("SQLite veritabanı dosya yolu tanımlanmamış.")

            # Bağlantı bilgilerini ekrana yazdır
            Display.print_info("SQLite Bağlantı Bilgileri:")
            Display.print_info(f"  Veritabanı Dosyası: {db_path}")

            # Veritabanı dosyasını kontrol et
            if not os.path.exists(db_path):
                Display.print_warning("Veritabanı dosyası bulunamadı. Yeni bir dosya oluşturulacak...")
                open(db_path, 'w').close()

            # SQLite bağlantısını test et
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Örnek bir SQL sorgusu çalıştır
            cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
            conn.commit()

            # Bağlantı başarılı
            info_logger.info(f"SQLite bağlantısı başarılı: {db_path}")
            Display.print_success("SQLite bağlantısı başarılı.")
            conn.close()
            return True

        except Exception as e:
            # Hata loglama ve kullanıcıya gösterim
            error_logger.error(f"SQLite bağlantısı başarısız: {str(e)}")
            Display.print_error("SQLite bağlantısı başarısız.")
            return False

    def test_postgresql_connection(self):
        """
        PostgreSQL bağlantısını test eder ve sonucu döndürür.
        Config dosyasından alınan bağlantı detaylarını kullanır.
        """
        user = None
        password = None
        dbname = None
        host = None
        port = None
        try:
            # Config dosyasını yükle
            config = load_config()

            if not config or 'postgresql' not in config:
                raise ValueError("PostgreSQL bağlantı ayarları 'postgresql' altında bulunamadı.")

            # PostgreSQL bağlantı detaylarını al
            postgres_config = config['postgresql']
            user = postgres_config.get('postgres_user')
            password = postgres_config.get('postgres_password')
            dbname = postgres_config.get('postgres_db')
            host = postgres_config.get('postgres_host')
            port = postgres_config.get('postgres_port', 5432)

            if not user or not password or not dbname or not host:
                raise ValueError("PostgreSQL bağlantı ayarları eksik.")

            # Bağlantı bilgilerini ekrana yazdır (şifre maskelenmiş)
            Display.print_info("PostgreSQL Bağlantı Bilgileri:")
            Display.print_info(f"  Kullanıcı: {user}")
            Display.print_info(f"  Şifre: ****")
            Display.print_info(f"  Veritabanı: {dbname}")
            Display.print_info(f"  Sunucu: {host}")
            Display.print_info(f"  Port: {port}")

            # PostgreSQL bağlantısını test et
            connection = psycopg2.connect(
                user=user,
                password=password,
                database=dbname,
                host=host,
                port=port
            )

            # Test sorgusu
            cursor = connection.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()

            # Bağlantı başarılı
            if result and result[0] == 1:
                info_logger.info(f"PostgreSQL bağlantısı başarılı: {host}:{port}, Veritabanı: {dbname}")
                Display.print_success("PostgreSQL bağlantısı başarılı.")
            else:
                raise ValueError("PostgreSQL test sorgusu başarısız.")

            # Bağlantıyı kapat
            cursor.close()
            connection.close()
            return True

        except Exception as e:
            # Hata loglama ve kullanıcıya gösterim
            error_logger.error(f"PostgreSQL bağlantısı başarısız: {str(e)}")
            Display.print_error("PostgreSQL bağlantısı başarısız.")
            # Bağlantı başarısız olursa, bağlantı bilgilerini göster (şifre dahil)
            Display.print_info("PostgreSQL Bağlantı Bilgileri:")
            Display.print_info(f"  Kullanıcı: {user or 'Bulunamadı'}")
            Display.print_info(f"  Şifre: {password or 'Bulunamadı'}")
            Display.print_info(f"  Veritabanı: {dbname or 'Bulunamadı'}")
            Display.print_info(f"  Sunucu: {host or 'Bulunamadı'}")
            Display.print_info(f"  Port: {port or 'Bulunamadı'}")
            return False


def mask_password(uri):
    """
    Verilen URI'deki şifreyi maskeler.
    """
    try:
        # URI'yi ayrıştır
        parsed_uri = urllib.parse.urlparse(uri)

        # Şifreyi maskele
        netloc = parsed_uri.netloc.replace(parsed_uri.password, "****") if parsed_uri.password else parsed_uri.netloc

        # Yeni URI'yi oluştur
        masked_uri = urllib.parse.urlunparse(parsed_uri._replace(netloc=netloc))
        return masked_uri
    except Exception as e:
        # URI ayrıştırılamazsa orijinal URI'yi döndür
        error_logger.error(f"URI maskelenemedi: {str(e)}")
        return uri