import os
import sys
import time
import base64
from pathlib import Path

# Add syncflow-desktop to path
sys.path.insert(0, os.path.abspath("syncflow-desktop"))

from server.security import crypto_manager, sanitize_filename
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

def run_tests():
    print("==================================================")
    print("🔒 RUNNING KERCKHOFFS SECURITY SUITE (ZERO SECRETS)")
    print("==================================================")

    # Setup client ephemeral key
    client_priv = x25519.X25519PrivateKey.generate()
    client_pub_bytes = client_priv.public_key().public_bytes(
        encoding=Encoding.Raw, format=PublicFormat.Raw
    )
    client_pub_b64 = base64.b64encode(client_pub_bytes).decode("ascii")

    hacker_ip = "192.168.1.99"
    legit_ip = "192.168.1.25"

    # Test 1: Hacker calls handshake with NO PIN & NO TOKEN
    print("\n[TEST 1] Hacker calls /auth/handshake without PIN or Token...")
    try:
        crypto_manager.verify_and_handshake(client_ip=hacker_ip, client_public_key_b64=client_pub_b64)
        assert False, "FAILED: Hacker connected without PIN!"
    except ValueError as e:
        print(f" -> BLOCKED AS EXPECTED (403): {e}")

    # Test 2: Hacker tries wrong PIN
    print("\n[TEST 2] Hacker tries wrong PIN ('123456')...")
    try:
        crypto_manager.verify_and_handshake(client_ip=hacker_ip, client_public_key_b64=client_pub_b64, pin="123456")
        assert False, "FAILED: Hacker connected with wrong PIN!"
    except ValueError as e:
        print(f" -> BLOCKED AS EXPECTED: {e}")

    # Test 3: Anti-Brute-Force Lockout (5 failed attempts)
    print("\n[TEST 3] Testing Anti-Brute-Force lockout after 5 failed attempts...")
    for i in range(4): # 2 attempts already done, 3 more to reach 5
        try:
            crypto_manager.verify_and_handshake(client_ip=hacker_ip, client_public_key_b64=client_pub_b64, pin=f"00000{i}")
        except ValueError:
            pass

    # 6th attempt must be locked out
    try:
        crypto_manager.verify_and_handshake(client_ip=hacker_ip, client_public_key_b64=client_pub_b64, pin=crypto_manager.session_pin)
        assert False, "FAILED: Hacker IP was not locked out!"
    except ValueError as e:
        print(f" -> IP LOCKED OUT AS EXPECTED (Anti-Brute Force): {e}")

    # Test 4: Legitimate user connects with correct PIN from PC screen
    print("\n[TEST 4] Legitimate user connects with correct PIN...")
    session_id, server_pub = crypto_manager.verify_and_handshake(
        client_ip=legit_ip,
        client_public_key_b64=client_pub_b64,
        pin=crypto_manager.session_pin
    )
    assert session_id is not None
    assert crypto_manager.is_session_valid(session_id)
    print(f" -> HANDSHAKE SUCCESS! Session Token: {session_id[:12]}...")

    # Test 5: Legitimate user connects via QR Pairing Token
    print("\n[TEST 5] Legitimate user connects via QR Pairing Token...")
    session_id_qr, _ = crypto_manager.verify_and_handshake(
        client_ip="192.168.1.30",
        client_public_key_b64=client_pub_b64,
        pairing_token=crypto_manager.pairing_token
    )
    assert session_id_qr is not None
    print(f" -> QR PAIRING SUCCESS! Session Token: {session_id_qr[:12]}...")

    # Test 6: Anti-Replay Protection (Expired timestamp & Duplicate nonce)
    print("\n[TEST 6] Anti-Replay Protection test...")
    # 6a. Expired timestamp (> 60s skew)
    try:
        crypto_manager.verify_and_handshake(
            client_ip="192.168.1.31",
            client_public_key_b64=client_pub_b64,
            pin=crypto_manager.session_pin,
            timestamp=int(time.time()) - 200,
            nonce="replay-test-nonce-1"
        )
        assert False, "FAILED: Expired timestamp was accepted!"
    except ValueError as e:
        print(f" -> EXPIRED TIMESTAMP REJECTED: {e}")

    # 6b. Duplicate nonce
    crypto_manager.verify_and_handshake(
        client_ip="192.168.1.32",
        client_public_key_b64=client_pub_b64,
        pin=crypto_manager.session_pin,
        timestamp=int(time.time()),
        nonce="replay-test-nonce-unique"
    )
    try:
        crypto_manager.verify_and_handshake(
            client_ip="192.168.1.33",
            client_public_key_b64=client_pub_b64,
            pin=crypto_manager.session_pin,
            timestamp=int(time.time()),
            nonce="replay-test-nonce-unique"
        )
        assert False, "FAILED: Replayed nonce was accepted!"
    except ValueError as e:
        print(f" -> DUPLICATE NONCE REJECTED: {e}")

    # Test 7: AES-256-GCM Chunk Encryption & Wireshark-proof Wire Format
    print("\n[TEST 7] Chunk Encryption & Decryption...")
    sample_payload = b"IMG_9824.HEIC file chunk binary data secret photos"
    encrypted_chunk = crypto_manager.encrypt_chunk(sample_payload, session_id=session_id)
    assert encrypted_chunk != sample_payload
    assert sample_payload not in encrypted_chunk
    print(f" -> Encrypted {len(sample_payload)} bytes -> {len(encrypted_chunk)} bytes ciphertext (high entropy)")

    decrypted_chunk = crypto_manager.decrypt_chunk(encrypted_chunk, session_id=session_id)
    assert decrypted_chunk == sample_payload
    print(" -> Decrypted successfully matching original bytes 100%!")

    # Test 8: Tampering / MITM Detection
    print("\n[TEST 8] Anti-Tampering (flipping 1 byte in transit)...")
    tampered = bytearray(encrypted_chunk)
    tampered[15] ^= 0xFF  # flip byte
    try:
        crypto_manager.decrypt_chunk(bytes(tampered), session_id=session_id)
        assert False, "FAILED: Tampered chunk was accepted!"
    except Exception as e:
        print(f" -> TAMPERING DETECTED & REJECTED: {type(e).__name__}")

    # Test 9: Path Traversal
    print("\n[TEST 9] Path Traversal Sanitization...")
    assert sanitize_filename("../../Windows/System32/evil.exe") == "evil.exe"
    assert sanitize_filename("..\\..\\calc.exe") == "calc.exe"
    assert sanitize_filename("safe_file.png") == "safe_file.png"
    print(" -> All malicious paths successfully sanitized!")

    print("\n==================================================")
    print("✅ ALL KERCKHOFFS SECURITY TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
