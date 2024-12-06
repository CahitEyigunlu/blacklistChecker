from pymongo import MongoClient
from logger import logger

class MongoDB:
    """
    MongoDB bağlantısı ve işlemleri için bir sınıf.
    """
    def __init__(self, connection_string):
        """
        MongoDB nesnesini başlatır.

        Args:
            connection_string: MongoDB bağlantı dizesi.
        """
        self.connection_string = connection_string
        self.client = None
        self.db = None  # Veritabanı nesnesi için

    def connect(self, db_name):
        """
        MongoDB sunucusuna bağlanır ve belirtilen veritabanını seçer.

        Args:
            db_name: Bağlanılacak veritabanının adı.
        """
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[db_name]  # Veritabanını seç
            logger.info(f"MongoDB sunucusuna başarıyla bağlanıldı. Veritabanı: {db_name}")
        except Exception as e:
            logger.error(f"MongoDB bağlantı hatası: {e}")
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
            logger.info(f"{collection_name} koleksiyonuna belge eklendi. ID: {result.inserted_id}")
        except Exception as e:
            logger.error(f"Belge ekleme hatası: {e}")
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
            logger.info(f"{collection_name} koleksiyonunda {len(documents)} belge bulundu.")
            return documents
        except Exception as e:
            logger.error(f"Belge bulma hatası: {e}")
            raise

    def close_connection(self):
        """
        MongoDB bağlantısını kapatır.
        """
        try:
            if self.client:
                self.client.close()
                logger.info("MongoDB bağlantısı kapatıldı.")
        except Exception as e:
            logger.error(f"MongoDB bağlantı kapatma hatası: {e}")
            raise