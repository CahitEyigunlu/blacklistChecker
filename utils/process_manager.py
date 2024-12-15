
import json
import pika
import time
import signal
import aiodns
import asyncio
import aio_pika
import ipaddress
from aiodns import DNSResolver
from logB.logger import Logger
from utils.display import Display
from datetime import datetime, timedelta
from dns.resolver import Resolver, NXDOMAIN, Timeout, NoAnswer, NoNameservers

class AsyncRabbitMQ:
    """
    RabbitMQ'ye asenkron bağlantı ve işlemler için bir sınıf.
    """

    def __init__(self, config):
        """
        AsyncRabbitMQ nesnesini başlatır.

        Args:
            config: Uygulama yapılandırması.
        """
        self.config = config
        self.host = config["rabbitmq"]["host"]
        self.username = config["rabbitmq"]["username"]
        self.password = config["rabbitmq"]["password"]
        self.queue_name = config["rabbitmq"].get("default_queue", "default_queue")
        self.connection = None
        self.channel = None
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.display = Display()
        
    async def connect(self):
        try:
            connection_string = f"amqp://{self.username}:{self.password}@{self.host}:5672//"
            self.connection = await aio_pika.connect_robust(connection_string)
            self.channel = await self.connection.channel()

            # Prefetch ayarını burada yapın
            await self.channel.set_qos(prefetch_count=1)

            try:
                await self.channel.declare_queue(name=self.queue_name, passive=True)
            except aio_pika.exceptions.ChannelPreconditionFailed:
                self.logger.error(f"Kuyruk özellikleri uyumsuz: {self.queue_name}")
                raise

            self.logger.info("RabbitMQ sunucusuna başarıyla bağlanıldı.")
            self.display.print_success("✔️ RabbitMQ sunucusuna başarıyla bağlanıldı.")
        except Exception as e:
            self.logger.error(f"RabbitMQ bağlantı hatası: {e}")
            raise


    async def close_connection(self):
        """
        RabbitMQ bağlantısını asenkron olarak kapatır.
        """
        try:
            if self.connection:
                await self.connection.close()
                self.logger.info("RabbitMQ bağlantısı kapatıldı.")
                self.display.print_success("✔️ RabbitMQ bağlantısı kapatıldı.")
        except Exception as e:
            self.logger.error(f"RabbitMQ bağlantı kapatma hatası: {e}", extra={"function": "close_connection", "file": "process_manager.py"})
            raise

class Worker:
    """
    RabbitMQ'dan görevleri işleyen bir işçiyi temsil eder.
    """

    def __init__(self, worker_id, rabbitmq, process_task):
        self.worker_id = worker_id
        self.rabbitmq = rabbitmq
        self.process_task = process_task
        self.running = True

    async def run(self, queue_name):
        try:
            self.rabbitmq.logger.info(f"Worker {self.worker_id} başlatıldı ve kuyruğa bağlandı: {queue_name}")
            self.rabbitmq.display.print_info(f"Worker {self.worker_id} başlatıldı ve kuyruğa bağlandı: {queue_name}")   
            
            queue = await self.rabbitmq.channel.declare_queue(name=queue_name, durable=False)
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Mesaj alındı, işleniyor.")
                    async with message.process():
                        self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Mesaj işleniyor; Mesaj: {message.body}")
                        await self.process_task(message)
                        await asyncio.sleep(0.1)  # Mesaj işleme sonrası gecikme
                        self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Mesaj başarıyla işlendi.")
        except asyncio.CancelledError:
            self.rabbitmq.display.print_info(f"Worker {self.worker_id} iptal edildi.")
        except Exception as e:
            error_message = f"Worker {self.worker_id} başlatılırken bir hata oluştu: {e}"
            self.rabbitmq.logger.error(error_message)
            self.rabbitmq.display.print_error(error_message)


class ProcessManager:
    """
    RabbitMQ'dan gelen görevlerin işlenmesini yönetir.
    """

    def __init__(self, sqlite_manager, config):
        self.rabbitmq = AsyncRabbitMQ(config)
        self.sqlite_manager = sqlite_manager
        self.config = config
        self.logger = Logger(log_file_path=config["logging"]["error_log_path"])
        self.display = Display()
        self.processed_tasks = []
        self.workers = []
        self.start_time = datetime.now()
        self.concurrency_limit = 50
        self.sqlite_bulk_update_count = config["sqlite"].get("bulk_update_count", 500)
        self.tasks_to_update = []
        self.resolver = aiodns.DNSResolver()

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.stats = {
            "not_listed": 0,
            "listed": 0,
            "timed_out": 0,
            "no_answer": 0,
            "no_nameservers": 0,
            "dns_error": 0,
            "exception": 0
        }

    def display_statistics(self):
        """
        İşlenen görevlerle ilgili istatistikleri görüntüler.
        """
        elapsed_time = datetime.now() - self.start_time
        total_tasks = len(self.processed_tasks)

        self.display.print_info("=== Task Processing Statistics ===")
        self.display.print_info(f"Total Tasks Processed: {total_tasks}")
        self.display.print_info(f"Elapsed Time: {elapsed_time}")

        # Detaylı sonuçların gösterimi
        self.display.print_info("--- Task Results ---")
        for result, count in self.stats.items():
            self.display.print_info(f"{result.capitalize()}: {count}")

        # İşlem oranı ve performans
        if total_tasks > 0:
            avg_time_per_task = elapsed_time / total_tasks
            self.display.print_info(f"Average Time per Task: {avg_time_per_task}")
            self.display.print_info(f"Tasks per Second: {total_tasks / elapsed_time.total_seconds():.2f}")
        else:
            self.display.print_info("No tasks were processed.")

        self.display.print_info("=== End of Statistics ===")

    def signal_handler(self, sig, frame):
        """
        Çalışanları düzgün bir şekilde durdurmak için sonlandırma sinyallerini işler.
        """
        for worker in self.workers:
            worker.cancel()

    async def fetch_and_process_tasks(self, queue_name):
        """
        Görevleri RabbitMQ'dan alır ve işler.
        """
        await self.rabbitmq.connect()  # RabbitMQ'ye bağlan
        # Burada `queue` yerine `name` kullanılıyor
        queue_state = await self.rabbitmq.channel.declare_queue(name=queue_name, passive=True)
        total_tasks = queue_state.declaration_result.message_count
        self.display.print_success(f"Total tasks in the queue: {total_tasks}")

        async def process_task(message):
            try:
                task = json.loads(message.body)
                ip = task["ip"]
                dns = task["dns"]

                result = await self.perform_rdns_check_async(ip, dns)

                task.update({
                    "result": result["result"],
                    "status": result["status"],
                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

                self.processed_tasks.append(task)
                self.tasks_to_update.append(task)
                self.stats[result["result"]] += 1

                elapsed_time = datetime.now() - self.start_time
                tasks_done = len(self.processed_tasks)
                total_tasks_dynamic = total_tasks
                remaining_time = (elapsed_time / tasks_done) * (total_tasks_dynamic - tasks_done) if tasks_done > 0 else timedelta(seconds=0)

                self.display.print_dns_status(
                    worker_id="Async",
                    tasks_done=tasks_done,
                    total_tasks=total_tasks_dynamic,
                    elapsed_time=elapsed_time,
                    remaining_time=remaining_time,
                    ip=ip,
                    dns=dns,
                    result=result["result"],
                    status=result["status"],
                    details=result.get("details", None)
                )

                if len(self.tasks_to_update) >= self.sqlite_bulk_update_count:
                    self.sqlite_manager.bulk_update_tasks(self.tasks_to_update)
                    self.tasks_to_update = []

            except asyncio.CancelledError:
                pass
            except Exception as e:
                error_message = f"Görev işlenirken bir hata oluştu: {e}"
                self.logger.error(error_message)
                self.display.print_error(error_message)

        # Async worker'ları oluştur ve çalıştır
        self.workers = [
            asyncio.create_task(Worker(i + 1, self.rabbitmq, process_task).run(queue_name))
            for i in range(self.concurrency_limit)
        ]

        # Tüm worker'ları bekle
        self.display.print_info("Tüm işçilerin tamamlanması")
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.display.print_info("Tüm işçiler tamamlandı.")
        # Kalan görevleri güncelle
        if self.tasks_to_update:
            try:
                while self.tasks_to_update:
                    batch = self.tasks_to_update[:self.sqlite_bulk_update_count]
                    self.sqlite_manager.bulk_update_tasks(batch)
                    self.tasks_to_update = self.tasks_to_update[self.sqlite_bulk_update_count:]
            except Exception as e:
                error_message = f"Toplu güncelleme başarısız oldu: {e}"
                self.logger.error(error_message)
                self.display.print_error(error_message)

        self.display_statistics()

        await self.rabbitmq.close_connection()  # RabbitMQ bağlantısını kapat


    async def perform_rdns_check_async(self, ip, dns):
        try:
            # IP adresini doğrula
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                return {"status": "invalid_ip", "result": "invalid_ip", "details": f"Invalid IP: {ip}"}

            # Reverse IP for PTR query
            query = f"{'.'.join(reversed(ip.split('.')))}.{dns}"

            # Görevin başlangıç zamanını kaydet
            start_time = time.time()

            # Perform actual DNS query
            resolver = Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            try:
                # 'A' kaydı için sorgu
                answers = resolver.resolve(query, "A")
                # 'TXT' kaydı için sorgu
                answer_txt = resolver.resolve(query, "TXT")

                # Görevin bitiş zamanını kaydet ve süreyi hesapla
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000  # Milisaniye cinsinden

                return {
                    "status": "completed",
                    "result": "listed",
                    "details": f"{answers[0]}: {answer_txt[0]} ({duration_ms:.3f} ms)"
                }
            except NXDOMAIN:
                # NXDOMAIN hata durumu için süre hesaplama
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {"status": "completed", "result": "not_listed", "details": f"Query completed in {duration_ms:.3f} ms"}
            except Timeout:
                # Timeout durumu için süre hesaplama
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {"status": "completed", "result": "timed_out", "details": f"Query timed out in {duration_ms:.3f} ms"}
            except NoAnswer:
                # NoAnswer durumu için süre hesaplama
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {"status": "completed", "result": "no_answer", "details": f"No answer in {duration_ms:.3f} ms"}
            except NoNameservers:
                # NoNameservers durumu için süre hesaplama
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {"status": "completed", "result": "no_nameservers", "details": f"No nameservers in {duration_ms:.3f} ms"}
            except Exception as e:
                # Genel hata durumu için süre hesaplama
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {"status": "dns_error", "result": "dns_error", "details": f"DNS error in {duration_ms:.3f} ms: {str(e)}"}

        except Exception as e:
            # Genel bir hata durumunda
            error_message = f"Failed to perform RDNS check: {e}"
            self.logger.error(error_message)
            self.display.print_error(error_message)
            return {"status": "exception", "result": "exception", "details": f"Exception: {str(e)}"}