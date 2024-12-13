import asyncio
import json
from asyncio import Semaphore
from aio_pika import connect_robust, Message, DeliveryMode
from utils.display import Display
from logB.logger import Logger
from datetime import datetime

class TaskProcessor:
    def __init__(self, config, sqlite_manager):
        """
        Initializes the TaskProcessor.

        Args:
            config: Configuration dictionary.
            sqlite_manager: SQLite manager instance.
        """
        self.config = config
        self.sqlite_manager = sqlite_manager
        self.batch_size = config['rabbitmq']['batch_size']
        self.update_threshold = config['rabbitmq']['update_threshold']
        self.semaphore = Semaphore(config['rabbitmq']['max_workers'])
        self.queue_name = config['rabbitmq']['default_queue']
        self.processed_tasks = []
        self.running_tasks = set()
        self.display = Display()
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.error_logger = Logger(log_file_path=config['logging']['error_log_path'])
        self.connection = None
        self.channel = None
        self.last_update_time = None  # En son güncelleme zamanı


    async def connect(self):
        """
        Establishes the RabbitMQ connection and initializes the channel.
        """
        try:
            self.connection = await connect_robust(self.config['rabbitmq']['url'])
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=self.batch_size)
            self.display.print_success("Connected to RabbitMQ successfully.")
        except Exception as e:
            error_message = f"Error connecting to RabbitMQ: {e}"
            self.error_logger.error(error_message, extra={"function": "connect", "file": "task_processor.py"})
            self.display.print_error(f"❌ {error_message}")
            raise

    async def close_connection(self):
        """
        Closes the RabbitMQ connection gracefully.
        """
        if self.connection:
            await self.connection.close()
            self.display.print_success("RabbitMQ connection closed.")


    async def publish_task(self, task):
        """
        Publishes a task to RabbitMQ queue.
        """
        try:
            await self.channel.default_exchange.publish(
                Message(
                    body=json.dumps(task).encode(),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                routing_key=self.queue_name,
            )
            #self.logger.info(f"Published task: {task}")
        except Exception as e:
            error_message = f"Error publishing task: {e}"
            self.error_logger.error(error_message, extra={"function": "publish_task", "file": "task_processor.py"})
            self.display.print_error(f"❌ {error_message}")

    async def process_task(self, delivery_tag, task):
        """
        Processes a single task.
        """
        async with self.semaphore:
            try:
                self.display.print_info(f"Processing task: {task}")
                self.processed_tasks.append(task)

                # Trigger database update if threshold is met
                if len(self.processed_tasks) >= self.update_threshold:
                    asyncio.create_task(self.update_database())  # Arka plan görevi
            except Exception as e:
                error_message = f"Error processing task: {e}"
                self.error_logger.error(error_message, extra={"function": "process_task", "file": "task_processor.py", "task": task})
                self.display.print_error(f"❌ {error_message}")


    async def update_database(self):
        """
        Updates the SQLite database with the processed tasks and calculates the time 
        elapsed since the last update.
        """
        try:
            if not self.processed_tasks:
                return

            current_time = datetime.now()
            time_since_last_update = current_time - self.last_update_time if self.last_update_time else 0

            await self.sqlite_manager.bulk_update_tasks(self.processed_tasks)
            self.last_update_time = current_time

            log_message = f"Updated {len(self.processed_tasks)} tasks in SQLite."
            log_message += f" Time since last update: {time_since_last_update}"
            self.logger.info(log_message)
            self.display.print_success(f"✔️ {log_message}")

            self.processed_tasks = []  # Clear the processed tasks list
        except Exception as e:
            error_message = f"Error updating database: {e}"
            self.error_logger.error(error_message, extra={"function": "update_database", "file": "task_processor.py"})
            self.display.print_error(f"❌ {error_message}")

    async def fetch_tasks_batch(self):
        """
        Fetches a batch of tasks from RabbitMQ.
        """
        tasks = []
        try:
            queue = await self.channel.declare_queue(self.queue_name, durable=True)
            for _ in range(self.batch_size):
                message = await queue.get()
                if message:
                    async with message.process():
                        task = json.loads(message.body.decode('utf-8'))
                        tasks.append((message.delivery_tag, task))
                else:
                    break
        except Exception as e:
            error_message = f"Error fetching batch tasks: {e}"
            self.error_logger.error(error_message, extra={"function": "fetch_tasks_batch", "file": "task_processor.py"})
            self.display.print_error(f"❌ {error_message}")
        return tasks

    async def run(self):
        """
        Main task processing loop.
        """
        self.display.print_info(f"Starting TaskProcessor with batch size {self.batch_size}...")

        await self.connect()
        try:
            while True:
                tasks = await self.fetch_tasks_batch()
                if not tasks:
                    await asyncio.sleep(1)  # Kuyruk boşsa 1 saniye bekle
                    continue

                coroutines = [self.process_task(delivery_tag, task) for delivery_tag, task in tasks]
                await asyncio.gather(*coroutines)  # Görevleri paralel olarak çalıştır

        except Exception as e:
            error_message = f"Error in main loop: {e}"
            self.error_logger.error(error_message, extra={"function": "run", "file": "task_processor.py"})
            self.display.print_error(f"❌ {error_message}")
        finally:
            await self.close_connection()