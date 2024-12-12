from pymongo import MongoClient
from logB.logger import Logger


class MongoDB:
    """
    MongoDB bağlantısı ve işlemleri için bir sınıf.
    """

    def __init__(self, config):  # config parametresi eklendi
        """
        MongoDB nesnesini başlatır.

        Args:
            config: Uygulama yapılandırması.
        """
        self.config = config  # config değişkeni eklendi
        self.connection_string = config["mongodb"]["url"]  # connection string config'den alınıyor
        self.client = None
        self.db = None
        self.logger = Logger(log_file_path=config['logging']['app_log_path'])  # Logger nesnesi, config dosyasından log yolunu alıyor

    def connect(self, db_name=None):  # db_name parametresi opsiyonel hale getirildi
        """
        MongoDB sunucusuna bağlanır ve belirtilen veritabanını seçer.

        Args:
            db_name: Bağlanılacak veritabanının adı (opsiyonel). Eğer belirtilmezse, config dosyasındaki db_name kullanılır.
        """
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[db_name or self.config["mongodb"]["db_name"]]  # db_name yoksa config'den al
            self.logger.info(f"MongoDB sunucusuna başarıyla bağlanıldı. Veritabanı: {self.db.name}")
        except Exception as e:
            self.logger.error(f"MongoDB bağlantı hatası: {e}", extra={"function": "connect", "file": "mongodb.py"})  # extra bilgisi eklendi
            raise

    def insert_document(self, collection_name, document):
        """
        Belirtilen koleksiyona bir belge ekler.

        Args:
            collection_name: Belgenin ekleneceği koleksiyonun adı.
            document: Eklenecek belge (sözlük).
        """
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            self.logger.info(f"{collection_name} koleksiyonuna belge eklendi. ID: {result.inserted_id}")
        except Exception as e:
            self.logger.error(f"Belge ekleme hatası: {e}", extra={"function": "insert_document", "file": "mongodb.py", "collection": collection_name})  # extra bilgisi eklendi
            raise

    def find_documents(self, collection_name, query):
        """
        Belirtilen koleksiyonda sorguya uyan belgeleri bulur.

        Args:
            collection_name: Belgelerin aranacağı koleksiyonun adı.
            query: Sorgu (sözlük).

        Returns:
            Sorguya uyan belgelerin listesi.
        """
        try:
            collection = self.db[collection_name]
            documents = list(collection.find(query))
            self.logger.info(f"{collection_name} koleksiyonunda {len(documents)} belge bulundu.")
            return documents
        except Exception as e:
            self.logger.error(f"Belge bulma hatası: {e}", extra={"function": "find_documents", "file": "mongodb.py", "collection": collection_name, "query": query})  # extra bilgisi eklendi
            raise

    def close_connection(self):
        """
        MongoDB bağlantısını kapatır.
        """
        try:
            if self.client:
                self.client.close()
                self.logger.info("MongoDB bağlantısı kapatıldı.")
        except Exception as e:
            self.logger.error(f"MongoDB bağlantı kapatma hatası: {e}", extra={"function": "close_connection", "file": "mongodb.py"})  # extra bilgisi eklendi
            raise