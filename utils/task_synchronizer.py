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
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.error_logger = Logger(log_file_path=config['logging']['error_log_path'])
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
                # Doğrudan çağrı, await kullanmadan
                self.sqlite_manager.insert_tasks([
                    {"ip": ip, "dns": dns, "status": "pending"}
                    for ip, dns in missing_in_sqlite
                ])
                self.display.print_success(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")
                self.logger.info(f"✔️ Added {len(missing_in_sqlite)} missing tasks to SQLite.")

                # Verify insertion
                sqlite_tasks = self.sqlite_manager.fetch_tasks_by_date(today_date)  # Yeniden sorgula
                pending_tasks_in_sqlite = [
                    task for task in sqlite_tasks if task["status"] == "pending"
                ]
                self.display.print_info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
                self.logger.info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
            else:
                self.display.print_info("ℹ️ SQLite: No missing tasks found.")
                self.logger.info("ℹ️ SQLite: No missing tasks found.")

            # Step 4: Reset RabbitMQ queue
            try:
                self.display.print_info(f"ℹ️ Deleting RabbitMQ queue '{queue_name}'...")
                self.rabbitmq.channel.queue_delete(queue=queue_name)
                self.display.print_info(f"ℹ️ Recreating RabbitMQ queue '{queue_name}' with correct settings...")
                self.rabbitmq.channel.queue_declare(queue=queue_name, durable=False)  # Burada durable=True doğru ayarı belirtiyor
                self.display.print_info(f"✔️ RabbitMQ queue '{queue_name}' recreated successfully.")
            except Exception as e:
                self.error_logger.error(f"❌ Failed to reset RabbitMQ queue '{queue_name}': {e}")
                self.display.print_error(f"❌ Failed to reset RabbitMQ queue '{queue_name}': {e}")
                raise


            # Step 5: Add tasks to RabbitMQ in batches
            pending_tasks_in_sqlite = [
                task for task in sqlite_tasks if task["status"] == "pending"
            ]
            self.display.print_info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
            self.logger.info(f"ℹ️ SQLite: Found {len(pending_tasks_in_sqlite)} pending tasks.")
            self.display.print_info(f"ℹ️ RabbitMQ: Publishing tasks to '{queue_name}'...")
            batch_size = 10000  # Batch size for publishing tasks to RabbitMQ
            total_batches = (len(pending_tasks_in_sqlite) + batch_size - 1) // batch_size
            queue_size = len(pending_tasks_in_sqlite)
            self.display.print_info(f"ℹ️ Total tasks to publish: {queue_size}")

            for i in range(total_batches):
                try:
                    start_idx = i * batch_size
                    end_idx = min(start_idx + batch_size, len(pending_tasks_in_sqlite))
                    batch = pending_tasks_in_sqlite[start_idx:end_idx]
                    self.rabbitmq.publish_task(queue_name, batch)

                    # Log batch progress
                    batch_count = len(batch)
                    self.logger.info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added.")
                    self.display.print_info(f"✔️ Batch {i + 1}/{total_batches}: {batch_count} tasks added.")
                    
                    # Verify message count in RabbitMQ after each batch
                    queue_state = self.rabbitmq.channel.queue_declare(queue=queue_name, passive=True)
                    message_count = queue_state.method.message_count
                    
                    expected_message_count = start_idx + batch_count
                    if message_count != expected_message_count:
                        self.logger.warning(f"⚠️ Mismatch in RabbitMQ message count. Expected: {expected_message_count}, Actual: {message_count}")
                        self.display.print_warning(f"⚠️ Mismatch in RabbitMQ message count. Expected: {expected_message_count}, Actual: {message_count}")
                    else:
                        self.logger.info(f"✔️ Verified RabbitMQ message count after batch {i + 1}: {message_count}")
                        self.display.print_info(f"✔️ Verified RabbitMQ message count after batch {i + 1}: {message_count}")

                except Exception as batch_error:
                    error_message = f"Error in batch {i + 1}/{total_batches}: {batch_error}"
                    self.error_logger.error(error_message, extra={"function": "synchronize", "file": "task_synchronizer.py", "batch": i+1})
                    self.display.print_error(f"❌ {error_message}")

            # Final message count verification
            queue_state = self.rabbitmq.channel.queue_declare(queue=queue_name, passive=True)
            final_message_count = queue_state.method.message_count
            self.display.print_info(f"Message count in RabbitMQ queue '{queue_name}' after publishing: {final_message_count}")
            self.logger.info(f"Message count in RabbitMQ queue '{queue_name}' after publishing: {final_message_count}")




            try:
                self.rabbitmq.publish_task(queue_name, batch)
                print(f"Published batch of size {len(batch)} successfully.")
            except Exception as e:
                print(f"Failed to publish batch: {e}")

            self.logger.info("✔️ Task Synchronization Completed")
            exit(0)
        except Exception as e:
            error_message = f"❌ Task synchronization failed: {e}"
            self.error_logger.error(error_message, extra={"function": "synchronize", "file": "task_synchronizer.py"})  # extra bilgisi eklendi
            self.display.print_error(f"❌ {error_message}")

        self.display.print_section_header("✔️ All checks Completed")
        self.logger.info("✔️ All checks Completed")