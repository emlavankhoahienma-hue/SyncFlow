# ⚡ SyncFlow — Hệ Sinh Thái Đồng Bộ File 2 Chiều iOS & Máy Tính

> **Giải pháp truyền file LAN tốc độ cao, bảo toàn 100% chất lượng gốc, không thông qua bất kỳ máy chủ đám mây trung gian nào.**  
> Thiết kế chuẩn Design System **Terra Cotta** (`#E2725B`), hỗ trợ xem trước tệp trực tiếp bằng **Apple QuickLook** và chia sẻ nhanh qua **iOS ShareSheet**.

---

## 📑 Mục Lục
1. [Kiến Trúc & Điểm Nổi Bật](#1-kiến-trúc--điểm-nổi-bật)
2. [Bảo Mật Cấp Cao: Chống Nghe Lén Wireshark & Zero-Secret E2EE](#2-bảo-mật-cấp-cao-chống-nghe-lén-wireshark--zero-secret-e2ee)
3. [Cài Đặt & Chạy Trên Máy Tính (Windows / macOS / Linux)](#3-cài-đặt--chạy-trên-máy-tính)
4. [Cài Đặt Ứng Dụng iPhone (Sideload IPA)](#4-cài-đặt-ứng-dụng-iphone-sideload-ipa)
   - [Cách 1: Cài qua Sideloadly (Khuyên dùng - Miễn phí)](#cách-1-cài-qua-sideloadly)
   - [Cách 2: Cài qua TrollStore (Dành cho máy có TrollStore)](#cách-2-cài-qua-trollstore)
   - [Cách 3: Cài qua AltStore](#cách-3-cài-qua-altstore)
5. [Hướng Dẫn Sử Dụng Chi Tiết](#5-hướng-dẫn-sử-dụng-chi-tiết)
   - [Gửi file từ Máy tính sang iPhone](#51-gửi-file-từ-máy-tính-sang-iphone)
   - [Xem trước file & Chia sẻ trên iPhone (QuickLook & ShareSheet)](#52-xem-trước-file--chia-sẻ-trên-iphone)
   - [Gửi ảnh / video / tài liệu từ iPhone lên Máy tính](#53-gửi-từ-iphone-lên-máy-tính)
   - [Tự động chuyển đổi định dạng (HEIC→PNG, MOV→MP4)](#54-tự-động-chuyển-đổi-định-dạng)
6. [Xử Lý Sự Cố (Troubleshooting)](#6-xử-lý-sự-cố-troubleshooting)

---

## 1. Kiến Trúc & Điểm Nổi Bật

```
┌────────────────────────────────┐                 MẠNG NỘI BỘ (WI-FI LAN)                 ┌────────────────────────────────┐
│          iPhone (iOS)          │                                                         │       Máy Tính (Desktop)       │
│  • SwiftUI (iOS 17.0+)         │  ◄──────────── HTTP REST + WebSocket (:8765) ────────►  │  • Python 3.10+ & Flet 0.86    │
│  • Client thuần 2 chiều        │            AES-256-GCM Chunk E2EE (X25519)              │  • FastAPI Server + Zeroconf   │
│  • Apple QuickLook + ShareSheet│               Xác thực mã băm SHA-256 an toàn           │  • UI Terra Cotta Dark Mode    │
│  • Apple CryptoKit RAM-only    │               Chống nghe lén Wireshark 100%             │  • Cryptography RAM-only       │
└────────────────────────────────┘                                                         └────────────────────────────────┘
```

* **Máy tính là Server duy nhất**: Chạy FastAPI + WebSocket tại cổng `8765`, phát quảng bá Bonjour mDNS dịch vụ `_syncflow._tcp`.
* **iPhone là Client cho cả 2 chiều**:
  - Gửi lên PC: Upload chunk 1MB mã hoá AES-256-GCM, tự động nối tiếp khi mất sóng (Resume).
  - Tải về từ PC: Download chunk mã hoá E2EE hoặc có hỗ trợ `Range`, lưu vào thư mục `Documents` của app (hiển thị trực tiếp trong app Tệp/Files).
* **Bảo toàn tuyệt đối chất lượng**:
  - Tự động chuyển đổi HEIC → PNG (giữ nguyên độ sâu màu và độ phân giải).
  - Tự động chuyển đổi MOV/HEVC → MP4 chất lượng chuẩn điện ảnh (`CRF 18`, `ffmpeg` / `AVAssetExportSession`).
* **Không lưu trữ đám mây**: Toàn bộ dữ liệu đi thẳng trực tiếp giữa 2 thiết bị trong mạng Wi-Fi nội bộ với tốc độ tối đa của router (thường đạt 30–80 MB/s).

---

### 2. Bảo Mật Cấp Cao: Chuẩn Quân Sự Kerckhoffs & Zero-Secret E2EE

Ứng dụng tuân thủ nghiêm ngặt **Nguyên lý Kerckhoffs**: *"Một hệ thống mật mã phải an toàn ngay cả khi mọi thông tin về hệ thống (bao gồm toàn bộ mã nguồn trên GitHub) đều bị kẻ tấn công biết rõ."*

1. **Mã PIN 6 Số & Token Ghép Đôi Động Trên RAM (Không Lưu Trên Git)**:
   - Khi khởi động, Server Desktop tự động sinh một mã PIN 6 số (`secrets.choice`) và một Pairing Token 128-bit hoàn toàn ngẫu nhiên **chỉ tồn tại trong RAM máy tính**.
   - Mã PIN và Token chỉ hiển thị trực quan trên **màn hình máy tính** và được nhúng vào **mã QR**.
   - Bất kỳ ai trên cùng mạng Wi-Fi (dù đọc toàn bộ mã nguồn trên GitHub) cố gắng gửi lệnh handshake mà không có mã PIN đúng sẽ bị **chặn ngay lập tức (HTTP 403 Forbidden)**.

2. **Chống Tấn Công Dò Mật Khẩu (Anti-Brute Force Rate Limiter)**:
   - Nếu một địa chỉ IP trên mạng nội bộ thử sai mã PIN quá 5 lần, server sẽ lập tức **khóa IP đó trong 15 phút**. Kẻ tấn công không thể dùng bot tự động dò 1.000.000 tổ hợp PIN.

3. **Chống Tấn Công Phát Lại (Anti-Replay Protection)**:
   - Mọi gói tin bắt tay đều kèm theo timestamp và nonce ngẫu nhiên duy nhất.
   - Gói tin quá hạn $\pm 60$ giây hoặc nonce đã từng xuất hiện sẽ bị từ chối ngay lập tức, ngăn chặn việc hacker ghi âm lại gói tin mạng rồi phát lại sau.

4. **Chống Bắt Gói Tin Wireshark (Anti-Sniffing / AES-256-GCM E2EE)**:
   - Toàn bộ chunk truyền tải đều được mã hóa bằng **AES-256-GCM** với khóa đối xứng bắt tay qua **Curve25519 / X25519 ECDH + HKDF-SHA256**.
   - Bất kỳ ai dùng Wireshark, tcpdump, Charles Proxy chỉ thấy các byte ngẫu nhiên (entropy cao), không thể đọc được nội dung ảnh, video, tài liệu.

5. **Phát Hiện Can Thiệp Dữ Liệu (Anti-Tampering & MITM)**:
   - Thẻ xác thực **16-byte Poly1305/GCM Tag** bảo vệ toàn vẹn từng bit dữ liệu. Sửa đổi 1 bit sẽ lập tức làm sập phiên truyền và cảnh báo người dùng.

6. **Chống Vượt Thư Mục (Anti-Path Traversal)**:
   - Khử sạch toàn bộ `../`, `..\\`, ký tự điều khiển, và xác thực đường dẫn tuyệt đối đảm bảo file chỉ được lưu trong thư mục quy định.

---

## 3. Cài Đặt & Chạy Trên Máy Tính

### 3.1 Tải bản đóng gói sẵn (.zip) từ GitHub Releases (Khuyên dùng)
* Tải tệp `SyncFlow-Windows-x64.zip` từ mục **[Releases](https://github.com/emlavankhoahienma-hue/SyncFlow/releases)**.
* Giải nén và nhấp đúp vào `SyncFlow.exe` để sử dụng ngay lập tức mà không cần cài đặt Python.
* Nhấp chuột phải vào icon ứng dụng dưới Taskbar và chọn **Pin to taskbar** để tiện mở lần sau.

### 3.2 Chạy từ mã nguồn Python
1. Đảm bảo máy tính đã cài đặt **Python 3.10 trở lên** (khuyên dùng Python 3.11 hoặc 3.12).
2. Mở Command Prompt hoặc PowerShell tại thư mục dự án:
   ```bash
   cd syncflow-desktop
   pip install -r requirements.txt
   ```
3. Khởi chạy ứng dụng:
   ```bash
   python main.py
   ```
4. Ứng dụng Desktop sẽ tự khởi động:
   - Giao diện Flet chuẩn Terra Cotta mở lên.
   - Server FastAPI bắt đầu lắng nghe tại cổng `8765`.
   - Bonjour Service tự động phát quảng bá để iPhone nhận diện trong mạng Wi-Fi.

---

## 4. Cài Đặt Ứng Dụng iPhone (Sideload IPA)

File cài đặt iOS là file **`SyncFlow-unsigned.ipa`**. Bạn có thể tải file này từ mục **[Releases](https://github.com/emlavankhoahienma-hue/SyncFlow/releases)** trên GitHub hoặc file tạo từ GitHub Actions.

### Cách 1: Cài qua Sideloadly (Khuyên dùng - Miễn phí)
1. Tải phần mềm **[Sideloadly](https://sideloadly.io/)** (miễn phí cho Windows và Mac).
2. Kết nối iPhone với máy tính bằng cáp Lightning / Type-C (chọn **Tin cậy máy tính này / Trust This Computer** trên iPhone nếu được hỏi).
3. Mở Sideloadly:
   - Mục **iDevice**: Chọn thiết bị iPhone của bạn.
   - Kéo tệp `SyncFlow-unsigned.ipa` thả vào ô vuông IPA lớn trên Sideloadly.
   - Mục **Apple ID**: Nhập email tài khoản Apple ID cá nhân của bạn.
   - Nhấn nút **Start**. Nhập mật khẩu Apple ID khi được yêu cầu (và mã xác thực 2 lớp gửi về điện thoại).
4. Khi Sideloadly báo **Done**:
   - Trên iPhone, vào **Cài đặt (Settings) > Cài đặt chung (General) > Quản lý VPN & Thiết bị (VPN & Device Management)**.
   - Nhấp vào tài khoản Apple ID của bạn và bấm **Tin cậy (Trust)**.
   - Bật **Chế độ nhà phát triển (Developer Mode)** tại **Cài đặt > Quyền riêng tư & Bảo mật > Chế độ nhà phát triển** (nếu dùng iOS 16+).

### Cách 2: Cài qua TrollStore (Dành cho máy có TrollStore)
- Mở file `SyncFlow-unsigned.ipa` bằng ứng dụng **TrollStore** trên iPhone.
- Chọn **Install**. Ứng dụng sẽ được cài đặt vĩnh viễn, không bao giờ bị hết hạn 7 ngày.

### Cách 3: Cài qua AltStore
- Mở ứng dụng AltStore trên iPhone, chuyển qua tab **My Apps**, nhấn dấu **+** ở góc trên và chọn file `SyncFlow-unsigned.ipa`.

---

## 5. Hướng Dẫn Sử Dụng Chi Tiết

### 5.1 Gửi file từ Máy tính sang iPhone
1. Trên máy tính, mở SyncFlow và chuyển sang tab **Gửi**.
2. Nhấn nút **Chọn file để gửi** (hoặc kéo thả tệp vào khung chứa). Hỗ trợ mọi loại tệp: ảnh, video, tài liệu PDF, zip,...
3. Nhấn **Đưa vào hàng đợi sẵn sàng cho iPhone tải**:
   - Nút sẽ có vòng quay loading báo hiệu đang chuẩn bị file.
   - Thông báo thành công sẽ xuất hiện cùng danh sách các tệp đang sẵn sàng chia sẻ trong mục `SendQueue`.
4. Trên iPhone:
   - Mở ứng dụng SyncFlow, vào tab **Nhận**.
   - Bạn sẽ thấy ngay danh sách các tệp trên máy tính. Nhấn nút **Tải**.
   - Tệp sẽ được tải trực tiếp về iPhone mà không bị gián đoạn hay nhảy màn hình.

### 5.2 Xem trước file & Chia sẻ trên iPhone
Sau khi tải file về iPhone, bạn có toàn quyền kiểm soát tệp ngay trong tab **Nhận**:
* **Xem trước tức thì (Apple QuickLook)**: Chạm trực tiếp vào bất kỳ tệp nào để mở trình xem toàn màn hình (xem ảnh chất lượng cao, phát video 4K, đọc PDF, xem văn bản).
* **Chia sẻ nhanh (ShareSheet)**: Bấm vào icon chia sẻ ↗️ (`square.and.arrow.up`) trên dòng tệp để gửi ngay qua **AirDrop**, **Zalo**, **Messenger**, **Telegram**, hoặc chọn **Lưu vào Tệp (Files)**.
* **Lưu vào Thư viện Ảnh (Photos)**: Đối với tệp hình ảnh và video, bấm nút icon ảnh 🖼️ để lưu thẳng vào Album Ảnh của iPhone.
* **Mở trong ứng dụng Tệp của iOS**: Mở ứng dụng **Tệp (Files)** trên iPhone > mục **Trên iPhone của tôi (On My iPhone)** > thư mục **SyncFlow** để quản lý các tệp đã tải về.

### 5.3 Gửi từ iPhone lên Máy tính
1. Trên iPhone, mở tab **Gửi**.
2. Chọn giữa 2 chế độ:
   - **Ảnh & Video**: Mở thư viện chọn hàng loạt ảnh/video gốc.
   - **Mọi loại file**: Mở trình duyệt tệp iOS để chọn tài liệu, file nén, nhạc,...
3. Bật tùy chọn **Tự động chuyển đổi định dạng** nếu muốn đổi ảnh HEIC sang PNG hoặc video MOV sang MP4.
4. Bấm **Bắt đầu gửi lên máy tính**. Tiến độ truyền tải và tốc độ MB/s sẽ hiển thị trực tiếp theo thời gian thực trên cả điện thoại và máy tính.
5. Trên máy tính, tệp nhận được sẽ tự động lưu vào thư mục `Downloads/SyncFlow`.

### 5.4 Tự Động Chuyển Đổi Định Dạng
| Định dạng gốc | Định dạng chuyển đổi | Chất lượng | Cơ chế xử lý |
|---|---|---|---|
| **HEIC / HEIF** | **PNG** | Giữ nguyên độ phân giải & độ sâu màu | `ImageIO` (iOS) / `pillow-heif` (PC) |
| **MOV (HEVC)** | **MP4** | Chuẩn hình ảnh sắc nét, CRF 18 visually lossless | `AVAssetExportSession` (iOS) / `ffmpeg` (PC) |

---

## 6. Xử Lý Sự Cố (Troubleshooting)

### ❓ iPhone báo "Chưa kết nối với máy tính"
1. **Chung mạng Wi-Fi**: Đảm bảo cả iPhone và máy tính đang kết nối vào **cùng một mạng Wi-Fi**.
2. **Tắt cách ly AP (AP Isolation)**: Một số router Wi-Fi công cộng (quán cà phê) chặn các thiết bị giao tiếp với nhau. Hãy dùng mạng gia đình hoặc phát Wi-Fi Hotspot từ điện thoại/máy tính.
3. **Cấp quyền Mạng cục bộ trên iPhone**: Vào **Cài đặt iPhone > SyncFlow > bật Mạng cục bộ (Local Network)**.
4. **Tường lửa Windows (Windows Firewall)**:
   - Mở *Windows Defender Firewall*, cho phép Python hoặc cổng `8765` nhận kết nối trong Private Network.
   - Nếu Bonjour không tự tìm thấy, mở tab **Cài đặt** trên iPhone và nhập thủ công địa chỉ IP hiển thị trên màn hình máy tính (ví dụ: `192.168.1.5`).

### ❓ Sideloadly báo lỗi khi cài IPA
- Đảm bảo bạn đã cài đặt **iTunes** và **iCloud** bản chính thức từ Apple (không dùng bản tải từ Microsoft Store).
- Đăng nhập đúng Apple ID và nhập đúng mã xác thực 2 bước.
