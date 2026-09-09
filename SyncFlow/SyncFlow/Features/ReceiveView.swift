import SwiftUI
import Photos

struct ReceiveView: View {
    @EnvironmentObject var appState: AppState
    @Binding var selectedTab: Int

    @State private var availableFiles: [RemoteFileItem] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.lg.rawValue) {
                    // Header Status
                    HStack {
                        VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                            Text("File có sẵn trên máy tính")
                                .font(DS.Font.headline())
                                .foregroundColor(DS.Color.textPrimary)

                            Text("Tải trực tiếp vào Files app (thư mục Documents)")
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.textMuted)
                        }

                        Spacer()

                        Button(action: {
                            Task { await loadFiles() }
                        }) {
                            ZStack {
                                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                    .fill(.ultraThinMaterial)
                                    .frame(width: 32, height: 32)
                                Image(systemName: "arrow.clockwise")
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundColor(DS.Color.primary)
                            }
                        }
                    }

                    if isLoading {
                        HStack {
                            Spacer()
                            ProgressView()
                                .tint(DS.Color.primary)
                                .padding(DS.Spacing.xxl.rawValue)
                            Spacer()
                        }
                    } else if let error = errorMessage {
                        VStack(spacing: DS.Spacing.md.rawValue) {
                            Text(error)
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.warning)
                                .multilineTextAlignment(.center)

                            PrimaryButton(title: "Thử lại", action: {
                                Task { await loadFiles() }
                            })
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

                            Text("Không có file nào trong hàng đợi của máy tính")
                                .font(DS.Font.headline())
                                .foregroundColor(DS.Color.textPrimary)

                            Text("Kéo file vào ứng dụng SyncFlow trên máy tính để chia sẻ qua đây.")
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.textMuted)
                                .multilineTextAlignment(.center)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(DS.Spacing.xxl.rawValue)
                        .background(DS.Color.surface)
                        .cornerRadius(DS.Radius.card.rawValue)
                    } else {
                        VStack(spacing: DS.Spacing.sm.rawValue) {
                            ForEach(availableFiles) { item in
                                HStack(spacing: DS.Spacing.md.rawValue) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                            .fill(.ultraThinMaterial)
                                            .frame(width: 32, height: 32)
                                        Image(systemName: iconFor(ext: item.ext))
                                            .font(.system(size: 15, weight: .medium))
                                            .foregroundColor(DS.Color.primary)
                                    }

                                    VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                                        Text(item.name)
                                            .font(DS.Font.headline())
                                            .foregroundColor(DS.Color.textPrimary)
                                            .lineLimit(1)

                                        Text(item.formattedSize)
                                            .font(DS.Font.mono(12))
                                            .foregroundColor(DS.Color.textMuted)
                                    }

                                    Spacer()

                                    Button(action: {
                                        startDownload(item: item)
                                    }) {
                                        HStack(spacing: DS.Spacing.xs.rawValue) {
                                            Image(systemName: "arrow.down.to.line")
                                                .font(.system(size: 12, weight: .semibold))
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
                                .padding(DS.Spacing.md.rawValue)
                                .background(DS.Color.surface)
                                .cornerRadius(DS.Radius.card.rawValue)
                            }
                        }
                    }
                }
                .padding(DS.Spacing.lg.rawValue)
            }
            .background(DS.Color.background.ignoresSafeArea())
            .navigationTitle("Nhận file")
            .task {
                await loadFiles()
            }
        }
    }

    private func loadFiles() async {
        guard let url = appState.serverBaseURL, appState.isConnected else {
            errorMessage = "Chưa kết nối với máy tính. Hãy kiểm tra cài đặt mạng."
            return
        }

        isLoading = true
        errorMessage = nil
        do {
            availableFiles = try await APIClient.shared.fetchFiles(serverURL: url)
            isLoading = false
        } catch {
            errorMessage = "Lỗi khi lấy danh sách file: \(error.localizedDescription)"
            isLoading = false
        }
    }

    private func startDownload(item: RemoteFileItem) {
        guard let serverURL = appState.serverBaseURL else { return }
        appState.transferManager.enqueueDownload(fileItem: item, serverURL: serverURL)
        selectedTab = 3 // Switch to Progress tab
    }

    private func iconFor(ext: String) -> String {
        let lower = ext.lowercased()
        if ["png", "jpg", "jpeg", "heic", "webp"].contains(lower) { return "photo.fill" }
        if ["mp4", "mov", "mkv"].contains(lower) { return "film.fill" }
        if ["zip", "rar", "tar", "gz"].contains(lower) { return "archivebox.fill" }
        return "doc.fill"
    }
}
