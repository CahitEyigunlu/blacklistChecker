import pika
from logger import logger

class RabbitMQ:
    """
    RabbitMQ bağlantısı ve işlemleri için bir sınıf.
    """
    def __init__(self, host):
        """
        RabbitMQ nesnesini başlatır.

        Args:
            host: RabbitMQ sunucusunun host adı veya IP adresi.
        """
        self.host = host
        self.connection = None
        self.channel = None

    def connect(self):
        """
        RabbitMQ sunucusuna bağlanır.
        """
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            self.channel = self.connection.channel()
            logger.info("RabbitMQ sunucusuna başarıyla bağlanıldı.")
        except Exception as e:
            logger.error(f"RabbitMQ bağlantı hatası: {e}")
            raise

    def create_queue(self, queue_name):
        """
        Belirtilen adda bir kuyruk oluşturur.

        Args:
            queue_name: Oluşturulacak kuyruğun adı.
        """
        try:
            self.channel.queue_declare(queue=queue_name)
            logger.info(f"Kuyruk oluşturuldu: {queue_name}")
        except Exception as e:
            logger.error(f"Kuyruk oluşturma hatası: {e}")
            raise

    def publish_message(self, queue_name, message):
        """
        Belirtilen kuyruğa bir mesaj yayınlar.

        Args:
            queue_name: Mesajın yayınlanacağı kuyruğun adı.
            message: Yayınlanacak mesaj.
        """
        try:
            self.channel.basic_publish(exchange='', routing_key=queue_name, body=message)
            logger.info(f"{queue_name} kuyruğuna mesaj yayınlandı: {message}")
        except Exception as e:
            logger.error(f"Mesaj yayınlama hatası: {e}")
            raise

    def consume_messages(self, queue_name, callback):
        """
        Belirtilen kuyruktan mesajları tüketir.

        Args:
            queue_name: Mesajların tüketileceği kuyruğun adı.
            callback: Mesaj alındığında çağrılacak geri çağırma fonksiyonu.
        """
        try:
            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            logger.info(f"{queue_name} kuyruğundan mesajlar tüketiliyor...")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Mesaj tüketme hatası: {e}")
            raise

    def close_connection(self):
        """
        RabbitMQ bağlantısını kapatır.
        """
        try:
            if self.connection:
                self.connection.close()
                logger.info("RabbitMQ bağlantısı kapatıldı.")
        except Exception as e:
            logger.error(f"RabbitMQ bağlantı kapatma hatası: {e}")
            raise