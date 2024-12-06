import pika
from logB.logger import Logger


class RabbitMQ:
    """
    A class for RabbitMQ connection and operations.
    """

    def __init__(self, host, username, password, queue_name=None):
        """
        Initializes the RabbitMQ object.

        Args:
            host: Hostname or IP address of the RabbitMQ server.
            username: Username for RabbitMQ authentication.
            password: Password for RabbitMQ authentication.
            queue_name: Optional queue name to ensure existence.
        """
        self.host = host
        self.username = username
        self.password = password
        self.connection = None
        self.channel = None
        self.logger = Logger(log_file_path="logs/rabbitmq.log")  # Logger instance
        self.queue_name = queue_name

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

            # Ensure the default queue exists
            if self.queue_name:
                self.channel.queue_declare(queue=self.queue_name)
                self.logger.info(f"Queue '{self.queue_name}' created or already exists.")
        except pika.exceptions.ProbableAuthenticationError as e:
            self.logger.error(f"Authentication error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"RabbitMQ connection error: {e}")
            raise


    def create_queue(self, queue_name):
        """
        Creates a queue with the specified name.

        Args:
            queue_name: The name of the queue to create.
        """
        try:
            self.channel.queue_declare(queue=queue_name)
            self.logger.info(f"Created queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"Error creating queue: {e}")
            raise

    def purge_queue(self, queue_name):
        """
        Purges the specified queue.

        Args:
            queue_name: The name of the queue to purge.
        """
        try:
            self.channel.queue_purge(queue=queue_name)
            self.logger.info(f"Purged queue: {queue_name}")
        except Exception as e:
            self.logger.error(f"Error purging queue: {e}")
            raise

    def publish_message(self, queue_name, message):
        """
        Publishes a message to the specified queue.

        Args:
            queue_name: The name of the queue to publish to.
            message: The message to publish.
        """
        try:
            self.channel.basic_publish(exchange='', routing_key=queue_name, body=message)
            self.logger.info(f"Published message to {queue_name} queue: {message}")
        except Exception as e:
            self.logger.error(f"Error publishing message: {e}")
            raise

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
            self.logger.error(f"Error consuming messages: {e}")
            raise

    def close_connection(self):
        """
        Closes the RabbitMQ connection.
        """
        try:
            if self.connection:
                self.connection.close()
                self.logger.info("RabbitMQ connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {e}")
            raise

    def get_all_tasks(self, queue_name):
        """
        Retrieves all tasks from a specific RabbitMQ queue without consuming them.

        Args:
            queue_name (str): Name of the RabbitMQ queue.

        Returns:
            list: A list of all messages in the queue.
        """
        self.channel.queue_declare(queue=queue_name, passive=True)
        tasks = []
        while True:
            method_frame, header_frame, body = self.channel.basic_get(queue=queue_name, auto_ack=False)
            if method_frame:
                tasks.append(body)
            else:
                break
        return tasks
