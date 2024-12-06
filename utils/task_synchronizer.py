from datetime import datetime
from utils.display import Display
from logB.logger import Logger


class TaskSynchronizer:
    """
    Synchronizes tasks between in-memory tasks, SQLite, and RabbitMQ.
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

    async def synchronize(self):
        """
        Synchronizes tasks between SQLite and RabbitMQ.
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

            # Step 5: Add tasks to RabbitMQ in batches
            pending_tasks_in_sqlite = [
                task for task in sqlite_tasks if task["status"] == "pending"
            ]
            self.display.print_info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
            self.logger.info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")

            batch_size = 10000  # Batch size for publishing tasks to RabbitMQ
            total_batches = (len(pending_tasks_in_sqlite) + batch_size - 1) // batch_size

            for i in range(total_batches):
                start_idx = i * batch_size
                end_idx = min(start_idx + batch_size, len(pending_tasks_in_sqlite))
                batch = pending_tasks_in_sqlite[start_idx:end_idx]
                self.rabbitmq.publish_task(queue_name, batch)

                # Log batch progress
                batch_count = len(batch)
                self.logger.info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added.")
                self.display.print_info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added.")

            self.logger.info("✔️ Task Synchronization Completed")
        except Exception as e:
            self.logger.error(f"❌ Task synchronization failed: {e}")
            self.display.print_error(f"❌ Task synchronization failed: {e}")

        self.display.print_section_header("✔️ All checks Completed")
        self.logger.info("✔️ All checks Completed")
