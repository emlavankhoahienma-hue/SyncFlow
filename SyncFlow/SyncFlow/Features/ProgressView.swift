import SwiftUI
import Photos

struct ProgressViewScreen: View {
    @EnvironmentObject var appState: AppState

    @State private var toastMessage: String?
    @State private var previewItem: URLItem?
    @State private var shareItem: URLItem?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.xl.rawValue) {
                    // Active & Queued Transfers Section
                    if appState.transferManager.activeTransfers.isEmpty && appState.transferManager.queue.isEmpty {
                        emptyActiveState
                    } else {
                        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                            Text("ĐANG XỬ LÝ")
                                .font(DS.Font.mono(12))
                                .fontWeight(.bold)
                                .foregroundColor(DS.Color.textMuted)

                            ForEach(appState.transferManager.activeTransfers) { item in
                                activeTransferRow(item: item)
                            }

                            ForEach(appState.transferManager.queue) { item in
                                queuedTransferRow(item: item)
                            }
                        }
                    }

                    // Completed Transfers Section
                    if !appState.transferManager.completedTransfers.isEmpty {
                        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                            HStack {
                                Text("ĐÃ HOÀN TẤT")
                                    .font(DS.Font.mono(12))
                                    .fontWeight(.bold)
                                    .foregroundColor(DS.Color.textMuted)

                                Spacer()

                                Button("Xóa") {
                                    appState.transferManager.completedTransfers.removeAll()
                                }
                                .font(DS.Font.mono(12))
                                .foregroundColor(DS.Color.textMuted)
                            }

                            ForEach(appState.transferManager.completedTransfers) { item in
                                completedTransferRow(item: item)
                            }
                        }
                    }
                }
                .padding(DS.Spacing.lg.rawValue)
            }
            .background(DS.Color.background.ignoresSafeArea())
            .navigationTitle("Tiến độ")
            .toolbar {
                if !appState.transferManager.activeTransfers.isEmpty || !appState.transferManager.queue.isEmpty {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Hủy tất cả") {
                            appState.transferManager.cancelAll()
                        }
                        .font(DS.Font.mono(13))
                        .foregroundColor(DS.Color.warning)
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
            .sheet(item: $previewItem) { item in
                QuickLookPreview(url: item.url)
            }
            .sheet(item: $shareItem) { item in
                ShareSheet(activityItems: [item.url])
            }
        }
    }

    private var emptyActiveState: some View {
        VStack(spacing: DS.Spacing.md.rawValue) {
            ZStack {
                RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                    .fill(.ultraThinMaterial)
                    .frame(width: 56, height: 56)
                Image(systemName: "checkmark.circle")
                    .font(.system(size: 28))
                    .foregroundColor(DS.Color.success)
            }

            Text("Không có tác vụ nào đang truyền")
                .font(DS.Font.headline())
                .foregroundColor(DS.Color.textPrimary)

            Text("Các file đang gửi hoặc nhận sẽ hiển thị tiến độ trực tiếp tại đây.")
                .font(DS.Font.body())
                .foregroundColor(DS.Color.textMuted)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity)
        .padding(DS.Spacing.xxl.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    private func activeTransferRow(item: TransferItem) -> some View {
        VStack(spacing: DS.Spacing.md.rawValue) {
            HStack(spacing: DS.Spacing.md.rawValue) {
                ProgressRingView(progress: item.progress, size: 52, lineWidth: 6)

                VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                    Text(item.name)
                        .font(DS.Font.headline())
                        .foregroundColor(DS.Color.textPrimary)
                        .lineLimit(1)

                    Text(item.formattedProgressText)
                        .font(DS.Font.mono(12))
                        .foregroundColor(DS.Color.textMuted)

                    HStack(spacing: DS.Spacing.md.rawValue) {
                        Text(item.formattedSpeed)
                            .font(DS.Font.mono(12))
                            .fontWeight(.medium)
                            .foregroundColor(DS.Color.primary)

                        if !item.formattedEta.isEmpty {
                            Text(item.formattedEta)
                                .font(DS.Font.mono(12))
                                .foregroundColor(DS.Color.textMuted)
                        }
                    }
                }

                Spacer()

                Button(action: {
                    appState.transferManager.cancelTransfer(item: item)
                }) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                            .fill(.ultraThinMaterial)
                            .frame(width: 32, height: 32)
                        Image(systemName: "xmark")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundColor(DS.Color.textMuted)
                    }
                }
            }
        }
        .padding(DS.Spacing.lg.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    private func queuedTransferRow(item: TransferItem) -> some View {
        HStack(spacing: DS.Spacing.md.rawValue) {
            ZStack {
                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                    .fill(.ultraThinMaterial)
                    .frame(width: 32, height: 32)
                Image(systemName: "clock")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(DS.Color.textMuted)
            }

            VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                Text(item.name)
                    .font(DS.Font.headline())
                    .foregroundColor(DS.Color.textPrimary)
                    .lineLimit(1)

                Text("Đang chờ trong hàng đợi...")
                    .font(DS.Font.mono(12))
                    .foregroundColor(DS.Color.textMuted)
            }

            Spacer()

            Button(action: {
                appState.transferManager.cancelTransfer(item: item)
            }) {
                Image(systemName: "xmark.circle")
                    .foregroundColor(DS.Color.textMuted)
            }
        }
        .padding(DS.Spacing.md.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    private func completedTransferRow(item: TransferItem) -> some View {
        HStack(spacing: DS.Spacing.md.rawValue) {
            Button(action: {
                if let url = item.fileURL {
                    previewItem = URLItem(url: url)
                }
            }) {
                HStack(spacing: DS.Spacing.md.rawValue) {
                    ZStack {
                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                            .fill(.ultraThinMaterial)
                            .frame(width: 32, height: 32)
                        Image(systemName: item.status == .completed ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                            .font(.system(size: 16))
                            .foregroundColor(item.status == .completed ? DS.Color.success : DS.Color.warning)
                    }

                    VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                        Text(item.name)
                            .font(DS.Font.headline())
                            .foregroundColor(DS.Color.textPrimary)
                            .lineLimit(1)

                        Text(item.direction == .upload ? "Đã gửi lên máy tính" : "Đã tải về Files • Chạm để xem")
                            .font(DS.Font.body())
                            .foregroundColor(DS.Color.textMuted)
                    }
                }
            }
            .buttonStyle(.plain)

            Spacer()

            if item.direction == .download && item.status == .completed, let url = item.fileURL {
                HStack(spacing: DS.Spacing.xs.rawValue) {
                    // Share button
                    Button(action: {
                        shareItem = URLItem(url: url)
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

                    // Save to Photos
                    if isMedia(ext: item.ext) {
                        Button(action: {
                            saveToPhotos(url: url)
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
                }
            }
        }
        .padding(DS.Spacing.md.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
    }

    private func isMedia(ext: String) -> Bool {
        let lower = ext.lowercased()
        return ["png", "jpg", "jpeg", "heic", "mp4", "mov"].contains(lower)
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
                            showToast("Đã lưu vào Thư viện Ảnh")
                        } else {
                            showToast("Không thể lưu vào Ảnh")
                        }
                    }
                }
            }
        }
    }

    private func showToast(_ msg: String) {
        withAnimation { toastMessage = msg }
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            withAnimation { toastMessage = nil }
        }
    }
}
