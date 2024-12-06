import asyncio
import dns.resolver  # For DNSBL lookups
from logB.logger import Logger
from utils.display import Display


class ProcessManager:
    """
    Manages the processing of tasks from RabbitMQ.
    """

    def __init__(self, rabbitmq, sqlite_manager, config):
        """
        Initializes the ProcessManager.

        Args:
            rabbitmq: RabbitMQ manager instance.
            sqlite_manager: SQLite manager instance.
            config: Configuration dictionary.
        """
        self.rabbitmq = rabbitmq
        self.sqlite_manager = sqlite_manager
        self.config = config
        self.logger = Logger(log_file_path="logs/process_manager.log")
        self.display = Display()
        self.processed_tasks = []

    async def fetch_and_process_tasks(self, queue_name, max_concurrent_tasks=10):
        """
        Fetches tasks from RabbitMQ dynamically and processes them with a concurrency limit.

        Args:
            queue_name (str): The name of the RabbitMQ queue to process.
            max_concurrent_tasks (int): Maximum number of concurrent tasks to process.
        """
        semaphore = asyncio.Semaphore(max_concurrent_tasks)  # Limit the number of concurrent tasks

        async def process_single_task(delivery_tag, task):
            """
            Processes a single task, releases semaphore after processing.

            Args:
                delivery_tag (int): The delivery tag of the RabbitMQ message.
                task (dict): The task data.
            """
            async with semaphore:
                try:
                    self.display.print_info(f"Processing task: {task}")
                    # Perform DNSBL query
                    ip = task.get("ip")
                    dnsbl_server = task.get("dns")
                    reversed_ip = ".".join(reversed(ip.split(".")))
                    query = f"{reversed_ip}.{dnsbl_server}"

                    try:
                        answers = dns.resolver.resolve(query, "A")
                        task["status"] = "blacklisted"
                        task["result"] = [str(answer) for answer in answers]
                        self.display.print_success(f"IP {ip} is blacklisted on {dnsbl_server}.")
                    except dns.resolver.NXDOMAIN:
                        task["status"] = "clean"
                        task["result"] = None
                        self.display.print_info(f"IP {ip} is not blacklisted on {dnsbl_server}.")
                    except Exception as e:
                        task["status"] = "error"
                        task["result"] = str(e)
                        self.logger.error(f"Error querying {query}: {e}")

                    self.rabbitmq.channel.basic_ack(delivery_tag)  # Acknowledge task in RabbitMQ
                    self.logger.info(f"Task completed: {task}")
                except Exception as e:
                    self.logger.error(f"Error processing task: {e}")
                    self.rabbitmq.channel.basic_nack(delivery_tag)  # Negative acknowledgment
                    self.display.print_error(f"❌ Error processing task: {e}")

        try:
            while True:
                tasks = self.rabbitmq.fetch_tasks(queue_name, max_concurrent_tasks)
                if not tasks:
                    self.display.print_info("No tasks found in RabbitMQ. Sleeping...")
                    await asyncio.sleep(5)  # Wait before checking for new tasks
                    continue

                # Launch task processing
                task_futures = [
                    process_single_task(delivery_tag, task) for delivery_tag, task in tasks
                ]
                await asyncio.gather(*task_futures)  # Wait for all tasks to complete

                # Bulk update SQLite after processing all tasks in the batch
                completed_tasks = [task for _, task in tasks if task.get("status") in {"clean", "blacklisted"}]
                if completed_tasks:
                    try:
                        self.sqlite_manager.bulk_update_tasks(completed_tasks)
                        self.display.print_success(
                            f"✔️ Bulk updated {len(completed_tasks)} tasks in SQLite."
                        )
                        self.logger.info(f"✔️ Bulk updated {len(completed_tasks)} tasks in SQLite.")
                    except Exception as e:
                        self.logger.error(f"Error updating SQLite: {e}")
                        self.display.print_error(f"❌ Error updating SQLite: {e}")

        except Exception as e:
            self.logger.error(f"Error during fetch and process tasks: {e}")
            self.display.print_error(f"❌ Error during fetch and process tasks: {e}")
