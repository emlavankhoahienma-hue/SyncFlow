# SyncFlow — Hệ Sinh Thái Đồng Bộ File 2 Chiều iOS & Máy Tính

Hệ thống đồng bộ ảnh, video và tệp tin tốc độ cao qua mạng nội bộ Wi-Fi (LAN) giữa **iPhone (SwiftUI, iOS 17+)** và **Máy tính (Python + Flet)**, được xây dựng theo chuẩn Design System **Terra Cotta** và hỗ trợ sideload (Sideloadly, TrollStore, AltStore).

---

## 1. Kiến Trúc & Nguyên Tắc Hoạt Động

```
┌─────────────────┐         LAN (Wi-Fi)          ┌──────────────────────────┐
│   iPhone App    │  ◄──── HTTP REST + WS ────►  │  Python Desktop (Flet)   │
│  SwiftUI iOS17+ │   chunked upload/download    │  FastAPI server (:8765)  │
│  Client thuần   │   SHA-256 verify, resume     │  + Bonjour mDNS + Flet UI│
└─────────────────┘                              └──────────────────────────┘
```

- **Máy tính (Python) là Server duy nhất**: Khởi chạy FastAPI Server + WebSocket tại cổng `8765`, phát quảng bá Bonjour mDNS dịch vụ `_syncflow._tcp`.
- **iPhone là Client thuần cho cả 2 chiều**:
  - Gửi lên máy tính: iPhone upload từng chunk 1MB, tự động nối tiếp khi đứt đoạn (Resume offset).
  - Tải về từ máy tính: iPhone download chunked có hỗ trợ HTTP Range, lưu vào thư mục `Documents` của Files app và có nút "Lưu vào Ảnh" trực tiếp cho ảnh/video.
- **Bảo toàn chất lượng**:
  - Tự động chuyển đổi HEIC → PNG (giữ nguyên độ phân giải và bit-depth màu).
  - Tự động chuyển đổi video MOV/HEVC → MP4 chất lượng cao (CRF 18 visually lossless qua ffmpeg / AVAssetExportSession).

---

## 2. Cấu Trúc Thư Mục

```
syncflow/
├── SyncFlow/                             # Ứng dụng iOS SwiftUI (iOS 17+)
│   ├── SyncFlow.xcodeproj/               # Xcode Project cấu hình sẵn
│   ├── SyncFlow/
│   │   ├── App/
│   │   │   ├── SyncFlowApp.swift          # Entrypoint @main
│   │   │   └── AppState.swift             # Quản lý trạng thái kết nối & dịch vụ
│   │   ├── DesignSystem/
│   │   │   └── DesignSystem.swift         # Token màu #E2725B, Spacing 4, Font bo tròn
│   │   ├── Components/
│   │   │   ├── PrimaryButton.swift        # Nút bo góc 10px, spring scale + haptics
│   │   │   ├── MaterialIconTextField.swift# Khung 32x32 material icon + viền 0.5px
│   │   │   ├── TransferCard.swift         # Card to nhất, duy nhất có shadow mờ
│   │   │   ├── FormatBadge.swift          # Badge định dạng chuyển đổi
│   │   │   └── ProgressRingView.swift     # Vòng tiến độ 8px
│   │   ├── Core/
│   │   │   ├── Networking/                # REST APIClient, WebSocket, Bonjour Discovery
│   │   │   ├── Transfer/                  # TransferManager (hàng đợi tối đa 2), ChunkUploader
│   │   │   ├── Conversion/                # HEICConverter (ImageIO), HEVCConverter (AVAsset)
│   │   │   └── Pickers/                   # PhotoVideoPicker (PHPicker), AnyFilePicker (UIDocumentPicker)
│   │   ├── Features/                      # HomeView, SendView, ReceiveView, ProgressView, HistoryView, SettingsView
│   │   ├── Resources/Assets.xcassets      # AppIcon, launchBackground #16181D
│   │   └── Info.plist                     # Cấp quyền LAN, Bonjour, Photos, ATS Allow
│   └── exportOptions.plist
├── syncflow-desktop/                     # Ứng dụng Máy tính Python + Flet
│   ├── main.py                            # Chạy song song FastAPI + Flet UI
│   ├── requirements.txt
│   ├── server/                            # api.py, ws.py, storage.py, models.py, discovery.py
│   ├── convert/                           # heic.py (pillow-heif), hevc.py (ffmpeg CRF 18)
│   └── ui/                                # Giao diện Flet khớp Design System Terra Cotta
└── .github/workflows/
    └── build.yml                          # CI/CD xuất file SyncFlow-unsigned.ipa
```

---

## 3. Hướng Dẫn Sử Dụng

### 3.1 Chạy Ứng Dụng Desktop (Máy Tính)

1. Cài đặt Python 3.10+ (Đã thử nghiệm hoàn hảo trên Python 3.12).
2. Cài đặt các thư viện phụ thuộc:
   ```bash
   cd syncflow-desktop
   pip install -r requirements.txt
   ```
3. Khởi chạy ứng dụng:
   ```bash
   python main.py
   ```
4. Ứng dụng Desktop sẽ mở giao diện Flet Dark Mode và tự động:
   - Mở server FastAPI tại `http://0.0.0.0:8765`.
   - Hiển thị địa chỉ IP nội bộ và mã QR trong mục **Cài đặt**.
   - Mở dịch vụ tìm kiếm mDNS `_syncflow._tcp`.

### 3.2 Cài Đặt và Chạy Ứng Dụng iOS (iPhone)

#### Cách 1: Build file IPA Unsigned qua GitHub Actions
- Đẩy source code lên GitHub repository của bạn.
- Vào tab **Actions** → Chạy workflow **Build Unsigned IPA**.
- Tải file `SyncFlow-unsigned.ipa` từ Artifacts về máy tính.
- Sideload vào iPhone bằng **Sideloadly** (ký bằng Apple ID miễn phí), **TrollStore** hoặc **AltStore**.

#### Cách 2: Mở trực tiếp trên Xcode (macOS)
- Mở file `SyncFlow/SyncFlow.xcodeproj` trong Xcode 15+.
- Chọn team Signing của bạn trong `Signing & Capabilities`.
- Chọn thiết bị iPhone và nhấn **Run** (Cmd + R).

---

## 4. Kiểm Tra Danh Mục Nghiệm Thu (Acceptance Checklist)

- [x] **Design System**: `DesignSystem.swift` định nghĩa `DS` token độc quyền, cấm màu xanh dương/tím chủ đạo, cấm hardcode `Color.black/white`, màu nền `#16181D`, màu chính Terra Cotta `#E2725B`.
- [x] **PrimaryButton**: Góc bo 10px, hiệu ứng nhấn spring scale 0.95, rung haptic `.medium`.
- [x] **TextField**: Icon nằm trong khung material 32×32 bo góc 8px ở bên trái, viền mảnh 0.5px.
- [x] **Shadow**: Duy nhất `TransferCard` có shadow với opacity <= 0.25.
- [x] **Pickers**: `PHPicker` dùng filter `.any(of: [.images, .videos])`, `UIDocumentPicker` dùng `[.data, .content]`, hỗ trợ hàng nghìn định dạng file không hardcode đuôi.
- [x] **Giao thức mạng**: Chunk 1MB chuẩn, kiểm tra hash SHA-256 stream, hỗ trợ resume qua offset, WebSocket cập nhật tiến độ mỗi 250ms.
- [x] **Chuyển đổi**: HEIC→PNG qua ImageIO/pillow-heif, HEVC/MOV→MP4 qua AVAssetExportSession/ffmpeg CRF 18 giữ tối đa độ nét.
- [x] **CI/CD**: Workflow GitHub Actions xuất file `.ipa` unsigned không đòi hỏi Apple Developer Certificate trả phí.
