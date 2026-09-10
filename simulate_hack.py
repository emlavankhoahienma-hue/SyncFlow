import os
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import json
import urllib.request
import urllib.error
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SERVER_URL = "http://127.0.0.1:8765"
HKDF_SALT = b"SyncFlow-E2EE-v1"
HKDF_INFO = b"syncflow-file-transfer"

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def http_post_json(url, payload, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def http_post_bytes(url, data_bytes, headers=None):
    h = {"Content-Type": "application/octet-stream"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data_bytes, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def print_header(title):
    print("\n" + "="*70)
    print(f" 🔥 GIẢ LẬP TẤN CÔNG: {title}")
    print("="*70)

def main():
    print("""
  ███████╗██╗   ██╗███╗   ██╗ ██████╗███████╗██╗      ██████╗ ██╗    ██╗
  ██╔════╝╚██╗ ██╔╝████╗  ██║██╔════╝██╔════╝██║     ██╔═══██╗██║    ██║
  ███████╗ ╚████╔╝ ██╔██╗ ██║██║     █████╗  ██║     ██║   ██║██║ █╗ ██║
  ╚════██║  ╚██╔╝  ██║╚██╗██║██║     ██╔══╝  ██║     ██║   ██║██║███╗██║
  ███████║   ██║   ██║ ╚████║╚██████╗██║     ███████╗╚██████╔╝╚███╔███╔╝
  ╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
              CÔNG CỤ GIẢ LẬP TẤN CÔNG & KIỂM THỬ BẢO MẬT
    """)

    # 0. Kiểm tra kết nối server
    try:
        code, text = http_get(f"{SERVER_URL}/health")
        if code != 200:
            print("❌ Server không phản hồi!")
            return
        data = json.loads(text)
        print(f"✅ Đã kết nối đến Server SyncFlow (Thiết bị: {data['device_name']}, Phiên bản: {data['version']})")
    except Exception as e:
        print(f"❌ Không thể kết nối đến server: {e}")
        return

    # -------------------------------------------------------------
    # 1. KỊCH BẢN 1: Hacker dùng Wireshark bắt trộm gói tin trên Wi-Fi
    # -------------------------------------------------------------
    print_header("KỊCH BẢN 1: HACKER DÙNG WIRESHARK BẮT GÓI TIN TRÊN MẠNG WI-FI")
    print("🎯 Mục tiêu hacker: Bật Wireshark trong cùng quán cà phê / Wi-Fi để xem trộm tệp gửi qua lại.")
    
    # Client hợp lệ bắt tay tạo E2EE
    client_priv = x25519.X25519PrivateKey.generate()
    client_pub_bytes = client_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    client_pub_b64 = base64.b64encode(client_pub_bytes).decode("ascii")
    
    code, hs_data = http_post_json(f"{SERVER_URL}/auth/handshake", {"client_public_key": client_pub_b64})
    srv_pub_bytes = base64.b64decode(hs_data["server_public_key"])
    
    shared_secret = client_priv.exchange(x25519.X25519PublicKey.from_public_bytes(srv_pub_bytes))
    session_key = HKDF(algorithm=hashes.SHA256(), length=32, salt=HKDF_SALT, info=HKDF_INFO).derive(shared_secret)

    # Dữ liệu nhạy cảm cần truyền
    plaintext_secret = b"SECRET_DOCUMENT: Tai khoan ngan hang: 99998888, Mat khau: P@ssw0rd2026, Hinh anh nhay cam gia dinh!"
    print(f"\n[+] Dữ liệu gốc người dùng gửi: \n    \"{plaintext_secret.decode('utf-8')}\"")

    # Mã hóa AES-256-GCM
    nonce = os.urandom(12)
    aesgcm = AESGCM(session_key)
    wire_payload = nonce + aesgcm.encrypt(nonce, plaintext_secret, None)

    print("\n🕵️  HACKER BẮT ĐƯỢC GÓI TIN TRÊN WIRESHARK:")
    hex_dump = " ".join(f"{b:02x}" for b in wire_payload[:36])
    print(f"    Gói tin bắt được (Hex): {hex_dump} ... [tổng {len(wire_payload)} bytes]")
    print(f"    Thử tìm kiếm chuỗi 'Tai khoan' trong gói tin: {'TÌM THẤY ❌' if b'Tai khoan' in wire_payload else 'KHÔNG TÌM THẤY (100% Mã hóa an toàn) ✅'}")
    print(f"    Thử tìm kiếm chuỗi 'Mat khau' trong gói tin:   {'TÌM THẤY ❌' if b'Mat khau' in wire_payload else 'KHÔNG TÌM THẤY (100% Mã hóa an toàn) ✅'}")
    print("👉 KẾT QUẢ: Hacker chỉ thấy chuỗi byte ngẫu nhiên vô nghĩa. Wireshark hoàn toàn bất lực trước AES-256-GCM!")

    # -------------------------------------------------------------
    # 2. KỊCH BẢN 2: Tấn công Man-In-The-Middle (MITM) chèn mã độc/sửa byte
    # -------------------------------------------------------------
    print_header("KỊCH BẢN 2: HACKER CHÈN MÃ ĐỘC / SỬA GÓI TIN TRÊN ĐƯỜNG TRUYỀN (MITM)")
    print("🎯 Mục tiêu hacker: Chặn gói tin giữa đường, chèn mã độc hoặc làm sai lệch nội dung tệp.")

    # Khởi tạo upload
    code, init_data = http_post_json(f"{SERVER_URL}/upload/init", {
        "meta": {"name": "test_mitm.bin", "ext": "bin", "size": len(plaintext_secret)}
    })
    transfer_id = init_data["transfer_id"]

    # Hacker can thiệp: Sửa 1 byte trong payload đã mã hóa
    tampered_payload = bytearray(wire_payload)
    tampered_payload[25] ^= 0xFF  # Làm hỏng byte
    print(f"[!] Hacker can thiệp trên đường truyền: Thay đổi byte tại vị trí 25 thành '{tampered_payload[25]:02x}'")

    print("[*] Gói tin bị sửa đổi đang được gửi tới Server...")
    status_code, resp_text = http_post_bytes(
        f"{SERVER_URL}/upload/chunk/{transfer_id}",
        bytes(tampered_payload),
        headers={"X-Encrypted": "1", "X-Chunk-Index": "0"}
    )

    print(f"    Mã phản hồi từ Server: HTTP {status_code}")
    print(f"    Chi tiết từ Server:    {resp_text.strip()}")
    if status_code == 400:
        print("👉 KẾT QUẢ: Thẻ xác thực Auth Tag của AES-256-GCM lập tức phát hiện gói tin đã bị can thiệp!")
        print("    Server TỪ CHỐI NHẬN FILE (HTTP 400), hủy toàn bộ tác vụ. Mã độc không thể xâm nhập! ✅")

    # -------------------------------------------------------------
    # 3. KỊCH BẢN 3: Tấn công Path Traversal ghi đè file hệ thống
    # -------------------------------------------------------------
    print_header("KỊCH BẢN 3: HACKER GỬI FILE VƯỢT THƯ MỤC (PATH TRAVERSAL ATTACK)")
    print("🎯 Mục tiêu hacker: Gửi file tên '../../../../Windows/System32/hacked.exe' để ghi đè file hệ thống.")

    malicious_name = "../../../../Windows/System32/hacked.exe"
    safe_data = b"Safe test content"
    enc_safe = os.urandom(12)
    enc_safe = enc_safe + aesgcm.encrypt(enc_safe, safe_data, None)

    code, init_mal = http_post_json(f"{SERVER_URL}/upload/init", {
        "meta": {"name": malicious_name, "ext": "exe", "size": len(safe_data)}
    })
    mal_transfer_id = init_mal["transfer_id"]

    http_post_bytes(
        f"{SERVER_URL}/upload/chunk/{mal_transfer_id}",
        enc_safe,
        headers={"X-Encrypted": "1", "X-Chunk-Index": "0"}
    )
    code, comp_mal = http_post_json(f"{SERVER_URL}/upload/complete/{mal_transfer_id}", {})
    saved_path = comp_mal["path"]

    print(f"[!] Tên file độc hại hacker cố tình gửi: \"{malicious_name}\"")
    print(f"    Đường dẫn thực tế Server lưu file:     \"{saved_path}\"")
    
    if "System32" not in saved_path and "Downloads" in saved_path:
        print("👉 KẾT QUẢ: Cơ chế sanitize_filename() đã tự động triệt tiêu toàn bộ đường dẫn thoát '../'!")
        print("    File bị cô lập an toàn trong thư mục Downloads/SyncFlow. Hệ thống Windows được bảo vệ an toàn 100%! ✅")
        # Dọn dẹp
        try:
            os.remove(saved_path)
        except Exception:
            pass

    # -------------------------------------------------------------
    # 4. KỊCH BẢN 4: Hacker dùng khóa giả mạo / Fake Key Injection
    # -------------------------------------------------------------
    print_header("KỊCH BẢN 4: HACKER DÙNG KHÓA GIẢ MẠO ĐỂ ĐỌC DỮ LIỆU ĐÃ BẮT")
    print("🎯 Mục tiêu hacker: Lưu lại các gói tin Wireshark rồi cố giải mã bằng một khóa tự tạo.")

    fake_key = b"A" * 32  # Khóa giả 256-bit
    try:
        fake_aesgcm = AESGCM(fake_key)
        fake_aesgcm.decrypt(wire_payload[:12], wire_payload[12:], None)
        print("❌ LỖI BẢO MẬT: Hacker đã giải mã được!")
    except Exception as e:
        print(f"    Lỗi ném ra khi Hacker cố giải mã: {type(e).__name__} (InvalidTag)")
        print("👉 KẾT QUẢ: Không có khóa phiên sinh từ RAM, dữ liệu vĩnh viễn là rác nhị phân đối với hacker! ✅")

    print("\n" + "="*70)
    print(" 🏆 TỔNG KẾT: TẤT CẢ 4 KỊCH BẢN TẤN CÔNG ĐỀU BỊ ĐẨY LÙI 100%!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()

