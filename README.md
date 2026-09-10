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

## 2. Bảo Mật Cấp Cao: Chống Nghe Lén Wireshark & Zero-Secret E2EE

Ứng dụng được thiết kế với cơ chế bảo mật truyền dữ liệu chủ động, giải quyết triệt để nguy cơ lộ dữ liệu trong môi trường mạng Wi-Fi công cộng hoặc khi có kẻ xấu xâm nhập mạng nội bộ:

1. **Chống bắt gói tin Wireshark (Anti-Sniffing / E2EE)**:
   - Toàn bộ các phân mảnh dữ liệu (chunks) truyền tải giữa iPhone và PC qua mạng Wi-Fi đều được mã hóa bằng thuật toán đối xứng **AES-256-GCM**.
   - Bất kỳ ai dùng phần mềm bắt gói tin (như **Wireshark**, tcpdump, Charles Proxy) trong cùng mạng LAN chỉ nhìn thấy các khối dữ liệu nhị phân ngẫu nhiên (pseudorandom entropy cao), hoàn toàn không thể giải mã hay đọc được hình ảnh, video, tên file hoặc tài liệu của bạn.

2. **Chính Sách Không Lưu Bí Mật (Zero Secrets in Git)**:
   - **Tuyệt đối không lưu private key, mật khẩu, token hay pre-shared key nào trong mã nguồn Git.**
   - Mỗi lần ứng dụng khởi chạy hoặc kết nối, iPhone (`CryptoKit.Curve25519`) và Máy tính (`cryptography.x25519`) sẽ tự động sinh một cặp khóa phù du (**Ephemeral Keypair**) ngẫu nhiên trong **RAM**.
   - Hai thiết bị trao đổi Public Key (32 byte) qua endpoint `/auth/handshake` và bắt tay thỏa thuận khóa bí mật chung (**ECDH Key Agreement**).
   - Hàm dẫn xuất khóa **HKDF-SHA256** tạo ra khóa đối xứng 256-bit trong RAM. Khóa này tự hủy ngay khi ngắt kết nối hoặc thoát app. Dù mã nguồn Git có công khai thì các phiên truyền tải trong quá khứ hay tương lai cũng không thể bị giải mã.

3. **Phát hiện can thiệp và chèn dữ liệu (Anti-Tampering & MITM Detection)**:
   - Mỗi chunk mã hóa đi kèm một **Auth Tag** 16-byte theo chuẩn Galois/Counter Mode (GCM).
   - Nếu có kẻ tấn công thực hiện tấn công trung gian (Man-in-the-middle, ARP spoofing) cố tình sửa đổi dù chỉ 1 bit trên đường truyền, quá trình giải mã sẽ báo lỗi xác thực ngay lập tức và server/client sẽ hủy bỏ tác vụ truyền tệp để bảo vệ an toàn hệ thống.

4. **Chống tấn công vượt thư mục (Anti-Path Traversal)**:
   - Tên tệp gửi từ client được chuẩn hóa và khử toàn bộ ký tự nguy hiểm (`../`, `..\\`, ký tự điều khiển, null byte) để đảm bảo tệp tải lên không bao giờ ghi đè ra ngoài thư mục quy định.

---

## 3. Cài Đặt & Chạy Trên Máy Tính

### 3.1 Chạy trực tiếp qua Shortcut hoặc Launcher
* Nếu bạn đã có file `SyncFlow.exe` (hoặc shortcut trên Desktop):
  - Nhấp đúp vào **SyncFlow** trên Desktop để mở ngay ứng dụng.
  - Bạn có thể nhấp chuột phải vào icon ứng dụng dưới Taskbar và chọn **Pin to taskbar** để tiện mở lần sau.

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
