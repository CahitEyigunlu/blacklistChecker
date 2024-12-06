from datetime import datetime
from utils.display import Display
from logB.logger import Logger
import os


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
        Enhanced synchronization method with detailed logging and file outputs.
        """
        today_date = datetime.now().strftime("%Y-%m-%d")
        queue_name = self.config["rabbitmq"].get("default_queue", "default_queue")
        total_tasks_count = len(self.in_memory_tasks)

        # Dosya yolları
        base_path = "task_logs"
        os.makedirs(base_path, exist_ok=True)
        memory_tasks_path = os.path.join(base_path, "in_memory_tasks.txt")
        sqlite_tasks_path = os.path.join(base_path, "sqlite_tasks.txt")
        missing_tasks_path = os.path.join(base_path, "missing_tasks.txt")

        # Step 1: Display and log total tasks generated
        self.display.print_success(f"✔️ Total tasks generated: {total_tasks_count}")
        self.logger.info(f"✔️ Total tasks generated: {total_tasks_count}")

        try:
            # Step 2: Fetch SQLite tasks for today
            sqlite_tasks = self.sqlite_manager.fetch_tasks_by_date(today_date)
            sqlite_task_set = set((task["ip"], task["blacklist_name"]) for task in sqlite_tasks)
            self.display.print_info(f"SQLite: Found {len(sqlite_tasks)} tasks for today.")
            self.logger.info(f"SQLite: Found {len(sqlite_tasks)} tasks for today.")

            # Write SQLite tasks to file
            with open(sqlite_tasks_path, "w") as file:
                for task in sqlite_tasks:
                    file.write(f'{task["ip"]},{task["blacklist_name"]}\n')

            # Step 3: Compare SQLite tasks with in-memory tasks
            in_memory_task_set = set((task["ip"], task["blacklist_name"]) for task in self.in_memory_tasks)

            # Write in-memory tasks to file
            with open(memory_tasks_path, "w") as file:
                for task in self.in_memory_tasks:
                    file.write(f'{task["ip"]},{task["blacklist_name"]}\n')

            missing_in_sqlite = in_memory_task_set - sqlite_task_set

            # Write missing tasks to file
            with open(missing_tasks_path, "w") as file:
                for ip, blacklist_name in missing_in_sqlite:
                    file.write(f"{ip},{blacklist_name}\n")

            if missing_in_sqlite:
                self.sqlite_manager.insert_tasks([
                    {"ip": ip, "blacklist_name": blacklist_name, "status": "pending"}
                    for ip, blacklist_name in missing_in_sqlite
                ])
                self.display.print_success(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")
                self.logger.info(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")
            else:
                self.display.print_info("SQLite: No missing tasks found.")
                self.logger.info("SQLite: No missing tasks found.")

            # Step 4: Compare RabbitMQ tasks with SQLite pending tasks
            rabbitmq_tasks = self.rabbitmq.get_all_tasks(queue_name)
            rabbitmq_task_set = set((task["ip"], task["blacklist_name"]) for task in rabbitmq_tasks)
            pending_tasks_in_sqlite = [
                task for task in sqlite_tasks if task["status"] == "pending"
            ]
            pending_task_set = set((task["ip"], task["blacklist_name"]) for task in pending_tasks_in_sqlite)

            missing_in_rabbitmq = pending_task_set - rabbitmq_task_set
            if missing_in_rabbitmq:
                for ip, blacklist_name in missing_in_rabbitmq:
                    self.rabbitmq.publish_task(queue_name, {
                        "ip": ip,
                        "blacklist_name": blacklist_name
                    })
                self.display.print_success(f"✔️ Added {len(missing_in_rabbitmq)} missing tasks to RabbitMQ.")
                self.logger.info(f"✔️ Added {len(missing_in_rabbitmq)} missing tasks to RabbitMQ.")
            else:
                self.display.print_info("RabbitMQ: No missing tasks found.")
                self.logger.info("RabbitMQ: No missing tasks found.")

            # Step 5: Check if all tasks are completed
            completed_tasks = [
                task for task in sqlite_tasks if task["status"] == "completed"
            ]
            if len(completed_tasks) == len(sqlite_tasks) and len(sqlite_tasks) == total_tasks_count:
                # All tasks completed
                active_db_tasks = self.active_db_manager.fetch_all_tasks()
                active_db_task_set = set((task["ip"], task["blacklist_name"]) for task in active_db_tasks)

                differences = in_memory_task_set - active_db_task_set
                if differences:
                    self.display.print_info(f"Active DB: Found {len(differences)} missing tasks. Syncing.")
                    self.logger.info(f"Active DB: Found {len(differences)} missing tasks. Syncing.")
                    self.active_db_manager.insert_tasks(differences)
                else:
                    self.display.print_success("✔️ All tasks are already synchronized across systems.")
                    self.logger.info("✔️ All tasks are already synchronized across systems.")

                # If the tasks are from an old date, reset everything
                oldest_task_date = min(task["check_date"] for task in sqlite_tasks)
                if oldest_task_date != today_date:
                    self.display.print_info("Tasks belong to an old date. Resetting everything.")
                    self.logger.info("Tasks belong to an old date. Resetting everything.")
                    self.sqlite_manager.clear_all_tasks()
                    self.rabbitmq.clear_queue(queue_name)
                    self.sqlite_manager.insert_tasks(self.in_memory_tasks)
                    for task in self.in_memory_tasks:
                        self.rabbitmq.publish_task(queue_name, task)

        except Exception as e:
            self.display.print_error(f"Task synchronization failed: {e}")
            self.logger.error(f"Task synchronization failed: {e}")

        self.display.print_section_header("Task Synchronization Completed")
        self.logger.info("Task Synchronization Completed")
