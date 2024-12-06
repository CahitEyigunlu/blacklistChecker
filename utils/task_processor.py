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
            batch_size (int): Number of tasks to fetch in parallel.
            update_threshold (int): Number of tasks before bulk SQLite update.
        """
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.batch_size = batch_size
        self.update_threshold = update_threshold
        self.processed_tasks = []
        self.running_tasks = set()  # Track running asyncio tasks
        self.display = Display()
        self.logger = Logger(log_file_path="logs/task_processor.log")

    async def fetch_task(self, queue_name):
        """
        Fetches a single task from RabbitMQ.

        Args:
            queue_name (str): RabbitMQ queue name.

        Returns:
            tuple: A tuple containing delivery_tag and task data.
        """
        try:
            method_frame, _, body = self.rabbitmq.channel.basic_get(queue=queue_name, auto_ack=False)
            if method_frame:
                task = json.loads(body.decode('utf-8'))
                return method_frame.delivery_tag, task
        except Exception as e:
            self.logger.error(f"Error fetching task: {e}")
        return None, None

    async def process_task(self, delivery_tag, task):
        """
        Processes a single task and acknowledges it.

        Args:
            delivery_tag: RabbitMQ delivery tag for acking the message.
            task (dict): The task data.
        """
        try:
            self.display.print_info(f"Processing task: {task}")
            await asyncio.sleep(0.5)  # Simulate task processing delay

            # Mark the task as processed
            self.processed_tasks.append(task)

            # Acknowledge the task in RabbitMQ
            self.rabbitmq.channel.basic_ack(delivery_tag)
            self.logger.info(f"Processed and acknowledged task: {task}")

        except Exception as e:
            self.logger.error(f"Error processing task: {e}")
            self.rabbitmq.channel.basic_nack(delivery_tag)

    async def update_database(self):
        """
        Updates the SQLite database with the processed tasks.
        """
        try:
            if not self.processed_tasks:
                return

            self.sqlite_manager.bulk_update_tasks(self.processed_tasks)
            self.logger.info(f"Updated {len(self.processed_tasks)} tasks in SQLite.")
            self.display.print_success(f"✔️ Updated {len(self.processed_tasks)} tasks in SQLite.")
            self.processed_tasks = []  # Clear the processed tasks list
        except Exception as e:
            self.logger.error(f"Error updating database: {e}")

    async def run(self, queue_name):
        """
        Main task processing loop.

        Args:
            queue_name (str): RabbitMQ queue name.
        """
        self.display.print_info(f"Starting TaskProcessor with batch size {self.batch_size}...")

        while True:
            # Ensure there are enough running tasks
            while len(self.running_tasks) < self.batch_size:
                delivery_tag, task = await self.fetch_task(queue_name)
                if task:
                    task_coro = self.process_task(delivery_tag, task)
                    self.running_tasks.add(asyncio.create_task(task_coro))

            # Wait for one task to complete
            done, self.running_tasks = await asyncio.wait(self.running_tasks, return_when=asyncio.FIRST_COMPLETED)

            # If processed tasks reach the threshold, update the database
            if len(self.processed_tasks) >= self.update_threshold:
                await self.update_database()
