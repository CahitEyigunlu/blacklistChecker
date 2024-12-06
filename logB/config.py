# config.py

import os
from cryptography.fernet import Fernet

# Log file configuration
LOG_DIRECTORY = os.path.join(os.getcwd(), "logs")  # Çalışma dizininde 'logs' klasörü oluşturur
os.makedirs(LOG_DIRECTORY, exist_ok=True)  # Log klasörünün varlığını garanti eder

LOG_FILE_PATH = os.path.join(LOG_DIRECTORY, "app_logs.json")
LOG_ROTATION_SIZE = 10 * 1024 * 1024  # Log dosyası 10 MB'a ulaştığında döndürme işlemi yapılır
LOG_RETENTION_DAYS = 30  # Log dosyaları 30 gün boyunca saklanır

# Security configuration (Encryption key for sensitive data in logs)
# Fernet şifrelemesi için 32 baytlık URL güvenli base64 kodlanmış bir anahtar gereklidir.
# Aşağıdaki anahtarı bir kere oluşturup sabit olarak kullanabilirsiniz.
# Yeni bir anahtar oluşturmak için:
# `ENCRYPTION_KEY = Fernet.generate_key()`

# Geçerli bir Fernet anahtarı. Üretim ortamında bu anahtarı güvenli bir yerde saklayın!
ENCRYPTION_KEY = b'G2k9k7eXKDm6cF3yJaVu6M4TJmnM9jFi6OlEhzGpREU='

# Diğer ayarlar
DEBUG_MODE = True  # Hata ayıklama modunu etkinleştirir, daha ayrıntılı loglama sağlar
