from cryptography.fernet import Fernet
from app.config import settings

# Initialize Fernet with exactly 32-byte url-safe base64-encoded key
fernet = Fernet(settings.abdm_encryption_key.encode('utf-8'))

def encrypt_data(data: str | None) -> str | None:
    """Encrypt sensitive string data (e.g., ABHA Number)."""
    if not data:
        return None
    return fernet.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted_data: str | None) -> str | None:
    """Decrypt sensitive string data."""
    if not encrypted_data:
        return None
    try:
        return fernet.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')
    except Exception:
        # In case of tampered data
        return None
