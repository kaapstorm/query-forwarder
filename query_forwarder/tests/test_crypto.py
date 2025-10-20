"""Tests for encryption utilities."""
import pytest

from query_forwarder.crypto import EncryptionService


def test_encrypt_decrypt_roundtrip():
    """Test that decrypt() successfully decrypts ciphertext from encrypt()."""
    secret_key = EncryptionService.generate_key()
    service = EncryptionService(secret_key=secret_key)

    plaintext = "my_secret_password"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)

    assert decrypted == plaintext


def test_encrypt_produces_different_ciphertext_each_time():
    """Test that encrypt() produces different ciphertext for same plaintext due to random nonce."""
    secret_key = EncryptionService.generate_key()
    service = EncryptionService(secret_key=secret_key)

    plaintext = "my_secret_password"
    encrypted1 = service.encrypt(plaintext)
    encrypted2 = service.encrypt(plaintext)

    assert encrypted1 != encrypted2
    assert service.decrypt(encrypted1) == plaintext
    assert service.decrypt(encrypted2) == plaintext


def test_encrypt_decrypt_with_special_characters():
    """Test that encrypt/decrypt works with special characters and unicode."""
    secret_key = EncryptionService.generate_key()
    service = EncryptionService(secret_key=secret_key)

    plaintext = "pássw0rd!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)

    assert decrypted == plaintext


def test_encrypt_decrypt_with_empty_string():
    """Test that encrypt/decrypt works with empty string."""
    secret_key = EncryptionService.generate_key()
    service = EncryptionService(secret_key=secret_key)

    plaintext = ""
    encrypted = service.encrypt(plaintext)
    decrypted = service.decrypt(encrypted)

    assert decrypted == plaintext


def test_decrypt_with_wrong_key_raises_error():
    """Test that decrypt() raises an error when using wrong key."""
    key1 = EncryptionService.generate_key()
    key2 = EncryptionService.generate_key()

    service1 = EncryptionService(secret_key=key1)
    service2 = EncryptionService(secret_key=key2)

    plaintext = "my_secret_password"
    encrypted = service1.encrypt(plaintext)

    with pytest.raises(Exception):
        service2.decrypt(encrypted)


def test_decrypt_with_tampered_ciphertext_raises_error():
    """Test that decrypt() raises an error if ciphertext has been tampered with."""
    secret_key = EncryptionService.generate_key()
    service = EncryptionService(secret_key=secret_key)

    plaintext = "my_secret_password"
    encrypted = service.encrypt(plaintext)

    tampered = encrypted[:-4] + "AAAA"

    with pytest.raises(Exception):
        service.decrypt(tampered)


def test_generate_key_produces_32_bytes():
    """Test that generate_key() produces 32-byte keys suitable for AES-256."""
    key = EncryptionService.generate_key()
    assert len(key) == 32


def test_generate_key_produces_unique_keys():
    """Test that generate_key() produces unique keys each time."""
    key1 = EncryptionService.generate_key()
    key2 = EncryptionService.generate_key()
    assert key1 != key2


def test_init_without_key_raises_error():
    """Test that initializing without a key raises ValueError."""
    with pytest.raises(ValueError, match="Secret key must be provided"):
        EncryptionService(secret_key=None)


def test_init_with_wrong_key_length_raises_error():
    """Test that initializing with wrong key length raises ValueError."""
    with pytest.raises(ValueError, match="Secret key must be exactly 32 bytes"):
        EncryptionService(secret_key=b"too_short")