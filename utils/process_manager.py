import json
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
from dns.resolver import NXDOMAIN, Timeout, NoAnswer, NoNameservers

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

    async def connect(self, prefetch_count):  # prefetch_count parametresi eklendi
        try:
            connection_string = f"amqp://{self.username}:{self.password}@{self.host}:5672//"
            self.connection = await aio_pika.connect_robust(connection_string)
            self.channel = await self.connection.channel()

            # Prefetch ayarı parametre ile yapılır
            await self.channel.set_qos(prefetch_count=prefetch_count)

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
    def __init__(self, worker_id, rabbitmq, process_task):
        self.worker_id = worker_id
        self.rabbitmq = rabbitmq
        self.process_task = process_task
        self.running = True  # Durdurma sinyali için bayrak

    def stop(self):
        """
        Worker'ı durdurma sinyali.
        """
        self.running = False

    async def run(self, queue_name):
        try:
            self.rabbitmq.logger.info(f"Worker {self.worker_id} başlatıldı ve kuyruğa bağlandı: {queue_name}")
            queue = await self.rabbitmq.channel.declare_queue(name=queue_name, durable=False)

            idle_count = 0  # İşlem yapılmayan ardışık döngü sayısı
            max_idle_count = 5  # İşlem yapılmayan maksimum döngü sayısı

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self.running:
                        break  # Worker durdurma sinyali

                    if queue.declaration_result.message_count == 0:  # Kuyrukta iş yok
                        idle_count += 1
                        if idle_count >= max_idle_count:
                            self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Kuyrukta iş kalmadı, sonlanıyor.")
                            return
                        await asyncio.sleep(1)  # Bekleme süresi
                        continue

                    # İşlem sıfırlama
                    idle_count = 0

                    async with message.process():
                        self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Mesaj işleniyor; Mesaj: {message.body}")
                        await self.process_task(message)
                        await asyncio.sleep(0.1)  # Mesaj işleme sonrası gecikme
                        self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Mesaj başarıyla işlendi.")

                self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Kuyruk boş, işlem tamam.")
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

        # Sinyal işleyicileri güncellendi
        signal.signal(signal.SIGINT, lambda s, f: asyncio.run(self.stop_workers()))
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.run(self.stop_workers()))

        self.stats = {
            "not_listed": 0,
            "listed": 0,
            "timed_out": 0,
            "no_answer": 0,
            "no_nameservers": 0,
            "dns_error": 0,
            "exception": 0
        }


    async def stop_workers(self):
        """
        Tüm worker'lara durdurma sinyali gönderir ve tamamlanmalarını bekler.
        """
        for worker in self.workers:
            worker.stop()  # Worker'ları durdur
        await asyncio.gather(*self.workers, return_exceptions=True)  # Worker'ların sonlanmasını bekle
        await asyncio.sleep(1)
        await self.rabbitmq.close_connection()  # RabbitMQ bağlantısını kapat
        self.display.print_info("Tüm işçiler ve bağlantılar durduruldu.")

    def display_statistics(self):
        elapsed_time = datetime.now() - self.start_time
        total_tasks = len(self.processed_tasks)

        self.display.print_info("=== Task Processing Statistics ===")
        self.display.print_info(f"Total Tasks Processed: {total_tasks}")
        self.display.print_info(f"Elapsed Time: {elapsed_time}")

        self.display.print_info("--- Task Results ---")
        for result, count in self.stats.items():
            ratio = (count / total_tasks) * 100 if total_tasks > 0 else 0
            self.display.print_info(f"{result.capitalize()}: {count} ({ratio:.2f}%)")

        if total_tasks > 0:
            avg_time_per_task = elapsed_time / total_tasks
            self.display.print_info(f"Average Time per Task: {avg_time_per_task}")
            self.display.print_info(f"Tasks per Second: {total_tasks / elapsed_time.total_seconds():.2f}")
        else:
            self.display.print_info("No tasks were processed.")

        self.display.print_info("=== End of Statistics ===")

    async def fetch_and_process_tasks(self, queue_name):
        """
        Görevleri RabbitMQ'dan alır ve işler.
        """
        await self.rabbitmq.connect(prefetch_count=min(self.concurrency_limit * 2, 100))  
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
                remaining_time = (elapsed_time / tasks_done) * (total_tasks - tasks_done) if tasks_done > 0 else timedelta(seconds=0)

                self.display.print_dns_status(
                    worker_id="Async",
                    tasks_done=tasks_done,
                    total_tasks=total_tasks,  # total_tasks_dynamic yerine total_tasks kullanılıyor
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
        try:
            await asyncio.gather(*self.workers, return_exceptions=True)
        except asyncio.TimeoutError:
            self.logger.error("Timeout: İşçiler belirtilen sürede tamamlanamadı!")
            self.display.print_error("Timeout: İşçiler belirtilen sürede tamamlanamadı!")
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

    async def perform_rdns_check_async(self, ip, dns):
        """
        Asenkron olarak ters DNS araması gerçekleştirir.

        Args:
            ip (str): IP adresi.
            dns (str): DNS sunucusu.

        Returns:
            dict: Aramasonuçlarını içeren bir sözlük.
        """
        try:
            # IP adresini doğrula
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                return {"status": "invalid_ip", "result": "invalid_ip", "details": f"Invalid IP: {ip}"}

            # PTR sorgusu için ters IP
            query = f"{'.'.join(reversed(ip.split('.')))}.{dns}"
            start_time = time.time()

            try:
                # 'A' ve 'TXT' kayıtları için asenkron sorgular
                answers = await self.resolver.query(query, "A")
                answer_txt = await self.resolver.query(query, "TXT")

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                return {
                    "status": "completed",
                    "result": "listed",
                    "details": f"{answers[0]}: {answer_txt[0]} ({duration_ms:.3f} ms)"
                }

            except (NXDOMAIN, Timeout, NoAnswer, NoNameservers, Exception) as e:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                if isinstance(e, NXDOMAIN):
                    result = "not_listed"  # Değiştirildi
                    details = f"Query completed in {duration_ms:.3f} ms"
                elif isinstance(e, Timeout):
                    result = "timed_out"
                    details = f"Query timed out in {duration_ms:.3f} ms"
                elif isinstance(e, NoAnswer):
                    result = "no_answer"
                    details = f"No answer in {duration_ms:.3f} ms"
                elif isinstance(e, NoNameservers):
                    result = "no_nameservers"
                    details = f"No nameservers in {duration_ms:.3f} ms"
                else:
                    result = "dns_error"
                    details = f"DNS error in {duration_ms:.3f} ms: {str(e)}"

                return {"status": "completed", "result": result, "details": details}

        except Exception as e:
            error_message = f"Failed to perform RDNS check: {e}"
            self.logger.error(error_message)
            self.display.print_error(error_message)
            return {"status": "exception", "result": "exception", "details": f"Exception: {str(e)}"}