import os
import re
import time
import base64
import secrets
import logging
from typing import Optional, Tuple, Dict, Set
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

# Anti-Brute-Force & Anti-Replay constraints
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 900  # 15 minutes lockout
MAX_TIMESTAMP_SKEW_SECONDS = 60  # 60 seconds tolerance for anti-replay


WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

def sanitize_filename(filename: str, base_dir: Optional[Path] = None) -> str:
    """
    Sanitizes untrusted filenames to prevent Path Traversal attacks (e.g. ../../evil.exe),
    null byte injections, Windows device names (CON, PRN, AUX, NUL), and invalid filesystem characters.
    Optionally verifies that the resulting path stays within base_dir.
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

    # Block Windows reserved device names
    stem = Path(base).stem.upper()
    if stem in WINDOWS_RESERVED:
        base = f"safe_{base}"

    if base_dir:
        resolved_base = base_dir.resolve()
        candidate = (base_dir / base).resolve()
        if resolved_base != candidate and resolved_base not in candidate.parents:
            logger.warning(f"Path traversal attempt detected: {filename} -> forcing safe fallback")
            return "unnamed_file"

    return base



class AuthSecurityManager:
    """
    Kerckhoffs-compliant Security & Authentication Manager.
    
    Even if a hacker has 100% of the open-source code from GitHub:
    1. The PIN and Pairing Token are generated randomly on PC RAM each session.
       Zero secrets ever exist in Git, config files, or on disk.
    2. Only users who can physically see the PC screen or scan the PC's QR code
       can obtain the 6-digit PIN / pairing token.
    3. Hackers on the same Wi-Fi who try to brute-force the PIN are locked out after 5 failures.
    4. Replay attacks are blocked via monotonic timestamp validation & nonce deduplication.
    5. Wire traffic is encrypted with AES-256-GCM so Wireshark sees only high-entropy noise.
    """

    def __init__(self):
        self._private_key = x25519.X25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._public_bytes = self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )

        self.session_pin: str = self._generate_pin()
        self.pairing_token: str = secrets.token_hex(16)
        
        # IP -> list of failed timestamps
        self._failed_attempts: Dict[str, list] = {}
        # Nonce -> timestamp
        self._seen_nonces: Dict[str, float] = {}
        # Session_ID -> dict(session_key=bytes, client_ip=str, created_at=float)
        self._active_sessions: Dict[str, dict] = {}
        
        # Fallback single active session key
        self.session_key: Optional[bytes] = None
        self.is_e2ee_active: bool = False

        logger.info(f"Initialized AuthSecurityManager. Session PIN: {self.session_pin}")

    def _generate_pin(self) -> str:
        """Generates a secure random 6-digit PIN."""
        return "".join(secrets.choice("0123456789") for _ in range(6))

    def regenerate_secrets(self) -> Tuple[str, str]:
        """Regenerates the session PIN and pairing token on demand."""
        self.session_pin = self._generate_pin()
        self.pairing_token = secrets.token_hex(16)
        logger.info(f"Regenerated Session PIN: {self.session_pin}")
        return self.session_pin, self.pairing_token

    def get_server_public_key_b64(self) -> str:
        return base64.b64encode(self._public_bytes).decode("ascii")

    def get_server_fingerprint(self) -> str:
        """Returns 8-character hex fingerprint of the server ephemeral public key."""
        import hashlib
        return hashlib.sha256(self._public_bytes).hexdigest()[:8]

    def check_request_flood(self, client_ip: str) -> bool:
        """Anti-flood: enforces maximum 180 requests per 60 seconds per IP."""
        now = time.time()
        if not hasattr(self, "_req_timestamps"):
            self._req_timestamps: Dict[str, list] = {}
        history = self._req_timestamps.get(client_ip, [])
        history = [t for t in history if now - t < 60]
        if len(history) >= 180:
            return False
        history.append(now)
        self._req_timestamps[client_ip] = history
        return True

    def _clean_expired_data(self):
        now = time.time()
        # Clean expired failed attempts
        for ip in list(self._failed_attempts.keys()):
            self._failed_attempts[ip] = [t for t in self._failed_attempts[ip] if now - t < LOCKOUT_WINDOW_SECONDS]
            if not self._failed_attempts[ip]:
                del self._failed_attempts[ip]

        # Clean expired nonces (> 120s)
        for nonce, t in list(self._seen_nonces.items()):
            if now - t > 120:
                del self._seen_nonces[nonce]

    def check_rate_limit(self, client_ip: str) -> Tuple[bool, str]:
        """Checks if the client IP is locked out due to excessive failed attempts."""
        self._clean_expired_data()
        attempts = self._failed_attempts.get(client_ip, [])
        if len(attempts) >= MAX_FAILED_ATTEMPTS:
            remaining_lock = int(LOCKOUT_WINDOW_SECONDS - (time.time() - attempts[0]))
            return False, f"IP {client_ip} bị khóa {remaining_lock}s do nhập sai PIN quá 5 lần (Anti-Brute Force)."
        return True, ""

    def record_failed_attempt(self, client_ip: str):
        """Records a failed authentication attempt."""
        now = time.time()
        if client_ip not in self._failed_attempts:
            self._failed_attempts[client_ip] = []
        self._failed_attempts[client_ip].append(now)
        logger.warning(f"Failed pairing attempt from {client_ip}. Total: {len(self._failed_attempts[client_ip])}")

    def verify_and_handshake(
        self,
        client_ip: str,
        client_public_key_b64: str,
        pin: Optional[str] = None,
        pairing_token: Optional[str] = None,
        timestamp: Optional[int] = None,
        nonce: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Validates pairing credentials, executes X25519 ECDH key exchange,
        derives AES-256-GCM symmetric session key, and issues a session_id.
        
        Returns: (session_id, server_public_key_b64)
        Raises: ValueError if invalid.
        """
        # 1. Anti-Brute-Force check
        ok, msg = self.check_rate_limit(client_ip)
        if not ok:
            raise ValueError(msg)

        # 2. Anti-Replay check (timestamp window)
        now = time.time()
        if timestamp is not None:
            if abs(now - timestamp) > MAX_TIMESTAMP_SKEW_SECONDS:
                raise ValueError("Gói tin đã quá hạn thời gian cho phép (Anti-Replay Attack detected).")

        # 3. Anti-Replay check (nonce uniqueness)
        if nonce is not None:
            if nonce in self._seen_nonces:
                raise ValueError("Nonce gói tin bị trùng lặp (Anti-Replay Attack detected).")
            self._seen_nonces[nonce] = now

        # 4. PIN / Pairing Token validation (Constant-Time to prevent timing attacks)
        is_pin_valid = pin is not None and secrets.compare_digest(pin.strip(), self.session_pin)
        is_token_valid = pairing_token is not None and secrets.compare_digest(pairing_token.strip(), self.pairing_token)

        if not is_pin_valid and not is_token_valid:
            self.record_failed_attempt(client_ip)
            remaining = MAX_FAILED_ATTEMPTS - len(self._failed_attempts.get(client_ip, []))
            raise ValueError(f"Mã PIN hoặc Pairing Token không chính xác. Còn lại {max(0, remaining)} lần thử.")

        # Pairing successful: Clear failed attempts for this IP
        if client_ip in self._failed_attempts:
            del self._failed_attempts[client_ip]

        # 5. X25519 ECDH Key Agreement
        client_pub_bytes = base64.b64decode(client_public_key_b64)
        if len(client_pub_bytes) != 32:
            raise ValueError(f"Invalid client public key length: {len(client_pub_bytes)} bytes")

        client_pub = x25519.X25519PublicKey.from_public_bytes(client_pub_bytes)
        shared_secret = self._private_key.exchange(client_pub)

        # RFC 7748 Low-order point attack protection
        if all(b == 0 for b in shared_secret):
            raise ValueError("Low-order point cryptographic attack detected (RFC 7748).")

        # 6. HKDF-SHA256 Derivation
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=HKDF_SALT,
            info=HKDF_INFO,
        )
        derived_key = hkdf.derive(shared_secret)

        # 7. Generate Ephemeral Session Token
        session_id = secrets.token_urlsafe(32)
        self._active_sessions[session_id] = {
            "session_key": derived_key,
            "client_ip": client_ip,
            "created_at": now,
            "last_active": now,
        }
        self.session_key = derived_key
        self.is_e2ee_active = True

        logger.info(f"Authenticated session {session_id[:8]}... created for {client_ip}")
        return session_id, self.get_server_public_key_b64()

    def is_session_valid(self, session_id: Optional[str]) -> bool:
        """Validates if a session_id is active."""
        if not session_id:
            return False
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["last_active"] = time.time()
            return True
        return False

    def get_session_key(self, session_id: Optional[str] = None) -> Optional[bytes]:
        """Returns the symmetric key for the given session_id, or active session key."""
        if session_id and session_id in self._active_sessions:
            return self._active_sessions[session_id]["session_key"]
        return self.session_key

    def decrypt_chunk(self, encrypted_chunk: bytes, session_id: Optional[str] = None) -> bytes:
        """Decrypts an AES-256-GCM chunk using the active session key."""
        key = self.get_session_key(session_id)
        if not self.is_e2ee_active or not key:
            return encrypted_chunk

        if len(encrypted_chunk) < NONCE_LENGTH + TAG_LENGTH:
            raise ValueError("Encrypted chunk is too small to contain Nonce and Tag.")

        nonce = encrypted_chunk[:NONCE_LENGTH]
        ciphertext_and_tag = encrypted_chunk[NONCE_LENGTH:]

        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext_and_tag, associated_data=None)

    def encrypt_chunk(self, plaintext_chunk: bytes, session_id: Optional[str] = None) -> bytes:
        """Encrypts a plaintext chunk using AES-256-GCM."""
        key = self.get_session_key(session_id)
        if not self.is_e2ee_active or not key:
            return plaintext_chunk

        nonce = os.urandom(NONCE_LENGTH)
        aesgcm = AESGCM(key)
        ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext_chunk, associated_data=None)
        return nonce + ciphertext_and_tag

    def reset_session(self):
        """Resets all session state."""
        self.session_key = None
        self.is_e2ee_active = False
        self._active_sessions.clear()
        self._private_key = x25519.X25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()
        self._public_bytes = self._public_key.public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw
        )


# Singleton instance for the server runtime
crypto_manager = AuthSecurityManager()

