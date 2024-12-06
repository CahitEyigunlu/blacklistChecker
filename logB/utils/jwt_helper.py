import jwt
from datetime import datetime, timedelta
from core_app.config.config import Config  # Tüm ayarları Config sınıfı üzerinden çağırıyoruz

ALGORITHM = "HS256"

def create_token(data):
    """Belirtilen verilerle bir JWT token oluşturur."""
    payload = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_EXPIRES)
    payload.update({"exp": expire})
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token):
    """JWT token doğrulaması yapar."""
    try:
        decoded_data = jwt.decode(token, Config.SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_data
    except jwt.ExpiredSignatureError:
        print("Token süresi dolmuş.")
        return None
    except jwt.InvalidTokenError:
        print("Geçersiz token.")
        return None

