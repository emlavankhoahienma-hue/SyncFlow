import SwiftUI
import Photos
import QuickLook

struct LocalFileItem: Identifiable {
    let id = UUID()
    let name: String
    let ext: String
    let url: URL
    let size: Int64
    let modifiedDate: Date

    var formattedSize: String {
        let mb = Double(size) / (1024 * 1024)
        if mb >= 1.0 {
            return String(format: "%.1f MB", mb)
        } else {
            let kb = Double(size) / 1024
            return String(format: "%.1f KB", kb)
        }
    }
}

struct URLItem: Identifiable {
    let id = UUID()
    let url: URL
}

struct ReceiveView: View {
    @EnvironmentObject var appState: AppState
    @Binding var selectedTab: Int

    @State private var availableFiles: [RemoteFileItem] = []
    @State private var localFiles: [LocalFileItem] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var toastMessage: String?

    @State private var previewItem: URLItem?
    @State private var shareItem: URLItem?
    @State private var showingQRScanner = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.xl.rawValue) {
                    // SECTION 1: REMOTE FILES ON DESKTOP
                    remoteFilesSection

                    // SECTION 2: RECEIVED FILES ON IPHONE (DOCUMENTS)
                    localReceivedFilesSection
                }
                .padding(DS.Spacing.lg.rawValue)
            }
            .background(DS.Color.background.ignoresSafeArea())
            .navigationTitle("Nhận file")
            .refreshable {
                await loadFiles()
                loadLocalFiles()
            }
            .task {
                await loadFiles()
                loadLocalFiles()
            }
            .onReceive(NotificationCenter.default.publisher(for: .transferDidComplete)) { notif in
                loadLocalFiles()
                if let item = notif.object as? TransferItem, item.direction == .download {
                    showToast("Đã tải xong '\(item.name)' • Chạm để xem hoặc chia sẻ")
                }
            }
            .onReceive(appState.transferManager.$completedTransfers) { _ in
                loadLocalFiles()
            }
            .onReceive(appState.transferManager.$activeTransfers) { _ in
                loadLocalFiles()
            }
            .sheet(item: $previewItem) { item in
                QuickLookPreview(url: item.url)
            }
            .sheet(item: $shareItem) { item in
                ShareSheet(activityItems: [item.url])
            }
            .sheet(isPresented: $showingQRScanner) {
                QRScannerView { scannedIP, scannedPort, scannedPIN, scannedToken, scannedFP in
                    Task {
                        showToast("Đang kết nối đến \(scannedIP)...")
                        let ok = await appState.connect(toIP: scannedIP, port: scannedPort, pin: scannedPIN, token: scannedToken, fingerprint: scannedFP)
                        if ok {
                            showToast("Đã kết nối với máy tính thành công!")
                            await loadFiles()
                        } else {
                            let err = appState.lastConnectionError ?? "Không thể kết nối đến \(scannedIP):\(scannedPort)"
                            showToast(err)
                        }
                    }
                }
            }
            .overlay(alignment: .bottom) {
                if let msg = toastMessage {
                    Text(msg)
                        .font(DS.Font.headline())
                        .foregroundColor(Color.white)
                        .padding(.horizontal, DS.Spacing.lg.rawValue)
                        .padding(.vertical, DS.Spacing.md.rawValue)
                        .background(DS.Color.primary)
                        .cornerRadius(DS.Radius.button.rawValue)
                        .padding(.bottom, DS.Spacing.xxl.rawValue)
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
    }

    // MARK: - Section 1: Remote Files on PC
    private var remoteFilesSection: some View {
        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
            HStack {
                VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                    Text("FILE CÓ SẴN TRÊN MÁY TÍNH")
                        .font(DS.Font.mono(12))
                        .fontWeight(.bold)
                        .foregroundColor(DS.Color.textMuted)

                    Text("Nhấn Tải để lưu trực tiếp vào thư mục SyncFlow")
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.textMuted)
                }

                Spacer()

                HStack(spacing: DS.Spacing.xs.rawValue) {
                    Button(action: {
                        showingQRScanner = true
                    }) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(.ultraThinMaterial)
                                .frame(width: 32, height: 32)
                            Image(systemName: "qrcode.viewfinder")
                                .font(.system(size: 15, weight: .medium))
                                .foregroundColor(DS.Color.primary)
                        }
                    }

                    Button(action: {
                        Task { await loadFiles() }
                    }) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(.ultraThinMaterial)
                                .frame(width: 32, height: 32)
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(DS.Color.primary)
                        }
                    }
                }
            }

            if isLoading {
                HStack {
                    Spacer()
                    ProgressView()
                        .tint(DS.Color.primary)
                        .padding(DS.Spacing.xl.rawValue)
                    Spacer()
                }
            } else if let error = errorMessage {
                VStack(spacing: DS.Spacing.md.rawValue) {
                    Text(error)
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.warning)
                        .multilineTextAlignment(.center)

                    HStack(spacing: DS.Spacing.md.rawValue) {
                        PrimaryButton(title: "Thử lại", action: {
                            Task { await loadFiles() }
                        })

                        Button(action: {
                            showingQRScanner = true
                        }) {
                            HStack(spacing: DS.Spacing.xs.rawValue) {
                                Image(systemName: "qrcode.viewfinder")
                                    .font(.system(size: 14, weight: .semibold))
                                Text("Quét mã QR")
                                    .font(DS.Font.headline())
                            }
                            .foregroundColor(Color.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(DS.Color.surfaceHigh)
                            .cornerRadius(DS.Radius.button.rawValue)
                            .overlay(
                                RoundedRectangle(cornerRadius: DS.Radius.button.rawValue)
                                    .stroke(DS.Color.primary.opacity(0.6), lineWidth: 1)
                            )
                        }
                    }
                }
                .padding(DS.Spacing.xl.rawValue)
                .background(DS.Color.surface)
                .cornerRadius(DS.Radius.card.rawValue)
            } else if availableFiles.isEmpty {
                VStack(spacing: DS.Spacing.md.rawValue) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                            .fill(.ultraThinMaterial)
                            .frame(width: 56, height: 56)
                        Image(systemName: "folder")
                            .font(.system(size: 26))
                            .foregroundColor(DS.Color.textMuted)
                    }

                    Text("Hàng đợi máy tính đang trống")
                        .font(DS.Font.headline())
                        .foregroundColor(DS.Color.textPrimary)

                    Text("Kéo file vào mục 'Gửi' trên máy tính để tải về iPhone.")
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.textMuted)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(DS.Spacing.xl.rawValue)
                .background(DS.Color.surface)
                .cornerRadius(DS.Radius.card.rawValue)
            } else {
                VStack(spacing: DS.Spacing.sm.rawValue) {
                    ForEach(availableFiles) { item in
                        remoteFileRow(item: item)
                    }
                }
            }
        }
    }

    private func remoteFileRow(item: RemoteFileItem) -> some View {
        let isDownloading = appState.transferManager.activeTransfers.contains(where: { $0.fileId == item.fileId })
        let isQueued = appState.transferManager.queue.contains(where: { $0.fileId == item.fileId })
        let localMatch = localFiles.first(where: { $0.name == item.name })

        return HStack(spacing: DS.Spacing.md.rawValue) {
            ZStack {
                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                    .fill(.ultraThinMaterial)
                    .frame(width: 36, height: 36)
                Image(systemName: iconFor(ext: item.ext))
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(DS.Color.primary)
            }

            VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                Text(item.name)
                    .font(DS.Font.headline())
                    .foregroundColor(DS.Color.textPrimary)
                    .lineLimit(1)

                Text(localMatch != nil ? "\(item.formattedSize) • Đã tải về máy" : item.formattedSize)
                    .font(DS.Font.mono(12))
                    .foregroundColor(localMatch != nil ? DS.Color.success : DS.Color.textMuted)
            }

            Spacer()

            if isDownloading {
                HStack(spacing: DS.Spacing.xs.rawValue) {
                    ProgressView()
                        .tint(DS.Color.primary)
                    Text("Đang tải...")
                        .font(DS.Font.mono(12))
                        .foregroundColor(DS.Color.primary)
                }
                .padding(.horizontal, DS.Spacing.md.rawValue)
                .padding(.vertical, DS.Spacing.sm.rawValue)
                .background(DS.Color.surfaceHigh)
                .cornerRadius(DS.Radius.button.rawValue)
            } else if isQueued {
                Text("Đang chờ...")
                    .font(DS.Font.mono(12))
                    .foregroundColor(DS.Color.textMuted)
                    .padding(.horizontal, DS.Spacing.md.rawValue)
                    .padding(.vertical, DS.Spacing.sm.rawValue)
                    .background(DS.Color.surfaceHigh)
                    .cornerRadius(DS.Radius.button.rawValue)
            } else if let local = localMatch {
                HStack(spacing: DS.Spacing.xs.rawValue) {
                    Button(action: {
                        previewItem = URLItem(url: local.url)
                    }) {
                        HStack(spacing: DS.Spacing.xs.rawValue) {
                            Image(systemName: "eye.fill")
                                .font(.system(size: 11))
                            Text("Xem")
                                .font(DS.Font.headline())
                        }
                        .foregroundColor(DS.Color.primary)
                        .padding(.horizontal, DS.Spacing.sm.rawValue)
                        .padding(.vertical, DS.Spacing.xs.rawValue)
                        .background(DS.Color.surfaceHigh)
                        .cornerRadius(DS.Radius.iconBlock.rawValue)
                    }

                    Button(action: {
                        shareItem = URLItem(url: local.url)
                    }) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(DS.Color.surfaceHigh)
                                .frame(width: 32, height: 32)
                            Image(systemName: "square.and.arrow.up")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(DS.Color.primary)
                        }
                    }

                    Button(action: {
                        startDownload(item: item)
                    }) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 12))
                            .foregroundColor(DS.Color.textMuted)
                            .padding(DS.Spacing.xs.rawValue)
                    }
                }
            } else {
                Button(action: {
                    startDownload(item: item)
                }) {
                    HStack(spacing: DS.Spacing.xs.rawValue) {
                        Image(systemName: "arrow.down.to.line")
                            .font(.system(size: 12, weight: .bold))
                        Text("Tải")
                            .font(DS.Font.headline())
                    }
                    .foregroundColor(Color.white)
                    .padding(.horizontal, DS.Spacing.md.rawValue)
                    .padding(.vertical, DS.Spacing.sm.rawValue)
                    .background(DS.Color.primary)
                    .cornerRadius(DS.Radius.button.rawValue)
                }
            }
        }
        .padding(DS.Spacing.md.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    // MARK: - Section 2: Local Received Files on iPhone
    private var localReceivedFilesSection: some View {
        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
            HStack {
                VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                    Text("TỆP ĐÃ TẢI VỀ IPHONE")
                        .font(DS.Font.mono(12))
                        .fontWeight(.bold)
                        .foregroundColor(DS.Color.textMuted)

                    Text("\(localFiles.count) tệp trong bộ nhớ máy • Chạm để xem / chia sẻ")
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.textMuted)
                }

                Spacer()

                HStack(spacing: DS.Spacing.xs.rawValue) {
                    Button(action: {
                        loadLocalFiles()
                    }) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(.ultraThinMaterial)
                                .frame(width: 32, height: 32)
                            Image(systemName: "arrow.triangle.2.circlepath")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(DS.Color.primary)
                        }
                    }

                    Button(action: {
                        openFilesApp()
                    }) {
                        HStack(spacing: DS.Spacing.xs.rawValue) {
                            Image(systemName: "folder.fill")
                                .font(.system(size: 11))
                            Text("Files")
                                .font(DS.Font.headline())
                        }
                        .foregroundColor(DS.Color.primary)
                        .padding(.horizontal, DS.Spacing.sm.rawValue)
                        .padding(.vertical, DS.Spacing.xs.rawValue)
                        .background(DS.Color.surfaceHigh)
                        .cornerRadius(DS.Radius.iconBlock.rawValue)
                    }
                }
            }

            if localFiles.isEmpty {
                VStack(spacing: DS.Spacing.md.rawValue) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                            .fill(.ultraThinMaterial)
                            .frame(width: 52, height: 52)
                        Image(systemName: "tray")
                            .font(.system(size: 24))
                            .foregroundColor(DS.Color.textMuted)
                    }

                    Text("Chưa có tệp nào được tải về")
                        .font(DS.Font.headline())
                        .foregroundColor(DS.Color.textPrimary)

                    Text("Các tệp tải từ máy tính sẽ được lưu tại đây và có thể mở trong app Tệp (Files).")
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.textMuted)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
                .padding(DS.Spacing.xl.rawValue)
                .background(DS.Color.surface)
                .cornerRadius(DS.Radius.card.rawValue)
            } else {
                VStack(spacing: DS.Spacing.sm.rawValue) {
                    ForEach(localFiles) { file in
                        localFileRow(file: file)
                    }
                }
            }
        }
    }

    private func localFileRow(file: LocalFileItem) -> some View {
        HStack(spacing: DS.Spacing.md.rawValue) {
            // Tap on icon or file info to open QuickLook
            Button(action: {
                previewItem = URLItem(url: file.url)
            }) {
                HStack(spacing: DS.Spacing.md.rawValue) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                            .fill(.ultraThinMaterial)
                            .frame(width: 36, height: 36)
                        Image(systemName: iconFor(ext: file.ext))
                            .font(.system(size: 16, weight: .medium))
                            .foregroundColor(DS.Color.primary)
                    }

                    VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                        Text(file.name)
                            .font(DS.Font.headline())
                            .foregroundColor(DS.Color.textPrimary)
                            .lineLimit(1)

                        Text(file.formattedSize)
                            .font(DS.Font.mono(12))
                            .foregroundColor(DS.Color.textMuted)
                    }
                }
            }
            .buttonStyle(.plain)

            Spacer()

            // Quick Actions: Share, Save to Photos, Delete
            HStack(spacing: DS.Spacing.xs.rawValue) {
                // Share button (UIActivityViewController)
                Button(action: {
                    shareItem = URLItem(url: file.url)
                }) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                            .fill(DS.Color.surfaceHigh)
                            .frame(width: 32, height: 32)
                        Image(systemName: "square.and.arrow.up")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(DS.Color.primary)
                    }
                }

                // Save to Photos if media
                if isMedia(ext: file.ext) {
                    Button(action: {
                        saveToPhotos(url: file.url)
                    }) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(DS.Color.surfaceHigh)
                                .frame(width: 32, height: 32)
                            Image(systemName: "photo.badge.plus")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(DS.Color.success)
                        }
                    }
                }

                // Delete button
                Button(action: {
                    deleteLocalFile(file: file)
                }) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                            .fill(DS.Color.surfaceHigh)
                            .frame(width: 32, height: 32)
                        Image(systemName: "trash")
                            .font(.system(size: 12, weight: .medium))
                            .foregroundColor(DS.Color.warning)
                    }
                }
            }
        }
        .padding(DS.Spacing.md.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    // MARK: - Helper Methods
    private func loadFiles() async {
        isLoading = true
        errorMessage = nil

        // If not connected, proactively re-attempt connection & Bonjour discovery
        if !appState.isConnected {
            appState.discoveryService.startDiscovery()
            await appState.connect()
        }

        guard let url = appState.serverBaseURL, appState.isConnected else {
            errorMessage = "Chưa kết nối với máy tính. Hãy bấm 'Quét mã QR' hoặc kiểm tra Wi-Fi."
            isLoading = false
            return
        }

        do {
            availableFiles = try await APIClient.shared.fetchFiles(serverURL: url)
            isLoading = false
        } catch {
            errorMessage = "Lỗi khi lấy danh sách file: \(error.localizedDescription)"
            isLoading = false
        }
    }

    private func loadLocalFiles() {
        let docs = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        do {
            let urls = try FileManager.default.contentsOfDirectory(at: docs, includingPropertiesForKeys: [.fileSizeKey, .contentModificationDateKey], options: [.skipsHiddenFiles])
            var items: [LocalFileItem] = []
            for u in urls {
                let res = try u.resourceValues(forKeys: [.fileSizeKey, .contentModificationDateKey])
                let size = Int64(res.fileSize ?? 0)
                let date = res.contentModificationDate ?? Date()
                items.append(LocalFileItem(
                    name: u.lastPathComponent,
                    ext: u.pathExtension.lowercased(),
                    url: u,
                    size: size,
                    modifiedDate: date
                ))
            }
            items.sort(by: { $0.modifiedDate > $1.modifiedDate })
            self.localFiles = items
        } catch {
            self.localFiles = []
        }
    }

    private func startDownload(item: RemoteFileItem) {
        guard let serverURL = appState.serverBaseURL else { return }
        appState.transferManager.enqueueDownload(fileItem: item, serverURL: serverURL)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        showToast("Đang tải '\(item.name)'...")
    }

    private func deleteLocalFile(file: LocalFileItem) {
        do {
            try FileManager.default.removeItem(at: file.url)
            loadLocalFiles()
            showToast("Đã xóa tệp '\(file.name)'")
        } catch {
            showToast("Lỗi khi xóa: \(error.localizedDescription)")
        }
    }

    private func saveToPhotos(url: URL) {
        PHPhotoLibrary.requestAuthorization(for: .addOnly) { status in
            if status == .authorized || status == .limited {
                PHPhotoLibrary.shared().performChanges({
                    if ["mp4", "mov"].contains(url.pathExtension.lowercased()) {
                        PHAssetChangeRequest.creationRequestForAssetFromVideo(atFileURL: url)
                    } else {
                        PHAssetChangeRequest.creationRequestForAssetFromImage(atFileURL: url)
                    }
                }) { success, _ in
                    DispatchQueue.main.async {
                        if success {
                            UINotificationFeedbackGenerator().notificationOccurred(.success)
                            showToast("Đã lưu vào Thư viện Ảnh")
                        } else {
                            UINotificationFeedbackGenerator().notificationOccurred(.error)
                            showToast("Không thể lưu vào Ảnh")
                        }
                    }
                }
            } else {
                DispatchQueue.main.async {
                    showToast("Cần cấp quyền truy cập Thư viện Ảnh trong Cài đặt")
                }
            }
        }
    }

    private func openFilesApp() {
        if let url = URL(string: "shareddocuments://") {
            UIApplication.shared.open(url)
        }
    }

    private func showToast(_ msg: String) {
        withAnimation { toastMessage = msg }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            withAnimation { toastMessage = nil }
        }
    }

    private func isMedia(ext: String) -> Bool {
        let lower = ext.lowercased()
        return ["png", "jpg", "jpeg", "heic", "webp", "mp4", "mov"].contains(lower)
    }

    private func iconFor(ext: String) -> String {
        let lower = ext.lowercased()
        if ["png", "jpg", "jpeg", "heic", "webp"].contains(lower) { return "photo.fill" }
        if ["mp4", "mov", "mkv"].contains(lower) { return "film.fill" }
        if ["zip", "rar", "tar", "gz", "7z"].contains(lower) { return "archivebox.fill" }
        if ["pdf"].contains(lower) { return "doc.richtext.fill" }
        return "doc.fill"
    }
}
