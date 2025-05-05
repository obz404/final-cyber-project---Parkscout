"""
aes_cipher.py

Provides a simple AES-CTR encryption/decryption wrapper using PyCryptodome.

Classes:
    Cipher: Encapsulates AES encryption and decryption in CTR mode.
"""

from Cryptodome.Cipher import AES

class Cipher:
    """
    AES-CTR cipher for encrypting and decrypting byte streams.

    This class encapsulates AES encryption and decryption in CTR mode,
    using a static key and nonce provided at initialization.

    Attributes:
        key (bytes): Symmetric key for AES operations. Must be 16, 24, or 32 bytes long.
        nonce (bytes): Nonce (initialization vector) for CTR mode. Should be unique per encryption session.
    """

    def __init__(self, key: bytes, nonce: bytes):
        """
        Initialize the Cipher with a secret key and nonce.

        Args:
            key (bytes): The AES key. Length must be valid for AES (16, 24, or 32 bytes).
            nonce (bytes): The CTR mode nonce. Must be unique for each encryption context.
        """
        self.key = key
        self.nonce = nonce

    def aes_encrypt(self, plaintext_bytes: bytes) -> bytes:
        """
        Encrypt plaintext using AES in CTR mode.

        Args:
            plaintext_bytes (bytes): Raw data to encrypt.

        Returns:
            bytes: The encrypted ciphertext.
        """
        # Create a new AES cipher object in CTR mode with the given key and nonce
        cipher = AES.new(self.key, AES.MODE_CTR, nonce=self.nonce)
        # Encrypt and return ciphertext
        return cipher.encrypt(plaintext_bytes)

    def aes_decrypt(self, ciphertext_bytes: bytes) -> str:
        """
        Decrypt ciphertext using AES in CTR mode.

        Args:
            ciphertext_bytes (bytes): Encrypted data to decrypt.

        Returns:
            str: The decrypted plaintext, decoded as a UTF-8 string.
        """
        # Create a new AES cipher object in CTR mode with the same key and nonce
        cipher = AES.new(self.key, AES.MODE_CTR, nonce=self.nonce)
        # Decrypt to raw bytes, then decode to UTF-8 text
        decrypted_bytes = cipher.decrypt(ciphertext_bytes)
        return decrypted_bytes.decode("utf-8")
