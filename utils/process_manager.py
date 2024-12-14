import asyncio
import aiodns
import json
from datetime import datetime
from dns.resolver import Resolver, NXDOMAIN, Timeout, NoAnswer, NoNameservers
from logB.logger import Logger
from utils.display import Display
import signal
import random
import ipaddress


class Worker:
    """Represents a single worker that processes tasks from RabbitMQ."""

    def __init__(self, worker_id, rabbitmq, config, display, logger, process_task):
        self.worker_id = worker_id
        self.rabbitmq = rabbitmq
        self.config = config
        self.display = display
        self.logger = logger
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
                    await asyncio.sleep(0.2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_message = f"Worker{self.worker_id} encountered an error: {e}"
                self.logger.error(error_message)


class ProcessManager:
    """Manages the processing of tasks from RabbitMQ."""

    def __init__(self, rabbitmq, sqlite_manager, config):
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.config = config
        self.logger = Logger(log_file_path=config["logging"]["error_log_path"])
        self.display = Display()
        self.processed_tasks = []
        self.running = True
        self.workers = []
        self.concurrency_limit = self.config.get("concurrency_limit", 5)
        self.active_tasks = 0
        self.dns_cache = {}
        self.sqlite_bulk_update_count = self.config["sqlite"].get("bulk_update_count", 100)
        self.tasks_to_update = []
        self.resolver = aiodns.DNSResolver()
        self.total_tasks_lock = asyncio.Lock()  # Kilitleme mekanizması ekle

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

    def signal_handler(self, sig, frame):
        """Handles termination signals to gracefully stop workers."""

        self.running = False
        for worker in self.workers:
            worker.cancel()

    async def fetch_and_process_tasks(self, queue_name):
            """
            Fetch tasks from RabbitMQ and process them asynchronously with concurrency limit.
            """

            queue_state = self.rabbitmq.channel.queue_declare(queue=queue_name, passive=True)
            total_tasks = queue_state.method.message_count

            # asyncio.Queue kullanarak görevleri worker'lara dağıt
            task_queue = asyncio.Queue()
            for _ in range(total_tasks):
                method_frame, properties, body = self.rabbitmq.channel.basic_get(
                    queue=queue_name, auto_ack=False
                )
                await task_queue.put((method_frame, properties, body))

            async def process_task(worker_id):
                """Process a single task from the queue."""
                while True:
                    try:
                        method_frame, properties, body = await task_queue.get()
                        
                        # Kuyrukta görev yoksa devam et
                        if method_frame is None:
                            task_queue.task_done()
                            break

                        try:
                            task = json.loads(body)
                            ip = task["ip"]
                            dns = task["dns"]

                            result = await self.perform_rdns_check_async(ip, dns)

                            task["result"] = result["result"]
                            task["status"] = result["status"]
                            task["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            self.processed_tasks.append(task)
                            self.tasks_to_update.append(task)

                            self.stats[result["status"]] += 1

                            self.display.print_success(
                                f"(Worker {worker_id} - {len(self.processed_tasks)}/{total_tasks}) ✅ {ip} is not listed in {dns}"
                            )

                            if len(self.tasks_to_update) >= self.sqlite_bulk_update_count:
                                self.sqlite_manager.bulk_update_tasks(self.tasks_to_update[:self.sqlite_bulk_update_count])
                                self.tasks_to_update = self.tasks_to_update[self.sqlite_bulk_update_count:]

                            self.rabbitmq.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

                        except Exception as e:
                            error_message = f"Worker{worker_id} failed to process task: {e}"
                            self.logger.error(error_message)
                            # Hatalı görevi tekrar kuyruğa ekle
                            await task_queue.put((method_frame, properties, body))

                    except asyncio.CancelledError:
                        break
                    finally:
                        task_queue.task_done()

            self.workers = [
                asyncio.create_task(process_task(i + 1))
                for i in range(self.concurrency_limit)
            ]

            await task_queue.join()  # Tüm görevlerin tamamlanmasını bekle

            # Kalan görevleri güncelle ve istatistikleri göster
            if self.tasks_to_update:
                self.sqlite_manager.bulk_update_tasks(self.tasks_to_update)

            self.display.print_info(f"All tasks completed. Total responses: {len(self.processed_tasks)}")
            self.display_statistics()

    def reverse_ip(self, ip):
        """Reverse an IPv4 or IPv6 address for a PTR query."""
        try:
            addr = ipaddress.ip_address(ip)
            if addr.version == 4:
                return f"{'.'.join(reversed(ip.split('.')))}.in-addr.arpa"
            elif addr.version == 6:
                expanded = addr.exploded.replace(':', '')
                reversed_ip = '.'.join(reversed(expanded))
                return f"{reversed_ip}.ip6.arpa"
        except ValueError:
            raise ValueError(f"Invalid IP address: {ip}")

    async def perform_rdns_check_async(self, ip, dns):
        """Perform an asynchronous PTR query with reverse IP and check DNSBL listing."""
        try:
            query = '.'.join(reversed(ip.split('.'))) + '.' + dns

            resolver = Resolver()
            resolver.timeout = 5
            resolver.lifetime = 5

            try:
                answers = resolver.query(query, "A")
                answer_txt = resolver.query(query, "TXT")
                result = {
                    "status": "listed",
                    "result": "listed",
                    "details": f"{answers[0]}: {answer_txt[0]}"
                }
                self.display.print_error(f"✅ {ip} is listed in {dns} ({answers[0]}: {answer_txt[0]})")
            except NXDOMAIN:
                result = {
                    "status": "not_listed",
                    "result": "not_listed"
                }
                self.display.print_success(f"✅ {ip} is not listed in {dns}")
            except Timeout:
                result = {
                    "status": "timed_out",
                    "result": "timed_out",
                    "message": f"Timeout while querying {dns}"
                }
                self.display.print_warning(f"⚠️ Timeout while querying {dns} ({ip})")
            except NoAnswer:
                result = {
                    "status": "no_answer",
                    "result": "no_answer",
                    "message": f"No answer from {dns}"
                }
                self.display.print_warning(f"⚠️ No answer from {dns} ({ip})")
            except NoNameservers:
                result = {
                    "status": "no_nameservers",
                    "result": "no_nameservers",
                    "message": f"No nameservers for {dns}"
                }
                self.display.print_warning(f"⚠️ No nameservers for {dns} ({ip})")
            except Exception as e:
                result = {
                    "status": "dns_error",
                    "result": "dns_error",
                    "message": str(e)
                }
                self.display.print_error(f"❌ Error querying {dns}: {e} ({ip})")

            return result

        except Exception as e:
            error_message = f"Failed to perform RDNS check for {dns}: {e}"
            self.logger.error(error_message)
            self.display.print_error(f"❌ {error_message}")
            return {
                "status": "exception",
                "result": "exception",
                "message": str(e)
            }

    def display_statistics(self):
        """Displays the statistics of the processed tasks in a table format."""
        self.display.print_info("Statistics:")
        self.display.print_info("----------------------")
        self.display.print_info(f"Not Listed: {self.stats['not_listed']}")
        self.display.print_info(f"Listed: {self.stats['listed']}")
        self.display.print_info(f"Timed Out: {self.stats['timed_out']}")
        self.display.print_info(f"No Answer: {self.stats['no_answer']}")
        self.display.print_info(f"No Nameservers: {self.stats['no_nameservers']}")
        self.display.print_info(f"DNS Error: {self.stats['dns_error']}")
        self.display.print_info(f"Exception: {self.stats['exception']}")
        self.display.print_info("----------------------")