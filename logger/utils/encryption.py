# encryption.py

from cryptography.fernet import Fernet
from logging_module.config import ENCRYPTION_KEY

# Initialize Fernet with the provided encryption key
fernet = Fernet(ENCRYPTION_KEY)

def encrypt(text):
    """
    Encrypts the given text using AES-256 encryption (Fernet).

    Args:
        text (str): The text to be encrypted.

    Returns:
        str: The encrypted text in base64-encoded format.
    """
    if not isinstance(text, str):
        raise TypeError("Text to be encrypted must be a string.")
    encrypted_text = fernet.encrypt(text.encode())
    return encrypted_text.decode()  # Return as a string

def decrypt(encrypted_text):
    """
    Decrypts the given encrypted text back to its original form.

    Args:
        encrypted_text (str): The encrypted text to be decrypted.

    Returns:
        str: The original, decrypted text.
    """
    if not isinstance(encrypted_text, str):
        raise TypeError("Encrypted text must be a string.")
    decrypted_text = fernet.decrypt(encrypted_text.encode())
    return decrypted_text.decode()  # Return as a string

def mask_data(data):
    """
    Masks sensitive information in a string for logs (e.g., replaces part of a string with asterisks).

    Args:
        data (str): The sensitive data to be masked.

    Returns:
        str: Masked data with sensitive portions replaced by asterisks.
    """
    if isinstance(data, str):
        return data[:3] + "****" + data[-3:] if len(data) > 6 else "***"
    return data  # Return unchanged if data is not a string

# Example usage
if __name__ == "__main__":
    # Sample text
    sensitive_text = "SecretInformation123"
    
    # Encrypt the text
    encrypted = encrypt(sensitive_text)
    print("Encrypted:", encrypted)
    
    # Decrypt the text
    decrypted = decrypt(encrypted)
    print("Decrypted:", decrypted)
    
    # Mask the text
    masked = mask_data(sensitive_text)
    print("Masked:", masked)
