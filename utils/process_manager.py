import json
import time
import signal
import aiodns
import asyncio
import aio_pika
import ipaddress
from aiodns import DNSResolver
from functools import partial
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
        

    async def connect(self, prefetch_count):
        try:
            connection_string = f"amqp://{self.username}:{self.password}@{self.host}:5672//"
            self.connection = await aio_pika.connect_robust(connection_string)
            self.channel = await self.connection.channel()

            # Prefetch ayarı parametre ile yapılır
            await self.channel.set_qos(prefetch_count=prefetch_count)

            try:
                await self.channel.declare_queue(name=self.queue_name, passive=True)
            except aio_pika.exceptions.ChannelPreconditionFailed:
                self.display.print_error(f"Kuyruk özellikleri uyumsuz: {self.queue_name}")  # Log yerine display.print_error
                raise

            self.display.print_success("✔️ RabbitMQ sunucusuna başarıyla bağlanıldı.")  # Log yerine display.print_success
        except Exception as e:
            self.display.print_error(f"RabbitMQ bağlantı hatası: {e}")  # Log yerine display.print_error
            raise

    async def close_connection(self):
        """
        RabbitMQ bağlantısını asenkron olarak kapatır.
        """
        try:
            if self.connection:
                await self.connection.close()
                self.display.print_success("✔️ RabbitMQ bağlantısı kapatıldı.")  # Log yerine display.print_success
        except Exception as e:
            self.display.print_error(f"RabbitMQ bağlantı kapatma hatası: {e}")  # Log yerine display.print_error
            raise

class Worker:
    def __init__(self, worker_id, rabbitmq, process_task, task_tracker_lock):
        self.worker_id = worker_id
        self.rabbitmq = rabbitmq
        self.process_task = process_task
        self.running = True
        self.last_task_time = datetime.now()
        self.task_tracker_lock = task_tracker_lock

    def stop(self):
        """
        Worker'ı durdurma sinyali.
        """
        self.running = False

    async def run(self, queue_name, task_tracker):
        try:
            self.rabbitmq.display.print_info(f"Worker {self.worker_id} başlatıldı ve kuyruğa bağlandı: {queue_name}")
            queue = await self.rabbitmq.channel.declare_queue(name=queue_name, durable=False)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    if not self.running:
                        self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Durduruldu.")
                        break

                    task_processed = False
                    async with message.process():
                        self.last_task_time = datetime.now()
                        try:
                            await asyncio.wait_for(self.process_task(message), timeout=60)
                            task_processed = True
                        except asyncio.TimeoutError:
                            self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Görev zaman aşımına uğradı.")
                            continue
                        except Exception as e:
                            self.rabbitmq.display.print_error(f"Worker {self.worker_id}: Görev işlenirken hata oluştu: {e}")
                            continue

                    if task_processed:
                        async with self.task_tracker_lock:
                            is_last_task = task_tracker["tasks_done"] >= task_tracker["total_tasks"]  # Kilidi erken bırakmak için

                        if is_last_task:  # Kilit dışında kontrol et
                            self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Tüm işler tamamlandı. Diğer worker'lar durduruluyor.")
                            await self.rabbitmq.process_manager.stop_workers()
                            break

            self.rabbitmq.display.print_info(f"Worker {self.worker_id}: Kuyrukta iş kalmadı veya tüm görevler tamamlandı.")
        except asyncio.CancelledError:
            self.rabbitmq.display.print_info(f"Worker {self.worker_id} iptal edildi.")
        except Exception as e:
            error_message = f"Worker {self.worker_id} başlatılırken bir hata oluştu: {e}"
            self.rabbitmq.display.print_error(error_message)  # Log yerine display.print_error

class ProcessManager:
    def __init__(self, sqlite_manager, config):
        self.rabbitmq = AsyncRabbitMQ(config)
        self.sqlite_manager = sqlite_manager
        self.config = config
        self.logger = Logger(log_file_path=config["logging"]["error_log_path"])
        self.display = Display()
        self.processed_tasks = []
        self.workers = []
        self.worker_tasks = []  # Worker görevlerini saklamak için
        self.start_time = datetime.now()
        self.concurrency_limit = config["rabbitmq"].get("RABBITMQ_CONCURRENCY_LIMIT", 50)
        self.sqlite_bulk_update_count = config["sqlite"].get("bulk_update_count", 500)
        self.tasks_to_update = []
        self.resolver = aiodns.DNSResolver()
        self.task_tracker_lock = asyncio.Lock()

        # RabbitMQ'ya ProcessManager referansını ekle
        self.rabbitmq.process_manager = self

        # Event loop'u al
        self.loop = asyncio.get_event_loop()

        # Sinyal işleyicilerini event loop'una ekle# Sinyal işleyicilerini tanımla
        signal.signal(signal.SIGINT, self.handle_stop_signal)
        signal.signal(signal.SIGTERM, self.handle_stop_signal)

        self.stats = {
            "not_listed": 0,
            "listed": 0,
            "timed_out": 0,
            "no_answer": 0,
            "no_nameservers": 0,
            "dns_error": 0,
            "exception": 0
        }

    def handle_stop_signal(self, signum, frame):
        """
        Sinyal alındığında tüm worker'ları durdurur ve event loop'u sonlandırır.
        """
        self.display.print_info(f"Sinyal alındı: {signum}. Tüm worker'lar durdurulacak.")
        
        # Tüm işçileri durdurmayı asenkron olarak başlat
        asyncio.create_task(self.stop_workers())

    async def ensure_stopped_workers(self, check_interval=0.1, timeout=5.0):
        """
        Tüm işçilerin durduğundan emin olur. Durmamış işçileri kontrol eder ve loglar.
        
        Args:
            check_interval (float): İşçi durumlarını kontrol etme aralığı (saniye).
            timeout (float): İşçilerin durması için maksimum bekleme süresi (saniye).
        """
        try:
            start_time = time.time()
            while True:
                # Çalışmaya devam eden işçileri kontrol et
                active_workers = [worker for worker in self.workers if worker.running]

                # Eğer tüm işçiler durmuşsa, döngüden çık
                if not active_workers:
                    break

                # Maksimum bekleme süresini aşarsa, kalan işçileri logla ve çık
                if time.time() - start_time > timeout:
                    self.display.print_warning(f"Durmamış işçiler: {[worker.worker_id for worker in active_workers]}")  # Log yerine display.print_warning
                    break

                # Belirli bir süre bekle ve tekrar kontrol et
                await asyncio.sleep(check_interval)

            # Eğer hala çalışan işçiler varsa, logla
            if active_workers:
                self.display.print_error(f"Durdurulamayan işçiler: {[worker.worker_id for worker in active_workers]}")  # Log yerine display.print_error
            else:
                self.display.print_success("Tüm işçiler başarıyla durduruldu.")  # Log yerine display.print_success
        except asyncio.CancelledError:
            self.display.print_info("ensure_stopped_workers iptal edildi.")

    async def stop_workers(self):
        """
        Tüm worker'lara durdurma sinyali gönderir ve görevlerini iptal eder.
        """
        try:
            for worker in self.workers:
                worker.stop()
                self.display.print_info(f"Worker {worker.worker_id} durduruldu.")
            
            # Worker görevlerini iptal et
            for task in self.worker_tasks:
                task.cancel()
            
            # İptal edilen görevlerin tamamlanmasını bekle (shield ile koruyarak)
            await asyncio.shield(asyncio.gather(*self.worker_tasks, return_exceptions=True))

            active_workers = [worker for worker in self.workers if worker.running]
            self.display.print_info(f"Aktif işçiler: {[worker.worker_id for worker in active_workers]}")
            self.display.print_info("Tüm işçiler durduruldu.")
        except asyncio.CancelledError:
            self.display.print_info("stop_workers iptal edildi.")

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
                    result = "not_listed"
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
            self.display.print_error(error_message)  # Log yerine display.print_error
            return {"status": "exception", "result": "exception", "details": f"Exception: {str(e)}"}

    async def fetch_and_process_tasks(self, queue_name):
        """
        Görevleri RabbitMQ'dan alır ve işler.
        """
        try:
            await self.rabbitmq.connect(prefetch_count=min(self.concurrency_limit * 2, 100))
            queue_state = await self.rabbitmq.channel.declare_queue(name=queue_name, passive=True)
            total_tasks = max(queue_state.declaration_result.message_count, 1) 
            self.display.print_success(f"Total tasks in the queue: {total_tasks}")

            # Görev sayısını kontrol et
            if total_tasks <= 1:
                self.display.print_info(f"Kuyrukta yalnızca {total_tasks} görev bulundu. İşçiler çalıştırılmadan işlem tamamlanacak.")
                
                # RabbitMQ bağlantısını kapat
                await self.rabbitmq.close_connection()

                # Fonksiyondan çık
                return

            # Görev takipçi
            task_tracker = {"tasks_done": 0, "total_tasks": total_tasks}  # tasks_done başlangıçta 0 olmalı

            async def process_task(message, worker_id):
                try:
                    # Mesajı çöz
                    task = json.loads(message.body)
                    ip = task["ip"]
                    dns = task["dns"]

                    # Ters DNS kontrolünü gerçekleştir
                    result = await self.perform_rdns_check_async(ip, dns)

                    # Görevi güncelle
                    task.update({
                        "result": result["result"],
                        "status": result["status"],
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    })

                    # İşlenen görevi güncelleme kuyruğuna ekle
                    self.processed_tasks.append(task)
                    self.tasks_to_update.append(task)
                    self.stats[result["result"]] += 1

                    # Güncelleme sınırına ulaşıldıysa veritabanını güncelle
                    if len(self.tasks_to_update) >= self.sqlite_bulk_update_count:
                        self.display.print_info("Kilit alınmaya çalışılıyor...")  # Kilit almadan önce log ekle
                        async with self.task_tracker_lock:  # Güncellemeyi güvence altına alın
                            self.display.print_info("Kilit başarıyla alındı.")  # Kilit aldıktan sonra log ekle
                            batch = self.tasks_to_update[:self.sqlite_bulk_update_count]
                            try:
                                self.sqlite_manager.bulk_update_tasks(batch)
                                del self.tasks_to_update[:self.sqlite_bulk_update_count]
                                self.display.print_info(f"{len(batch)} görev güncellendi.")
                            except Exception as e:
                                self.display.print_error(f"SQLite güncelleme sırasında hata: {e}")  # Log yerine display.print_error

                    # İşlenmiş görev sayacını artır
                    async with self.task_tracker_lock:  # task_tracker güncellemesi kilit altında
                        task_tracker["tasks_done"] += 1
                        is_last_task = task_tracker["tasks_done"] >= task_tracker["total_tasks"]  # Kilidi erken bırakmak için

                    elapsed_time = datetime.now() - self.start_time
                    tasks_done = task_tracker["tasks_done"]  # Güncel tasks_done değerini kullan
                    remaining_time = (elapsed_time / tasks_done) * (total_tasks - tasks_done) if tasks_done > 0 else timedelta(seconds=0)

                    self.display.print_dns_status(
                        worker_id=worker_id,
                        tasks_done=tasks_done,  # Güncel tasks_done değerini kullan
                        total_tasks=total_tasks, 
                        elapsed_time=elapsed_time,
                        remaining_time=remaining_time,
                        ip=ip,
                        dns=dns,
                        result=result["result"],
                        status=result["status"],
                        details=result.get("details", None)
                    )

                    if is_last_task:  # Kilit dışında kontrol et
                        self.display.print_info(f"Worker {worker_id}: Tüm işler tamamlandı. Diğer worker'lar durduruluyor.")
                        await self.stop_workers()  # stop_workers'ı çağır

                except Exception as e:
                    error_message = f"Görev işlenirken bir hata oluştu: {e}"
                    self.display.print_error(error_message)  # Log yerine display.print_error

            # Worker nesnelerini oluştur
            from functools import partial
            self.workers = [
                Worker(
                    worker_id=i + 1,
                    rabbitmq=self.rabbitmq,
                    process_task=partial(process_task, worker_id=i + 1),  # worker_id'yi sabitle
                    task_tracker_lock=self.task_tracker_lock
                )
                for i in range(self.concurrency_limit)
            ]

            # Worker'ların `run` metodunu `asyncio.create_task` ile başlat ve görevleri sakla
            self.worker_tasks = [
                asyncio.create_task(worker.run(queue_name, task_tracker))
                for worker in self.workers
            ]

            # Tüm görevlerin tamamlanmasını bekle
            self.display.print_info("Tüm işçilerin tamamlanması bekleniyor...")
            try:
                await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            except asyncio.CancelledError:
                self.display.print_info("fetch_and_process_tasks iptal edildi.")

            # Tüm işçilerin durduğundan emin ol
            await self.ensure_stopped_workers()

            # RabbitMQ kuyruğunda iş kalmadığından emin ol
            queue_state = await self.rabbitmq.channel.declare_queue(name=self.rabbitmq.queue_name, passive=True)
            if queue_state.declaration_result.message_count > 0:
                self.display.print_warning("Kuyrukta hala bekleyen işler var, ancak tüm işçiler durduruldu.")  # Log yerine display.print_warning

            # Kalan görevleri güncelle
            self.display.print_info(f"Güncelleme için bekleyen görev sayısı: {len(self.tasks_to_update)}")
            if self.tasks_to_update:
                try:
                    while self.tasks_to_update:
                        batch = self.tasks_to_update[:self.sqlite_bulk_update_count]
                        self.display.print_info(f"Güncellenen görev sayısı: {len(batch)}")
                        self.sqlite_manager.bulk_update_tasks(batch)
                        self.tasks_to_update = self.tasks_to_update[self.sqlite_bulk_update_count:]
                except Exception as e:
                    error_message = f"Toplu güncelleme başarısız oldu: {e}"
                    self.display.print_error(error_message)  # Log yerine display.print_error

            self.display_statistics()
        finally:  # Her zaman bağlantıyı kapat
            await self.rabbitmq.close_connection()  # RabbitMQ bağlantısını kapat