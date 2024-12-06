import pika

from utils.config_manager import load_config
from utils.display import Display
from logger import Logger

# Logger ayarları
info_logger = Logger("logs/info.log")
error_logger = Logger("logs/error.log")


def test_rabbitmq_connection():
    """
    RabbitMQ bağlantısını test eder.
    Config dosyasındaki RabbitMQ ayarlarını kullanır.
    """
    try:
        # Config dosyasını yükle
        config = load_config()

        if not config or 'rabbitmq' not in config:
            raise ValueError("RabbitMQ ayarları 'rabbitmq' altında bulunamadı.")

        # RabbitMQ bağlantı detaylarını al
        rabbitmq_config = config['rabbitmq']
        host = rabbitmq_config.get('host')
        port = rabbitmq_config.get('port', 5672)  # Varsayılan port: 5672
        username = rabbitmq_config.get('username')
        password = rabbitmq_config.get('password')

        if not host or not username or not password:
            raise ValueError("RabbitMQ bağlantı ayarları eksik.")

        # Bağlantı bilgilerini ekrana yazdır
        Display.print_info("RabbitMQ Bağlantı Bilgileri:")
        Display.print_info(f"  Host: {host}")
        Display.print_info(f"  Port: {port}")
        Display.print_info(f"  Kullanıcı Adı: {username}")

        # RabbitMQ bağlantısını test et
        credentials = pika.PlainCredentials(username, password)
        connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            socket_timeout=5  # Zaman aşımı 5 saniye
        )

        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.close()
        connection.close()

        # Başarı mesajı
        info_logger.info(f"RabbitMQ bağlantısı başarılı: {host}:{port}")
        Display.print_success("RabbitMQ bağlantısı başarılı.")
        return True

    except pika.exceptions.ProbableAuthenticationError:
        # Kimlik doğrulama hatası
        error_logger.error("RabbitMQ kimlik doğrulama hatası.")
        Display.print_error("RabbitMQ kimlik doğrulama hatası.")
        return False
    except pika.exceptions.AMQPConnectionError:
        # Bağlantı hatası
        error_logger.error("RabbitMQ bağlantı hatası.")
        Display.print_error("RabbitMQ bağlantı hatası.")
        return False
    except Exception as e:
        # Genel hata
        error_logger.error(f"RabbitMQ testi sırasında beklenmeyen hata: {str(e)}")
        Display.print_error(f"RabbitMQ testi sırasında beklenmeyen hata: {str(e)}")
        return False