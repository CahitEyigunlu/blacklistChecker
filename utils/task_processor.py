import asyncio
import json
from utils.display import Display
from logB.logger import Logger


class TaskProcessor:
    def __init__(self, rabbitmq, sqlite_manager, batch_size=10, update_threshold=100):
        """
        Initializes the TaskProcessor.

        Args:
            rabbitmq: RabbitMQ instance.
            sqlite_manager: SQLite manager instance.
            batch_size (int): Number of tasks to fetch at once from RabbitMQ.
            update_threshold (int): Number of tasks to process before a SQLite update.
        """
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.batch_size = batch_size
        self.update_threshold = update_threshold
        self.processed_tasks = []
        self.logger = Logger(log_file_path="logs/task_processor.log")
        self.display = Display()

    async def fetch_tasks(self, queue_name):
        """
        Fetches a batch of tasks from RabbitMQ.

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
        self.logger.info(f"Fetched {len(tasks)} tasks from RabbitMQ queue '{queue_name}'.")
        return tasks

    async def process_task(self, delivery_tag, task, queue_name):
        """
        Processes a single task.

        Args:
            delivery_tag: RabbitMQ delivery tag for acking the message.
            task (dict): The task to process.
            queue_name (str): RabbitMQ queue name.
        """
        try:
            # Simulate task processing (e.g., network request or computation)
            await asyncio.sleep(0.1)  # Simulated delay
            self.processed_tasks.append(task)

            # Acknowledge task completion
            self.rabbitmq.channel.basic_ack(delivery_tag)
            self.logger.info(f"Processed and acknowledged task: {task}")
        except Exception as e:
            self.logger.error(f"Failed to process task: {e}")
            self.rabbitmq.channel.basic_nack(delivery_tag)

    async def update_database(self):
        """
        Updates SQLite with the processed tasks.
        """
        try:
            self.sqlite_manager.bulk_update_tasks(self.processed_tasks)
            self.logger.info(f"Updated {len(self.processed_tasks)} tasks in SQLite.")
            self.display.print_success(f"✔️ Updated {len(self.processed_tasks)} tasks in SQLite.")
            self.processed_tasks = []  # Clear the processed tasks
        except Exception as e:
            self.logger.error(f"Failed to update database: {e}")

    async def run(self, queue_name):
        """
        Main loop to fetch, process, and update tasks.

        Args:
            queue_name (str): RabbitMQ queue name.
        """
        self.display.print_info("Starting task processor...")
        while True:
            tasks = await self.fetch_tasks(queue_name)
            if not tasks:
                self.display.print_info("No tasks fetched. Sleeping...")
                await asyncio.sleep(5)
                continue

            # Process tasks concurrently
            await asyncio.gather(
                *(self.process_task(tag, task, queue_name) for tag, task in tasks)
            )

            # Update database if threshold reached
            if len(self.processed_tasks) >= self.update_threshold:
                await self.update_database()
