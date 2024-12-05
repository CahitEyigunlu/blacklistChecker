import socket
from logging_module.logger import Logger
from config_manager import load_config
from display import Display

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")
warning_logger = Logger("logs/warning.log")
debug_logger = Logger("logs/debug.log")

def test_internet_connection():
    """
    İnternet bağlantısını test eder.
    """
    try:
        Display.print_info("İnternet bağlantısı kontrol ediliyor...")
        socket.create_connection(("www.google.com", 80), timeout=5)
        info_logger.info("İnternet bağlantısı başarılı.")
        Display.print_success("İnternet bağlantısı başarılı.")
    except Exception as e:
        error_logger.error(f"İnternet bağlantısı başarısız: {str(e)}")
        Display.print_error("İnternet bağlantısı başarısız.")

def test_dns_server():
    """
    DNS sunucusunu test eder.
    """
    try:
        Display.print_info("DNS sunucusu kontrol ediliyor...")
        socket.gethostbyname("www.google.com")
        info_logger.info("DNS sunucusu başarılı bir şekilde çalışıyor.")
        Display.print_success("DNS sunucusu başarılı.")
    except Exception as e:
        error_logger.error(f"DNS sunucusu başarısız: {str(e)}")
        Display.print_error("DNS sunucusu başarısız.")

from pymongo import MongoClient
def test_mongodb_connection():
    """
    MongoDB bağlantısını test eder.
    Config dosyasından alınan bağlantı detaylarını kullanır.
    """
    try:
        # Config dosyasını yükle
        config = load_config()

        if not config or 'mongo' not in config:
            raise ValueError("MongoDB bağlantı ayarları 'mongo' altında bulunamadı.")

        # MongoDB bağlantı detaylarını al
        mongo_config = config['mongo']
        mongo_uri = mongo_config.get('database_url')
        database_name = mongo_config.get('database_name')

        if not mongo_uri or not database_name:
            raise ValueError("MongoDB URI veya veritabanı adı eksik.")

        # Bağlantı bilgilerini ekrana yazdır
        Display.print_info("MongoDB Bağlantı Bilgileri:")
        Display.print_info(f"  URI: {mongo_uri}")
        Display.print_info(f"  Veritabanı: {database_name}")

        # MongoDB'ye bağlan
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Sunucu bilgilerini kontrol ederek bağlantıyı test et
        
        # Veritabanına bağlan
        db = client[database_name]
        db.list_collection_names()  # Koleksiyon isimlerini kontrol et

        # Bağlantı başarılı
        info_logger.info(f"MongoDB bağlantısı başarılı: {mongo_uri}, Veritabanı: {database_name}")
        Display.print_success("MongoDB bağlantısı başarılı.")
        return True

    except Exception as e:
        # Hata loglama ve kullanıcıya gösterim
        error_logger.error(f"MongoDB bağlantısı başarısız: {str(e)}")
        Display.print_error("MongoDB bağlantısı başarısız.")
        return False

import os
import sqlite3
def test_sqlite_connection():
    """
    SQLite bağlantısını test eder.
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
            open(db_path, 'w').close()  # Yeni dosya oluştur

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

import psycopg2
def test_postgresql_connection():
    """
    PostgreSQL bağlantısını test eder.
    Config dosyasından alınan bağlantı detaylarını kullanır.
    """
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
        port = postgres_config.get('postgres_port', 5432)  # Varsayılan port: 5432

        if not user or not password or not dbname or not host:
            raise ValueError("PostgreSQL bağlantı ayarları eksik.")

        # Bağlantı bilgilerini ekrana yazdır
        Display.print_info("PostgreSQL Bağlantı Bilgileri:")
        Display.print_info(f"  Kullanıcı: {user}")
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
        return False

import time
import dns.resolver

def test_blacklist_health(test_ip="127.0.0.2"):
    """
    Karaliste DNS sağlık kontrolü yapar.
    Her bir karalisteye test_ip üzerinden DNS sorgusu yapar.
    Yanıt alınan durumlarda süreyi kaydeder, alınamayanlarda durumu açıklayıcı bir şekilde rapor eder.
    :param test_ip: Test edilecek IP adresi (varsayılan: 127.0.0.2)
    """
    try:
        # Config dosyasını yükle
        config = load_config()

        if not config or 'blacklists' not in config:
            raise ValueError("Karaliste bilgileri 'blacklists' altında bulunamadı.")

        # Karaliste sonuçlarını tutmak için bir sözlük
        blacklist_results = {}

        # Her bir karaliste için DNS sorgusu yap
        for blacklist in config['blacklists']:
            name = blacklist.get('name', 'Unknown')
            dns_address = blacklist.get('dns', None)

            if not dns_address:
                error_logger.error(f"Karaliste DNS bilgisi eksik: {name}")
                Display.print_warning(f"DNS bilgisi eksik: {name}")
                blacklist_results[name] = {
                    "status": "Eksik DNS bilgisi",
                    "response_time": 0
                }
                continue

            try:
                Display.print_info(f"{name} ({dns_address}) kontrol ediliyor...")

                # Zaman ölçümü başlat
                start_time = time.time()

                # DNS sorgusu (test_ip üzerine)
                query = f"{test_ip}.{dns_address}"
                answers = dns.resolver.resolve(query, "A")  # "A" kaydı sorgulanır

                # Zaman ölçümü durdur
                elapsed_time = round((time.time() - start_time) * 1000, 2)  # Milisaniye cinsinden
                blacklist_results[name] = {
                    "status": "IP kara listede",
                    "response_time": elapsed_time,
                    "answers": [answer.to_text() for answer in answers]
                }

                # Başarı mesajı
                info_logger.info(f"{name} ({dns_address}) IP kara listede. Yanıt süresi: {elapsed_time} ms")
                Display.print_success(f"{name} ({dns_address}) IP kara listede. Yanıt süresi: {elapsed_time} ms")

            except dns.resolver.NXDOMAIN:
                # Kara listede olmadığını belirtir
                blacklist_results[name] = {
                    "status": "IP kara listede değil",
                    "response_time": 0
                }
                Display.print_info(f"{name} ({dns_address}): IP kara listede değil.")
                info_logger.info(f"{name} ({dns_address}): IP kara listede değil.")

            except dns.resolver.Timeout:
                # DNS sorgusu zaman aşımına uğradı
                blacklist_results[name] = {
                    "status": "DNS sorgusu zaman aşımına uğradı",
                    "response_time": 0
                }
                Display.print_warning(f"{name} ({dns_address}): DNS sorgusu zaman aşımına uğradı.")
                error_logger.error(f"{name} ({dns_address}): DNS sorgusu zaman aşımına uğradı.")

            except dns.resolver.NoAnswer:
                # DNS sorgusu yanıt vermedi
                blacklist_results[name] = {
                    "status": "DNS yanıt vermedi",
                    "response_time": 0
                }
                Display.print_warning(f"{name} ({dns_address}): DNS yanıt vermedi.")
                error_logger.error(f"{name} ({dns_address}): DNS yanıt vermedi.")

            except Exception as e:
                # Diğer tüm hatalar
                blacklist_results[name] = {
                    "status": "Beklenmeyen hata",
                    "response_time": 0,
                    "error": str(e)
                }
                Display.print_error(f"{name} ({dns_address}) beklenmeyen bir hata nedeniyle çalışmıyor. Hata: {str(e)}")
                error_logger.error(f"{name} ({dns_address}): Beklenmeyen hata. {str(e)}")

        # Tüm sonuçları kullanıcıya göster
        Display.print_info("Karaliste Sağlık Kontrol Sonuçları:")
        for name, result in blacklist_results.items():
            if result["response_time"] > 0:
                Display.print_info(f"{name}: {result['status']} - {result['response_time']} ms")
            else:
                Display.print_warning(f"{name}: {result['status']} (Hata: {result.get('error', 'Belirtilmedi')})")

        return blacklist_results

    except Exception as e:
        # Genel hata loglama ve kullanıcıya gösterim
        error_logger.error(f"Karaliste sağlık kontrolü başarısız: {str(e)}")
        Display.print_error("Karaliste sağlık kontrolü başarısız.")
        return {}



import pika
from config_manager import load_config
from display import Display
from logging_module.logger import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")

def test_rabbitmq_connection():
    """
    RabbitMQ bağlantısını test eder.
    Config dosyasındaki RabbitMQ ayarlarını kullanır.
    """
    try:
        # Config dosyasını yükle
        config = load_config()

        if not config or 'rabbitmq' not in config:
            raise ValueError("RabbitMQ ayarları 'rabbitmq' altında bulunamadı.")

        # RabbitMQ bağlantı detaylarını al
        rabbitmq_config = config['rabbitmq']
        host = rabbitmq_config.get('host')
        port = rabbitmq_config.get('port', 5672)  # Varsayılan port: 5672
        username = rabbitmq_config.get('username')
        password = rabbitmq_config.get('password')

        if not host or not username or not password:
            raise ValueError("RabbitMQ bağlantı ayarları eksik.")

        # Bağlantı bilgilerini ekrana yazdır
        Display.print_info("RabbitMQ Bağlantı Bilgileri:")
        Display.print_info(f"  Host: {host}")
        Display.print_info(f"  Port: {port}")
        Display.print_info(f"  Kullanıcı Adı: {username}")

        # RabbitMQ bağlantısını test et
        credentials = pika.PlainCredentials(username, password)
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            socket_timeout=5  # Zaman aşımı 5 saniye
        )

        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.close()
        connection.close()

        # Başarı mesajı
        info_logger.info(f"RabbitMQ bağlantısı başarılı: {host}:{port}")
        Display.print_success("RabbitMQ bağlantısı başarılı.")
        return True

    except pika.exceptions.ProbableAuthenticationError:
        # Kimlik doğrulama hatası
        error_logger.error("RabbitMQ kimlik doğrulama hatası.")
        Display.print_error("RabbitMQ kimlik doğrulama hatası.")
        return False
    except pika.exceptions.AMQPConnectionError:
        # Bağlantı hatası
        error_logger.error("RabbitMQ bağlantı hatası.")
        Display.print_error("RabbitMQ bağlantı hatası.")
        return False
    except Exception as e:
        # Genel hata
        error_logger.error(f"RabbitMQ testi sırasında beklenmeyen hata: {str(e)}")
        Display.print_error(f"RabbitMQ testi sırasında beklenmeyen hata: {str(e)}")
        return False


def runner():
    """
    Tüm kontrol işlevlerini sırasıyla çalıştırır.
    """
    Display.print_info("Runner başlatılıyor...")
    test_internet_connection()
    test_dns_server()
    test_mongodb_connection()
    test_sqlite_connection()
    test_postgresql_connection()
    test_rabbitmq_connection()
    test_blacklist_health()
    Display.print_success("Tüm testler tamamlandı.")




