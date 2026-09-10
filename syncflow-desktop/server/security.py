import os
import re
import base64
import logging
from typing import Optional, Tuple
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger("syncflow.security")

# Constant parameters for session key derivation (HKDF-SHA256)
HKDF_SALT = b"SyncFlow-E2EE-v1"
HKDF_INFO = b"syncflow-file-transfer"
NONCE_LENGTH = 12
TAG_LENGTH = 16


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes untrusted filenames to prevent Path Traversal attacks (e.g. ../../evil.exe),
    null byte injections, and invalid filesystem characters.
    """
    if not filename:
        return "unnamed_file"

    # Normalize separators and take basename only
    base = os.path.basename(filename.replace("\\", "/"))
    
    # Strip null bytes and control characters
    base = re.sub(r'[\x00-\x1f\x7f]', '', base)
    
    # Replace illegal Windows/POSIX characters
    base = re.sub(r'[<>:"/\\|?*]', '_', base)
    
    # Strip leading/trailing dots and spaces
    base = base.strip(". ")
    
    if not base:
        base = "unnamed_file"

    return base


class CryptoSessionManager:
    """
    Zero-Secret End-to-End Encryption (E2EE) Session Manager.
    
    Keys are generated ephemerally in RAM upon server startup/handshake.
    NO PRIVATE KEYS OR SECRETS ARE EVER STORED ON DISK OR IN GIT.
    
    Protocol:
    1. Ephemeral X25519 keypair generated in memory.
    2. Client and Server exchange raw 32-byte public keys via /auth/handshake.
    3. Both sides perform ECDH key agreement: shared_secret = X25519(priv, pub).
    4. HKDF-SHA256 derives 256-bit symmetric key for AES-256-GCM.
    5. Wire format for each chunk: [12 bytes Nonce] + [Ciphertext] + [16 bytes Tag].
       Wireshark and network sniffers only see high-entropy random bytes.
       Any packet tampering in flight causes GCM authentication failure.
    """

    def __init__(self):
        self._generate_ephemeral_keypair()
        self.session_key: Optional[bytes] = None
        self.is_e2ee_active: bool = False

    def _generate_ephemeral_keypair(self):
        self._private_key = x25519.X25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._public_bytes = self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )
        logger.info("Generated fresh in-memory ephemeral X25519 keypair.")

    def get_server_public_key_b64(self) -> str:
        """Returns the server's public key encoded in Base64."""
        return base64.b64encode(self._public_bytes).decode("ascii")

    def perform_handshake(self, client_public_key_b64: str) -> str:
        """
        Receives client's Base64 public key (32 bytes raw),
        computes ECDH shared secret, derives AES-256-GCM session key,
        and returns server's ephemeral public key in Base64.
        """
        try:
            client_pub_bytes = base64.b64decode(client_public_key_b64)
            if len(client_pub_bytes) != 32:
                raise ValueError(f"Invalid client public key length: {len(client_pub_bytes)} bytes (expected 32)")

            client_pub = x25519.X25519PublicKey.from_public_bytes(client_pub_bytes)
            shared_secret = self._private_key.exchange(client_pub)

            # HKDF-SHA256 key derivation
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=HKDF_SALT,
                info=HKDF_INFO,
            )
            self.session_key = hkdf.derive(shared_secret)
            self.is_e2ee_active = True
            logger.info("E2EE Session established successfully via X25519 + HKDF-SHA256.")

            return self.get_server_public_key_b64()
        except Exception as e:
            logger.error(f"Handshake failed: {e}")
            self.is_e2ee_active = False
            self.session_key = None
            raise

    def decrypt_chunk(self, encrypted_chunk: bytes) -> bytes:
        """
        Decrypts an AES-256-GCM chunk.
        Input format: [12 bytes Nonce] + [Ciphertext] + [16 bytes Tag]
        """
        if not self.is_e2ee_active or not self.session_key:
            # If E2EE is not active, return chunk as plaintext (backward compatibility)
            return encrypted_chunk

        if len(encrypted_chunk) < NONCE_LENGTH + TAG_LENGTH:
            raise ValueError("Encrypted chunk is too small to contain Nonce and Tag.")

        nonce = encrypted_chunk[:NONCE_LENGTH]
        ciphertext_and_tag = encrypted_chunk[NONCE_LENGTH:]

        aesgcm = AESGCM(self.session_key)
        # AESGCM.decrypt expects ciphertext with appended 16-byte tag
        return aesgcm.decrypt(nonce, ciphertext_and_tag, associated_data=None)

    def encrypt_chunk(self, plaintext_chunk: bytes) -> bytes:
        """
        Encrypts a plaintext chunk using AES-256-GCM.
        Generates a cryptographically random 12-byte nonce for each chunk.
        Output format: [12 bytes Nonce] + [Ciphertext] + [16 bytes Tag]
        """
        if not self.is_e2ee_active or not self.session_key:
            return plaintext_chunk

        nonce = os.urandom(NONCE_LENGTH)
        aesgcm = AESGCM(self.session_key)
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext_chunk, associated_data=None)
        return nonce + ciphertext_and_tag

    def reset_session(self):
        """Wipes session key and generates a new ephemeral keypair."""
        self.session_key = None
        self.is_e2ee_active = False
        self._generate_ephemeral_keypair()


# Singleton instance for the server runtime
crypto_manager = CryptoSessionManager()
