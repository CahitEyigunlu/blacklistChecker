
from cryptography.fernet import Fernet
from logB.config import ENCRYPTION_KEY

def mask_data(data):
    # Example: Replace sensitive data with asterisks
    return str(data)[:3] + '***' if isinstance(data, str) else data

def encrypt_data(data):
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(data.encode()).decode()

def decrypt_data(data):
    f = Fernet(ENCRYPTION_KEY)
    return f.decrypt(data.encode()).decode()
    