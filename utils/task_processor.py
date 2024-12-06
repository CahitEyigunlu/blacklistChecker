import asyncio
import json
from utils.display import Display
from logB.logger import Logger

class TaskProcessor:
    def __init__(self, rabbitmq, sqlite_manager, batch_size=10):
        """
        Initializes the TaskProcessor.

        Args:
            rabbitmq: RabbitMQ instance.
            sqlite_manager: SQLite manager instance.
            batch_size (int): Number of tasks to fetch and process in parallel.
        """
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.batch_size = batch_size
        self.display = Display()
        self.logger = Logger(log_file_path="logs/task_processor.log")

    async def fetch_tasks(self, queue_name):
        """
        Fetches tasks from RabbitMQ queue.

        Args:
            queue_name (str): RabbitMQ queue name.

        Returns:
            list: A list of tasks fetched from RabbitMQ.
        """
        tasks = []
        for _ in range(self.batch_size):
            method_frame, _, body = self.rabbitmq.channel.basic_get(queue=queue_name, auto_ack=False)
            if method_frame:
                task = json.loads(body.decode('utf-8'))
                tasks.append((method_frame.delivery_tag, task))
            else:
                break
        return tasks

    async def process_task(self, delivery_tag, task):
        """
        Processes a single task.

        Args:
            delivery_tag: RabbitMQ delivery tag for acking the message.
            task (dict): The task to process.
        """
        try:
            # Simulate task processing
            self.display.print_info(f"Processing task: {task}")
            await asyncio.sleep(0.5)  # Simulate task delay

            # Mark task as completed in SQLite
            self.sqlite_manager.update_task_status(
                ip=task["ip"],
                dns=task["dns"],
                status="completed"
            )

            # Acknowledge task completion
            self.rabbitmq.channel.basic_ack(delivery_tag)
            self.logger.info(f"Processed and acknowledged task: {task}")

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            self.rabbitmq.channel.basic_nack(delivery_tag)

    async def run(self, queue_name):
        """
        Runs the task processing loop.

        Args:
            queue_name (str): RabbitMQ queue name.
        """
        self.display.print_info(f"Starting TaskProcessor with batch size {self.batch_size}...")

        while True:
            tasks = await self.fetch_tasks(queue_name)

            if not tasks:
                self.display.print_info("No tasks in queue. Waiting...")
                await asyncio.sleep(5)
                continue

            # Process tasks in parallel
            await asyncio.gather(*(self.process_task(tag, task) for tag, task in tasks))

            self.display.print_success(f"✔️ Processed {len(tasks)} tasks.")
