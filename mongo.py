from pymongo import MongoClient
from pymongo.pool import PoolOptions

class MongoDBHandler:
    def __init__(self, mongo_uri, database_name, collection_name):
        self.client = MongoClient(mongo_uri, maxPoolSize=10)
        self.collection = self.client[database_name][collection_name]

    def save_to_mongo(self, blacklist_name, ip):
        """
        Kara liste cevaplarını MongoDB'ye kaydeder.
        """
        try:
            self.collection.insert_one({"blacklist": blacklist_name, "ip": ip})
            print(f"MongoDB'ye kayıt edildi: {blacklist_name} - {ip}")
        except Exception as e:
            print(f"MongoDB hata: {str(e)}")
