import sqlite3
from utils import display
from logger import logger

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Veritabanına bağlanır."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logger.info("Veritabanına başarıyla bağlanıldı.")
            return self.conn
        except sqlite3.Error as e:
            display.print_colored(f"Veritabanı bağlantı hatası: {e}", "kırmızı")
            logger.error(f"Veritabanı bağlantı hatası: {e}")
            return None

    def create_table(self):
        """IP adreslerini ve kontrol bilgilerini saklamak için tablo oluşturur."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_check (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    result TEXT,
                    check_date DATE,
                    last_checked DATETIME
                )
            ''')
            self.conn.commit()
            logger.info("Tablo başarıyla oluşturuldu.")
        except sqlite3.Error as e:
            display.print_colored(f"Tablo oluşturma hatası: {e}", "kırmızı")
            logger.error(f"Tablo oluşturma hatası: {e}")

    def add_ip_address(self, ip_address):
        """Yeni bir IP adresi ekler."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO ip_check (ip_address, status, check_date, last_checked) VALUES (?, ?, DATE('now'), DATETIME('now'))", (ip_address, "bekliyor"))
            self.conn.commit()
            logger.info(f"IP adresi eklendi: {ip_address}")
        except sqlite3.Error as e:
            display.print_colored(f"IP adresi ekleme hatası: {e}", "kırmızı")
            logger.error(f"IP adresi ekleme hatası: {e}")

    def update_ip_status(self, ip_address, status, result=None):
        """IP adresinin durumunu ve sonucunu günceller."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE ip_check SET status = ?, result = ?, last_checked = DATETIME('now') WHERE ip_address = ?", (status, result, ip_address))
            self.conn.commit()
            logger.info(f"IP adresi durumu güncellendi: {ip_address} - {status}")
        except sqlite3.Error as e:
            display.print_colored(f"IP durumu güncelleme hatası: {e}", "kırmızı")
            logger.error(f"IP durumu güncelleme hatası: {e}")

    def get_unchecked_ips(self):
        """Henüz kontrol edilmemiş veya bugün kontrol edilmemiş IP adreslerini alır."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT ip_address FROM ip_check WHERE status != 'tamamlandı' OR check_date != DATE('now')")
            ips = [row[0] for row in cursor.fetchall()]
            logger.info(f"Kontrol edilmemiş IP adresleri alındı: {len(ips)} adet")
            return ips
        except sqlite3.Error as e:
            display.print_colored(f"Kontrol edilmemiş IP'leri alma hatası: {e}", "kırmızı")
            logger.error(f"Kontrol edilmemiş IP'leri alma hatası: {e}")
            return []

    def close_connection(self):
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Veritabanı bağlantısı kapatıldı.")