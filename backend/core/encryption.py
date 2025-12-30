"""
Digital Denis — Data Encryption
═══════════════════════════════════════════════════════════════════════════

AES-256 (Fernet) encryption for sensitive data.
"""

import base64
from typing import Optional

from cryptography.fernet import Fernet
from core.config import settings

class EncryptionService:
    """
    Handles encryption and decryption of sensitive data.
    """
    def __init__(self, key: Optional[str] = None):
        self.key = key or settings.encryption_key
        # Ensure key is valid Fernet key (32 bytes base64)
        try:
            self.fernet = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)
        except Exception:
            # Fallback for development if key is not valid
            import hashlib
            derived_key = base64.urlsafe_b64encode(hashlib.sha256(self.key.encode()).digest())
            self.fernet = Fernet(derived_key)

    def encrypt(self, data: str) -> str:
        """Encrypt string to base64 string."""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt base64 string to original string."""
        if not encrypted_data:
            return encrypted_data
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            # Return original if decryption fails (e.g. data was not encrypted)
            return encrypted_data

# Global instance
encryptor = EncryptionService()
