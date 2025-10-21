"""Encryption utilities for sensitive data using AES-256-GCM."""
import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """Service for encrypting and decrypting sensitive data using AES-256-GCM.

    AES-256-GCM provides both confidentiality and authenticity, ensuring that
    encrypted data cannot be tampered with.
    """

    def __init__(self, secret_key: Optional[bytes] = None):
        """Initialize the encryption service.

        Args:
            secret_key: A 32-byte key for AES-256. If not provided, one should
                       be loaded from the application's configuration.
        """
        if secret_key is None:
            raise ValueError(
                "Secret key must be provided. Generate one using "
                "EncryptionService.generate_key()"
            )
        if len(secret_key) != 32:
            raise ValueError("Secret key must be exactly 32 bytes for AES-256")

        self.aesgcm = AESGCM(secret_key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new random 32-byte key suitable for AES-256.

        Returns:
            A 32-byte random key.
        """
        return AESGCM.generate_key(bit_length=256)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string using AES-256-GCM.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded string containing the nonce and ciphertext.
            Format: base64(nonce + ciphertext)
        """
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(
            nonce,
            plaintext.encode('utf-8'),
            associated_data=None
        )
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('ascii')

    def decrypt(self, encrypted_str: str) -> str:
        """Decrypt an encrypted string that was encrypted with encrypt().

        Args:
            encrypted_str: Base64-encoded string containing nonce and ciphertext.

        Returns:
            The decrypted plaintext string.

        Raises:
            cryptography.exceptions.InvalidTag: If the ciphertext has been tampered with.
        """
        encrypted_data = base64.b64decode(encrypted_str.encode('ascii'))
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        plaintext_bytes = self.aesgcm.decrypt(
            nonce,
            ciphertext,
            associated_data=None
        )
        return plaintext_bytes.decode('utf-8')


def get_encryption_service() -> EncryptionService:
    """Get encryption service with key from environment variable.

    Returns:
        EncryptionService instance

    Raises:
        ValueError: If ENCRYPTION_KEY environment variable is not set
    """
    encryption_key_hex = os.getenv("ENCRYPTION_KEY")
    if not encryption_key_hex:
        raise ValueError(
            "ENCRYPTION_KEY environment variable is not set. "
            "Generate one with: python -c \"from query_forwarder.crypto import "
            "EncryptionService; print(EncryptionService.generate_key().hex())\""
        )
    try:
        encryption_key = bytes.fromhex(encryption_key_hex)
    except ValueError as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format (must be hex): {e}")

    return EncryptionService(secret_key=encryption_key)
