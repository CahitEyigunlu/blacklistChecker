import os
import yaml
import sqlite3
import ipaddress
import psycopg2
from datetime import datetime
from pytz import timezone
import pika
from config_manager import load_config
from display import Display
from logging_module.logger import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")

class Controller:
    def __init__(self):
        """
        Controller sınıfını başlatır.
        Config değerlerini yükler ve bugünkü tarihi Istanbul saatine göre alır.
        """
        self.config = load_config()
        self.current_date = self.get_current_date()
        self.rabbitmq_channel = None

    @staticmethod
    def get_current_date():
        """
        Istanbul saatine göre bugünün tarihini döner.
        """
        istanbul_tz = timezone('Europe/Istanbul')
        return datetime.now(istanbul_tz).strftime("%Y-%m-%d")

    def setup_rabbitmq(self):
        """
        RabbitMQ bağlantısını kurar ve kuyruğu oluşturup temizler.
        """
        try:
            rabbitmq_config = self.config.get('rabbitmq', {})
            credentials = pika.PlainCredentials(rabbitmq_config['username'], rabbitmq_config['password'])
            connection_params = pika.ConnectionParameters(
                host=rabbitmq_config['host'],
                port=rabbitmq_config.get('port', 5672),
                credentials=credentials
            )
            connection = pika.BlockingConnection(connection_params)
            self.rabbitmq_channel = connection.channel()

            # Kuyruğu oluştur
            self.rabbitmq_channel.queue_declare(queue="task_queue", durable=True)

            # Kuyruğu temizle
            self.rabbitmq_channel.queue_purge(queue="task_queue")
            info_logger.info("RabbitMQ kuyruğu oluşturuldu ve temizlendi.")
            Display.print_success("RabbitMQ kuyruğu oluşturuldu ve temizlendi.")
        except Exception as e:
            error_logger.error(f"RabbitMQ ayarlanırken hata oluştu: {str(e)}")
            Display.print_error(f"RabbitMQ ayarlanırken hata oluştu: {str(e)}")


    def clear_old_records(self):
        """
        SQLite veritabanından bugünden eski kayıtları temizler.
        """
        try:
            sqlite_config = self.config.get('sqlite', {})
            db_path = sqlite_config['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Eski kayıtları sil
            query = "DELETE FROM tasks WHERE date < ?"
            cursor.execute(query, (self.current_date,))
            conn.commit()

            info_logger.info("SQLite eski kayıtlar temizlendi.")
            Display.print_success("SQLite eski kayıtlar temizlendi.")
            conn.close()
        except Exception as e:
            error_logger.error(f"SQLite kayıtları temizlenirken hata oluştu: {str(e)}")
            Display.print_error(f"SQLite kayıtları temizlenirken hata oluştu: {str(e)}")

    def check_pending_tasks(self):
        """
        SQLite'da bugünkü pending görevleri kontrol eder.
        """
        try:
            sqlite_config = self.config.get('sqlite', {})
            db_path = sqlite_config['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Pending görevleri kontrol et
            query = "SELECT * FROM tasks WHERE date = ? AND status = 'pending'"
            cursor.execute(query, (self.current_date,))
            pending_tasks = cursor.fetchall()

            conn.close()

            if pending_tasks:
                Display.print_info("Bugünkü pending görevler bulundu.")
                info_logger.info("Bugünkü pending görevler bulundu.")
                self.synchronize_tasks_with_rabbitmq(pending_tasks)
                return True
            else:
                return False
        except Exception as e:
            error_logger.error(f"SQLite pending görev kontrolü sırasında hata oluştu: {str(e)}")
            Display.print_error(f"SQLite pending görev kontrolü sırasında hata oluştu: {str(e)}")
            return False

    def synchronize_tasks_with_rabbitmq(self, tasks):
        """
        Görevleri RabbitMQ kuyruğuna senkronize eder.
        """
        try:
            for task in tasks:
                self.rabbitmq_channel.basic_publish(
                    exchange='',
                    routing_key='task_queue',
                    body=yaml.dump(task)
                )
            info_logger.info("Görevler RabbitMQ'ya senkronize edildi.")
            Display.print_success("Görevler RabbitMQ'ya senkronize edildi.")
        except Exception as e:
            error_logger.error(f"Görevler RabbitMQ'ya senkronize edilirken hata oluştu: {str(e)}")
            Display.print_error(f"Görevler RabbitMQ'ya senkronize edilirken hata oluştu: {str(e)}")

    def check_postgresql_for_today(self):
        """
        PostgreSQL'de bugünkü görevlerin durumunu kontrol eder.
        """
        try:
            postgres_config = self.config.get('postgresql', {})
            conn = psycopg2.connect(
                dbname=postgres_config['postgres_db'],
                user=postgres_config['postgres_user'],
                password=postgres_config['postgres_password'],
                host=postgres_config['postgres_host'],
                port=postgres_config.get('postgres_port', 5432)
            )
            cursor = conn.cursor()

            # Bugünkü görevleri kontrol et
            query = "SELECT * FROM completed_tasks WHERE date = %s"
            cursor.execute(query, (self.current_date,))
            completed_tasks = cursor.fetchall()

            conn.close()

            if completed_tasks:
                Display.print_info("Bugünkü görevler PostgreSQL'de zaten tamamlanmış.")
                info_logger.info("Bugünkü görevler PostgreSQL'de zaten tamamlanmış.")
                return True
            else:
                return False
        except Exception as e:
            error_logger.error(f"PostgreSQL kontrolü sırasında hata oluştu: {str(e)}")
            Display.print_error(f"PostgreSQL kontrolü sırasında hata oluştu: {str(e)}")
            return False
        
    def create_new_tasks(self):
        """
        Yeni görevler oluşturur ve SQLite'e yazar.
        CIDR formatındaki adresleri tekil IP adreslerine dönüştürür.
        """
        try:
            # YAML dosyasını oku
            with open('results/netconf_24_prefixes.yaml', 'r') as file:
                data = yaml.safe_load(file)

            # prefixes anahtarını kontrol et ve listeyi al
            prefixes = data.get('prefixes') if isinstance(data, dict) else data

            if not isinstance(prefixes, list):
                raise ValueError("YAML dosyasında geçerli bir 'prefixes' listesi bulunamadı.")

            tasks = []

            for cidr in prefixes:
                try:
                    # CIDR'ı tekil IP adreslerine aç
                    network = ipaddress.ip_network(cidr, strict=False)
                    for ip in network.hosts():
                        for blacklist in self.config.get('blacklists', []):
                            tasks.append({
                                "ip": str(ip),
                                "blacklist": blacklist['name'],
                                "dns": blacklist['dns'],
                                "status": "pending",
                                "date": self.current_date
                            })
                except ValueError as e:
                    # Geçersiz CIDR formatı için hata loglama
                    error_logger.error(f"Geçersiz CIDR formatı: {cidr} - Hata: {str(e)}")
                    Display.print_error(f"Geçersiz CIDR formatı: {cidr} - Hata: {str(e)}")
                    continue

            # SQLite'e yaz
            sqlite_config = self.config.get('sqlite', {})
            db_path = sqlite_config['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            insert_query = """
                INSERT INTO tasks (ip, blacklist, dns, status, date) 
                VALUES (?, ?, ?, ?, ?)
            """
            cursor.executemany(insert_query, [
                (task['ip'], task['blacklist'], task['dns'], task['status'], task['date'])
                for task in tasks
            ])
            conn.commit()
            conn.close()

            Display.print_success("Yeni görevler SQLite'e yazıldı.")
            info_logger.info("Yeni görevler SQLite'e yazıldı.")

            # Görevleri RabbitMQ'ya senkronize et
            self.synchronize_tasks_with_rabbitmq(tasks)
        except Exception as e:
            error_logger.error(f"Yeni görevler oluşturulurken hata oluştu: {str(e)}")
            Display.print_error(f"Yeni görevler oluşturulurken hata oluştu: {str(e)}")


    def initialize_databases(self):
        """
        Tüm veritabanları için gerekli tabloları oluşturur.
        """
        self.initialize_sqlite()
        self.initialize_postgresql()

    def initialize_postgresql(self):
        """
        PostgreSQL'de gerekli tabloları oluşturur.
        """
        try:
            postgres_config = self.config.get('postgresql', {})
            conn = psycopg2.connect(
                dbname=postgres_config['postgres_db'],
                user=postgres_config['postgres_user'],
                password=postgres_config['postgres_password'],
                host=postgres_config['postgres_host'],
                port=postgres_config.get('postgres_port', 5432)
            )
            cursor = conn.cursor()

            # Tamamlanan görevler tablosunu oluştur
            create_completed_tasks_table = """
            CREATE TABLE IF NOT EXISTS completed_tasks (
                id SERIAL PRIMARY KEY,
                ip TEXT NOT NULL,
                blacklist TEXT NOT NULL,
                dns TEXT NOT NULL,
                status TEXT NOT NULL,
                date DATE NOT NULL
            )
            """
            cursor.execute(create_completed_tasks_table)
            conn.commit()

            info_logger.info("PostgreSQL gerekli tablolar başarıyla oluşturuldu.")
            Display.print_success("PostgreSQL gerekli tablolar başarıyla oluşturuldu.")
            conn.close()
        except Exception as e:
            error_logger.error(f"PostgreSQL tabloları oluşturulurken hata oluştu: {str(e)}")
            Display.print_error(f"PostgreSQL tabloları oluşturulurken hata oluştu: {str(e)}")


    def initialize_sqlite(self):
        """
        SQLite'da gerekli tabloları oluşturur.
        """
        try:
            sqlite_config = self.config.get('sqlite', {})
            db_path = sqlite_config['db_path']
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Görevler tablosunu oluştur
            create_tasks_table = """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT NOT NULL,
                blacklist TEXT NOT NULL,
                dns TEXT NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL
            )
            """
            cursor.execute(create_tasks_table)
            conn.commit()

            info_logger.info("SQLite gerekli tablolar başarıyla oluşturuldu.")
            Display.print_success("SQLite gerekli tablolar başarıyla oluşturuldu.")
            conn.close()
        except Exception as e:
            error_logger.error(f"SQLite tabloları oluşturulurken hata oluştu: {str(e)}")
            Display.print_error(f"SQLite tabloları oluşturulurken hata oluştu: {str(e)}")

    def execute(self):
        """
        Controller ana iş akışını yürütür.
        """
        # Veritabanlarını başlat
        self.initialize_databases()
        # RabbitMQ'yu başlat ve kuyruğu temizle
        self.setup_rabbitmq()
        # Eski kayıtları temizle
        self.clear_old_records()
        # Bugünkü görevleri kontrol et
        if self.check_pending_tasks():
            Display.print_info("Pending görevler RabbitMQ'ya senkronize edildi.")
            return
        if self.check_postgresql_for_today():
            Display.print_info("Bugünkü görevler zaten tamamlanmış.")
            return
        # Yeni görevler oluştur
        self.create_new_tasks()
