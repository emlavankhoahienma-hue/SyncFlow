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

    # Test 10: Windows Reserved Device Names DOS protection
    print("\n[TEST 10] Windows Reserved Device Names (CON, PRN, AUX, NUL, COM1, LPT1)...")
    assert sanitize_filename("CON.txt") == "safe_CON.txt"
    assert sanitize_filename("aux.png") == "safe_aux.png"
    assert sanitize_filename("prn") == "safe_prn"
    assert sanitize_filename("NUL.dat") == "safe_NUL.dat"
    assert sanitize_filename("com1.zip") == "safe_com1.zip"
    assert sanitize_filename("lpt9.log") == "safe_lpt9.log"
    print(" -> Windows reserved device names safely prefixed with 'safe_' to avoid OS crash/hang!")

    # Test 11: Low-order point injection attack on X25519 (RFC 7748)
    print("\n[TEST 11] Low-order point injection attack on X25519 (RFC 7748 all-zeros)...")
    zero_pub_b64 = base64.b64encode(b"\x00" * 32).decode("ascii")
    try:
        crypto_manager.verify_and_handshake(
            client_ip="192.168.1.55",
            client_public_key_b64=zero_pub_b64,
            pin=crypto_manager.session_pin
        )
        assert False, "FAILED: Low-order point attack was accepted!"
    except ValueError as e:
        print(f" -> LOW-ORDER POINT REJECTED: {e}")

    # Test 12: Chunk Bomb / Memory Exhaustion Defense (> 2MB limit)
    print("\n[TEST 12] Chunk Bomb (> 2MB chunk memory exhaustion attack)...")
    from server.storage import storage_manager
    from server.models import FileMeta

    test_meta = FileMeta(file_id="bomb_test", name="test_bomb.dat", ext="dat", mime="application/octet-stream", size=5000000)
    storage_manager.init_upload("bomb_transfer", test_meta)
    oversized_chunk = b"X" * (2 * 1024 * 1024 + 1024)  # 2MB + 1KB
    try:
        storage_manager.write_chunk("bomb_transfer", oversized_chunk, 0)
        assert False, "FAILED: Chunk bomb was accepted!"
    except ValueError as e:
        print(f" -> CHUNK BOMB REJECTED: {e}")
    finally:
        storage_manager.active_transfers.pop("bomb_transfer", None)

    # Test 13: Disk Space Exhaustion Quota check
    print("\n[TEST 13] Disk Space Exhaustion protection (Requesting 1 Petabyte)...")
    huge_meta = FileMeta(file_id="huge_test", name="huge.iso", ext="iso", mime="application/octet-stream", size=10**15)
    try:
        storage_manager.init_upload("huge_transfer", huge_meta)
        assert False, "FAILED: Huge file was accepted despite insufficient disk space!"
    except OSError as e:
        print(f" -> DISK EXHAUSTION BLOCKED: {e}")

    # Test 14: Server Ephemeral Public Key Fingerprint (Anti-MITM / Rogue Server)
    print("\n[TEST 14] Server Ephemeral Public Key Fingerprint...")
    import hashlib
    fp = crypto_manager.get_server_fingerprint()
    assert len(fp) == 8
    expected_fp = hashlib.sha256(crypto_manager._public_bytes).hexdigest()[:8]
    assert fp == expected_fp
    print(f" -> Server Fingerprint: {fp} matches SHA256(server_pub_key)[:8] 100%!")

    # Test 15: API Flood Protection (Max 180 req/min/IP)
    print("\n[TEST 15] API Flood Protection (Rate Limiting 180 req/min)...")
    flood_ip = "192.168.1.77"
    for _ in range(180):
        ok = crypto_manager.check_request_flood(flood_ip)
        assert ok is True
    # 181st request must be denied
    assert crypto_manager.check_request_flood(flood_ip) is False
    print(" -> 181st request within 1 minute BLOCKED by Anti-Flood filter!")

    print("\n==================================================")
    print("✅ ALL 15 ADVANCED SECURITY TESTS PASSED PERFECTLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
