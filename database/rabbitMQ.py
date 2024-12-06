import pika

from logger import logger


class RabbitMQ:
    """
    A class for RabbitMQ connection and operations.
    """

    def __init__(self, host):
        """
        Initializes the RabbitMQ object.

        Args:
            host: Hostname or IP address of the RabbitMQ server.
        """
        self.host = host
        self.connection = None
        self.channel = None

    def connect(self):
        """
        Connects to the RabbitMQ server.
        """
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            self.channel = self.connection.channel()
            logger.info("Successfully connected to RabbitMQ server.")
        except Exception as e:
            logger.error(f"RabbitMQ connection error: {e}")
            raise

    def create_queue(self, queue_name):
        """
        Creates a queue with the specified name.

        Args:
            queue_name: The name of the queue to create.
        """
        try:
            self.channel.queue_declare(queue=queue_name)
            logger.info(f"Created queue: {queue_name}")
        except Exception as e:
            logger.error(f"Error creating queue: {e}")
            raise

    def purge_queue(self, queue_name):
        """
        Purges the specified queue.

        Args:
            queue_name: The name of the queue to purge.
        """
        try:
            self.channel.queue_purge(queue=queue_name)
            logger.info(f"Purged queue: {queue_name}")
        except Exception as e:
            logger.error(f"Error purging queue: {e}")
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
            logger.info(f"Published message to {queue_name} queue: {message}")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
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
            logger.info(f"Consuming messages from {queue_name} queue...")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise

    def close_connection(self):
        """
        Closes the RabbitMQ connection.
        """
        try:
            if self.connection:
                self.connection.close()
                logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise