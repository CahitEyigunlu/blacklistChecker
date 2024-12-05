import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pika

from config_manager import load_config
from display import Display
from mongo import MongoDBHandler
from postgre import PostgreSQLHandler
from query import QueryCommand
from sqlite import SQLiteTaskManager


class TaskDistributer:
    """
    RabbitMQ kuyruğundan görevleri alıp işleyen sınıf.
    """

    def __init__(self, rabbitmq_config, max_active_tasks=5):
        self.rabbitmq_config = rabbitmq_config
        self.max_active_tasks = max_active_tasks
        self.active_tasks = 0
        self.lock = threading.Lock()

        # Config dosyasını yükleyin
        config = load_config()

        # Handler nesnelerini başlatın
        try:
            self.mongodb_handler = MongoDBHandler(
                config['mongo']['database_url'],
                config['mongo']['database_name'],
                "blacklisted_ips"
            )
            self.postgresql_handler = PostgreSQLHandler(config['postgresql'])
            self.sqlite_task_manager = SQLiteTaskManager(config['sqlite']['db_path'])
            self.query_command = QueryCommand(config['blacklists']['dns_address'])
        except KeyError as e:
            Display.print_error(f"Config dosyasında eksik anahtar: {e}")
            logging.error(f"Config dosyasında eksik anahtar: {e}")
            raise

    def setup_rabbitmq(self):
        """
        RabbitMQ bağlantısını kurar ve kuyruğu hazırlar.
        """
        try:
            credentials = pika.PlainCredentials(
                self.rabbitmq_config['username'], self.rabbitmq_config['password']
            )
            connection_params = pika.ConnectionParameters(
                host=self.rabbitmq_config['host'],
                port=self.rabbitmq_config.get('port', 5672),
                credentials=credentials
            )
            connection = pika.BlockingConnection(connection_params)
            self.channel = connection.channel()
            self.channel.queue_declare(queue="task_queue", durable=True)
        except Exception as e:
            Display.print_error(f"RabbitMQ bağlantısı kurulurken hata oluştu: {e}")
            logging.error(f"RabbitMQ bağlantısı kurulurken hata oluştu: {e}", exc_info=True)
            raise

    def parse_task(self, task: str) -> dict:
        """
        Görev verisini temizler ve bir sözlük formatına dönüştürür.

        Args:
            task (str): Gelen görev verisi.

        Returns:
            dict: Temizlenmiş ve ayrıştırılmış görev verisi.
        """
        try:
            # Verinin formatını belirle
            if task.startswith("!!python/tuple"):
                # Tuple formatında veriyi ayrıştır
                task = task.replace("!!python/tuple\n-", "").replace("\n-", ",").replace("\n", ",")
                task = task.strip().strip(",")
                elements = [elem.strip().strip("'\"") for elem in task.split(",")]

                # Tuple formatı için doğru sayıda eleman kontrolü
                if len(elements) != 6:
                    raise ValueError("Tuple formatında beklenen sayıda eleman yok.")

                task_dict = {
                    'id': int(elements[0]),
                    'ip': elements[1],
                    'blacklist': elements[2],
                    'source': elements[3],
                    'status': elements[4],
                    'date': elements[5],
                }
            else:
                # Anahtar-Değer formatını ayrıştır
                lines = task.split("\n")
                task_dict = {}
                for line in lines:
                    if ":" in line:
                        key, value = line.split(":", 1)
                        task_dict[key.strip()] = value.strip().strip("'\"")

                # Eksik değerleri doldur
                task_dict.setdefault('id', None)
                task_dict.setdefault('ip', None)
                task_dict.setdefault('blacklist', None)
                task_dict.setdefault('source', None)
                task_dict.setdefault('status', None)
                task_dict.setdefault('date', None)

            return task_dict
        except ValueError as e:
            Display.print_error(f"Görev ayrıştırılırken hata oluştu: {e}")
            logging.error(f"Görev ayrıştırılırken hata oluştu: {e}")
            raise
        except Exception as e:
            Display.print_error(f"Görev ayrıştırılırken beklenmeyen bir hata oluştu: {e}")
            logging.error(f"Görev ayrıştırılırken beklenmeyen bir hata oluştu: {e}", exc_info=True)
            raise

    def process_task(self, task: str):
        """
        Görevi işler, kara liste kontrolü yapar ve veritabanlarına kaydeder.

        Args:
            task (str): İşlenecek görev verisi.
        """
        try:
            Display.print_info(f"Görev işleniyor: {task}")
            if not task.strip():
                Display.print_warning("Görev verisi boş. Atlanıyor...")
                return

            # Görevi temizle ve ayrıştır
            task_dict = self.parse_task(task)
            logging.info(f"Ayrıştırılan görev: {task_dict}")

            ip_address = task_dict['ip']
            blacklist_name = task_dict['blacklist']

            # Kara liste kontrolü
            try:
                if self.query_command.check_blacklist(ip_address):
                    Display.print_info(f"IP adresi {ip_address} kara listede bulundu.")

                    # Veriyi MongoDB ve PostgreSQL'e kaydet
                    try:
                        self.mongodb_handler.save_to_mongo(blacklist_name, ip_address)
                        self.postgresql_handler.save_to_postgres(blacklist_name, ip_address)
                        Display.print_success(f"Veritabanlarına kaydedildi: IP: {ip_address}, Kara Liste: {blacklist_name}")
                    except Exception as e:
                        Display.print_error(f"Veritabanına kaydedilirken hata oluştu: {e}")
                        logging.error(f"Veritabanına kaydedilirken hata oluştu: {e}", exc_info=True)
                        return
                else:
                    Display.print_info(f"IP adresi {ip_address} kara listede bulunamadı.")
            except Exception as e:
                Display.print_error(f"Kara liste kontrolü sırasında hata oluştu: {e}")
                logging.error(f"Kara liste kontrolü sırasında hata oluştu: {e}", exc_info=True)
                return

            # SQLite'tan görevi sil
            try:
                self.sqlite_task_manager.delete_completed_task(task_dict['id'])
                Display.print_info(f"Görev silindi: {task_dict['id']}")
            except Exception as e:
                Display.print_error(f"SQLite'tan görev silinirken hata oluştu: {e}")
                logging.error(f"SQLite'tan görev silinirken hata oluştu: {e}", exc_info=True)
                return

            Display.print_success(f"Görev başarıyla tamamlandı: IP: {ip_address}, Kara Liste: {blacklist_name}")

        except KeyError as e:
            Display.print_error(f"Görev verilerinde eksik anahtar: {e}")
            logging.error(f"Görev verilerinde eksik anahtar: {e}")
        except Exception as e:
            Display.print_error(f"Görev işlenirken beklenmeyen bir hata oluştu: {e}")
            logging.error(f"Görev işlenirken beklenmeyen bir hata oluştu: {e}", exc_info=True)

        finally:
            with self.lock:
                self.active_tasks -= 1

    def run(self):
        """
        RabbitMQ kuyruğunu dinler ve gelen görevleri işler.
        """
        try:
            self.setup_rabbitmq()
            with ThreadPoolExecutor(max_workers=self.max_active_tasks) as executor:
                futures = []
                while True:
                    if self.active_tasks < self.max_active_tasks:
                        method_frame, header_frame, body = self.channel.basic_get(queue="task_queue", auto_ack=False)
                        if body:
                            task = body.decode('utf-8')

                            if not task.strip():
                                Display.print_warning("Boş görev alındı. Atlanıyor...")
                                self.channel.basic_ack(method_frame.delivery_tag)
                                continue

                            with self.lock:
                                self.active_tasks += 1
                            future = executor.submit(self.process_task, task)
                            futures.append(future)
                            self.channel.basic_ack(method_frame.delivery_tag)

                    # Gelecek görevleri kontrol et
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            Display.print_error(f"Bir görevde hata oluştu: {e}")
                            logging.error(f"Bir görevde hata oluştu: {e}", exc_info=True)

                    # Tamamlanan görevleri temizle
                    futures = [f for f in futures if not f.done()]
        except KeyboardInterrupt:
            Display.print_info("Program sonlandırılıyor...")
            logging.info("Program sonlandırılıyor...")
        except Exception as e:
            Display.print_error(f"Beklenmeyen bir hata oluştu: {e}")
            logging.error(f"Beklenmeyen bir hata oluştu: {e}", exc_info=True)