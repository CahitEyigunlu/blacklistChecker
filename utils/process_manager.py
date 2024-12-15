import asyncio
import aiodns
import json
from datetime import datetime, timedelta
from dns.resolver import Resolver, NXDOMAIN, Timeout, NoAnswer, NoNameservers
from logB.logger import Logger
from utils.display import Display
import signal
import random
import ipaddress
from aiodns import DNSResolver
import time


class Worker:
    """Represents a single worker that processes tasks from RabbitMQ."""

    def __init__(self, worker_id, rabbitmq, process_task):
        self.worker_id = worker_id
        self.rabbitmq = rabbitmq
        self.process_task = process_task
        self.running = True

    async def run(self, queue_name):
        """Continuously fetch and process tasks until no more tasks are available."""
        while self.running:
            await asyncio.sleep(random.uniform(0, 0.1))
            try:
                method_frame, properties, body = self.rabbitmq.channel.basic_get(
                    queue=queue_name, auto_ack=False
                )

                if body:
                    delivery_tag = method_frame.delivery_tag
                    await self.process_task(body, delivery_tag, self.worker_id)
                else:
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_message = f"Worker{self.worker_id} encountered an error: {e}"
                Logger().error(error_message)
                Display().print_error(error_message)


class ProcessManager:
    """Manages the processing of tasks from RabbitMQ."""

    def __init__(self, rabbitmq, sqlite_manager, config):
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.config = config
        self.logger = Logger(log_file_path=config["logging"]["error_log_path"])
        self.display = Display()
        self.processed_tasks = []
        self.workers = []
        self.start_time = datetime.now()
        self.concurrency_limit = config.get("concurrency_limit", 200)
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
        Display statistics about the processed tasks.
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
        """Handles termination signals to gracefully stop workers."""
        for worker in self.workers:
            worker.cancel()

    async def fetch_and_process_tasks(self, queue_name):
        queue_state = self.rabbitmq.channel.queue_declare(queue=queue_name, passive=True)
        total_tasks = queue_state.method.message_count
        print(f"[DEBUG] Total tasks in queue '{queue_name}': {total_tasks}")

        async def process_task(task_body, delivery_tag, worker_id):
            try:
                task = json.loads(task_body)
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
                    worker_id=worker_id,
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

                self.rabbitmq.channel.basic_ack(delivery_tag=delivery_tag)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                error_message = f"Worker {worker_id} failed to process task: {e}"
                self.logger.error(error_message)
                self.display.print_error(error_message)

        self.workers = [
            asyncio.create_task(
                Worker(i + 1, self.rabbitmq, process_task).run(queue_name)
            )
            for i in range(self.concurrency_limit)
        ]

        # Tüm worker'ları bekle
        await asyncio.gather(*self.workers, return_exceptions=True)

        # Son kalan işlemleri güncelle
        if self.tasks_to_update:
            try:
                while self.tasks_to_update:
                    batch = self.tasks_to_update[:self.sqlite_bulk_update_count]
                    self.sqlite_manager.bulk_update_tasks(batch)
                    self.tasks_to_update = self.tasks_to_update[self.sqlite_bulk_update_count:]
            except Exception as e:
                error_message = f"Final bulk update failed in chunks: {e}"
                self.logger.error(error_message)
                self.display.print_error(error_message)

        self.display_statistics()

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



    async def perform_rdns_check_async2(self, ip, dns):
        """
        Perform an asynchronous PTR query with reverse IP and check DNSBL listing.
        Cache the unique DNS resolver results for the blacklist.
        """
        try:

            # Perform the actual DNSBL query
            query = f"{'.'.join(reversed(ip.split('.')))}.{dns}"

            resolver = Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            try:
                # Perform DNS queries
                answers = resolver.query(query, "A")
                answer_txt = resolver.query(query, "TXT")
                return {
                    "status": "blacklisted",
                    "result": "blacklisted",
                    "details": f"{answers[0]}: {answer_txt[0]}"
                }
            except NXDOMAIN:
                return {"status": "completed", "result": "not_listed"}
            except Timeout:
                return {"status": "completed", "result": "timed_out"}
            except NoAnswer:
                return {"status": "completed", "result": "no_answer"}
            except NoNameservers:
                return {"status": "completed", "result": "no_nameservers"}
            except Exception as e:
                return {"status": "dns_error", "result": "dns_error", "message": str(e)}

        except Exception as e:
            error_message = f"Failed to perform RDNS check: {e}"
            self.logger.error(error_message)
            self.display.print_error(error_message)
            return {"status": "exception", "result": "exception", "message": str(e)}
