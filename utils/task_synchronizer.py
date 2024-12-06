from datetime import datetime
from utils.display import Display
from logB.logger import Logger
import os
import json


class TaskSynchronizer:
    """
    Synchronizes tasks between in-memory tasks, SQLite, RabbitMQ, and the active database.
    """

    def __init__(self, sqlite_manager, rabbitmq, in_memory_tasks, config, active_db_manager):
        """
        Initializes the TaskSynchronizer.

        Args:
            sqlite_manager: SQLite manager instance.
            rabbitmq: RabbitMQ manager instance.
            in_memory_tasks: List of in-memory tasks (combinations).
            config: Configuration dictionary.
            active_db_manager: Active database manager instance for cross-checking.
        """
        self.sqlite_manager = sqlite_manager
        self.rabbitmq = rabbitmq
        self.in_memory_tasks = in_memory_tasks
        self.config = config
        self.active_db_manager = active_db_manager
        self.logger = Logger(log_file_path="logs/task_synchronizer.log")
        self.display = Display()

    def synchronize(self):
        """
        Synchronizes tasks between SQLite and RabbitMQ, and updates the active database.
        """
        today_date = datetime.now().strftime("%Y-%m-%d")
        queue_name = self.config["rabbitmq"].get("default_queue", "default_queue")
        total_tasks_count = len(self.in_memory_tasks)

        # Step 1: Display and log total tasks generated
        self.display.print_success(f"✔️ Total tasks generated: {total_tasks_count}")
        self.logger.info(f"✔️ Total tasks generated: {total_tasks_count}")

        try:
            # Step 2: Fetch tasks for today from SQLite
            sqlite_tasks = self.sqlite_manager.fetch_tasks_by_date(today_date)
            sqlite_task_set = set((task["ip"], task["dns"]) for task in sqlite_tasks)

            # Step 3: Compare SQLite tasks with in-memory tasks
            in_memory_task_set = set((task["ip"], task["dns"]) for task in self.in_memory_tasks)
            missing_in_sqlite = in_memory_task_set - sqlite_task_set

            if missing_in_sqlite:
                self.sqlite_manager.insert_tasks([
                    {"ip": ip, "dns": dns, "status": "pending"}
                    for ip, dns in missing_in_sqlite
                ])
                self.display.print_success(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")
                self.logger.info(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")
            else:
                self.display.print_info("ℹ️ SQLite: No missing tasks found.")
                self.logger.info("ℹ️ SQLite: No missing tasks found.")

            # Step 4: Clear RabbitMQ queue
            self.logger.info("ℹ️ Clearing RabbitMQ queue...")
            self.rabbitmq.clear_queue(queue_name)
            self.logger.info(f"✔️ RabbitMQ queue '{queue_name}' cleared successfully.")

            # Step 5: Fetch "pending" tasks from SQLite
            pending_tasks_in_sqlite = [
                task for task in sqlite_tasks if task["status"] == "pending"
            ]
            self.display.print_info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
            self.logger.info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")

            # Step 6: Add tasks to RabbitMQ in batches
            batch_size = 10000
            total_batches = (len(pending_tasks_in_sqlite) + batch_size - 1) // batch_size  # Calculate total batches
            total_added_tasks = 0

            self.logger.info(f"ℹ️ Starting RabbitMQ upload: {total_batches} batches (batch size: {batch_size}).")
            self.display.print_info(f"ℹ️ RabbitMQ upload: {total_batches} batches, {batch_size} tasks per batch.")

            for i in range(total_batches):
                start_idx = i * batch_size
                end_idx = start_idx + batch_size
                batch = pending_tasks_in_sqlite[start_idx:end_idx]
                self.rabbitmq.publish_task(queue_name, batch)
                batch_count = len(batch)
                total_added_tasks += batch_count
                self.logger.info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added to RabbitMQ.")
                self.display.print_info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added.")

            self.logger.info(f"✔️ Total of {total_added_tasks} tasks added to RabbitMQ queue '{queue_name}'.")
            self.display.print_success(f"✔️ Total of {total_added_tasks} tasks added to RabbitMQ queue '{queue_name}'.")

        except Exception as e:
            self.logger.error(f"❌ Task synchronization failed: {e}")
            self.display.print_error(f"❌ Task synchronization failed: {e}")

        self.display.print_section_header("✔️ Task Synchronization Completed")
        self.logger.info("✔️ Task Synchronization Completed")

    def report_status(self, status_message):
        """
        Reports the current status of the synchronization process.

        Args:
            status_message (str): The status message to log and display.
        """
        self.logger.info(status_message)
        self.display.print_info(status_message)
        return status_message

    def fetch_tasks(self, queue_name, batch_size):
        """
        Fetches tasks from RabbitMQ queue.

        Args:
            queue_name (str): The RabbitMQ queue name.
            batch_size (int): Number of tasks to fetch.

        Returns:
            list: A list of tasks fetched from RabbitMQ.
        """
        tasks = []
        for _ in range(batch_size):
            method_frame, _, body = self.rabbitmq.channel.basic_get(queue=queue_name, auto_ack=False)
            if method_frame:
                task = json.loads(body.decode('utf-8'))
                tasks.append((method_frame.delivery_tag, task))
            else:
                break
        return tasks

    def process_tasks(self, tasks):
        """
        Processes a list of tasks.

        Args:
            tasks (list): A list of tasks to process.
        """
        for delivery_tag, task in tasks:
            try:
                # Simulate task processing (e.g., network request, computation)
                print(f"Processing task: {task}")  # Replace with actual processing logic
                self.rabbitmq.channel.basic_ack(delivery_tag)  # Acknowledge task completion
            except Exception as e:
                self.logger.error(f"Failed to process task: {e}")
                self.rabbitmq.channel.basic_nack(delivery_tag)
