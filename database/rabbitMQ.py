import json
import pika
from logB.logger import Logger
from utils.display import Display


class RabbitMQ:
    """
    A class for RabbitMQ connection and operations.
    """

    def __init__(self, config, queue_name=None):
        """
        Initializes the RabbitMQ object.

        Args:
            config: Application configuration.
            queue_name: Optional queue name to ensure existence.
        """
        self.config = config
        self.host = config["rabbitmq"]["host"]
        self.username = config["rabbitmq"]["username"]
        self.password = config["rabbitmq"]["password"]
        self.connection = None
        self.channel = None
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])
        self.display = Display()
        self.queue_name = queue_name or config["rabbitmq"].get("default_queue", "default_queue")

    def ensure_queue_exists(self, queue_name):
        """
        Ensures the specified queue exists.

        Args:
            queue_name (str): The name of the queue to check/create.
        """
        try:
            self.channel.queue_declare(queue=queue_name)
            self.logger.info(f"Queue '{queue_name}' ensured to exist.")
        except Exception as e:
            self._handle_critical_error(f"Error ensuring queue exists: {e}", "ensure_queue_exists", queue_name)

    def connect(self):
        """
        Connects to the RabbitMQ server and ensures the default queue exists.
        """
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    credentials=credentials,
                    virtual_host='/'
                )
            )
            self.channel = self.connection.channel()
            self.logger.info("Successfully connected to RabbitMQ server.")
            self.display.print_success("✔️ Connected to RabbitMQ server.")
            self.ensure_queue_exists(self.queue_name)
        except pika.exceptions.ProbableAuthenticationError as e:
            self._handle_critical_error(f"Authentication error: {e}", "connect")
        except Exception as e:
            self._handle_critical_error(f"RabbitMQ connection error: {e}", "connect")

    def clear_queue(self, queue_name=None):
        """
        Clears all messages from the specified RabbitMQ queue.

        Args:
            queue_name (str): The name of the queue to clear.
        """
        queue_name = queue_name or self.queue_name
        try:
            self.channel.queue_purge(queue=queue_name)
            self.display.print_success(f"✔️ Queue '{queue_name}' cleared successfully.")
            self.display.print_success(f"✔️ Queue '{queue_name}' has {self.channel.queue_declare(queue=queue_name).method.message_count} messages.")
        except pika.exceptions.ChannelClosedByBroker as e:
            if e.args[0] == 404:
                self.display.print_warning(f"⚠️ Queue '{queue_name}' not found. Creating the queue...")
                self.ensure_queue_exists(queue_name)
                self.channel.queue_purge(queue=queue_name)
                self.display.print_success(f"✔️ Queue '{queue_name}' created and cleared successfully.")
            else:
                self._handle_critical_error(f"Error clearing queue '{queue_name}': {e}", "clear_queue", queue_name)
            
        except Exception as e:
            self._handle_critical_error(f"Error clearing queue '{queue_name}': {e}", "clear_queue", queue_name)

    def publish_task(self, queue_name, tasks):
        """
        Publishes multiple tasks to the specified queue in batch.

        Args:
            queue_name (str): The name of the queue to publish the tasks to.
            tasks (list of dict): The tasks to publish.
        """
        try:
            self.ensure_queue_exists(queue_name)
            for task in tasks:
                message = json.dumps(task)
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=message,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            self.logger.info(f"Published {len(tasks)} tasks to queue '{queue_name}'.")
        except Exception as e:
            self._handle_critical_error(f"Failed to publish tasks to queue '{queue_name}': {e}", "publish_task", queue_name)

    def publish_message(self, queue_name, message):
        """
        Publishes a message to the specified queue.

        Args:
            queue_name: The name of the queue to publish to.
            message: The message to publish.
        """
        try:
            self.ensure_queue_exists(queue_name)
            self.channel.basic_publish(exchange='', routing_key=queue_name, body=message)
            self.logger.info(f"Published message to {queue_name} queue: {message}")
        except Exception as e:
            self._handle_critical_error(f"Error publishing message to '{queue_name}': {e}", "publish_message", queue_name)

    def consume_messages(self, queue_name, callback):
        """
        Consumes messages from the specified queue.

        Args:
            queue_name: The name of the queue to consume from.
            callback: The callback function to call when a message is received.
        """
        try:
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            self.logger.info(f"Consuming messages from {queue_name} queue...")
            self.channel.start_consuming()
        except Exception as e:
            self._handle_critical_error(f"Error consuming messages: {e}", "consume_messages", queue_name)

    def fetch_tasks(self, queue_name, max_tasks):
        """
        Fetches tasks from a RabbitMQ queue.

        Args:
            queue_name (str): The name of the queue to fetch tasks from.
            max_tasks (int): Maximum number of tasks to fetch.

        Returns:
            list: A list of (delivery_tag, task_data) tuples.
        """
        tasks = []
        try:
            for _ in range(max_tasks):
                method_frame, _, body = self.channel.basic_get(queue=queue_name, auto_ack=False)
                if method_frame:
                    delivery_tag = method_frame.delivery_tag
                    task_data = json.loads(body)  # Assumes tasks are serialized as JSON
                    tasks.append((delivery_tag, task_data))
                else:
                    break
            return tasks
        except Exception as e:
            self.logger.error(f"Error fetching tasks from queue '{queue_name}': {e}", extra={"function": "fetch_tasks", "file": "rabbitmq.py", "queue_name": queue_name})
            return []

    def close_connection(self):
        """
        Closes the RabbitMQ connection.
        """
        try:
            if self.connection:
                self.connection.close()
                self.logger.info("RabbitMQ connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {e}", extra={"function": "close_connection", "file": "rabbitmq.py"})

    def _handle_critical_error(self, error_message, function_name, queue_name=None):
        """
        Logs the error, displays a user-friendly message, and terminates the application.

        Args:
            error_message (str): The error message to log and display.
            function_name (str): The name of the function where the error occurred.
            queue_name (str, optional): The name of the queue involved in the error.
        """
        self.logger.error(
            error_message,
            extra={"function": function_name, "file": "rabbitmq.py", "queue_name": queue_name}
        )
        self.display.print_error(f"❌ {error_message}")
        self.display.print_error("Critical RabbitMQ error. Terminating application.")
        exit(1)
