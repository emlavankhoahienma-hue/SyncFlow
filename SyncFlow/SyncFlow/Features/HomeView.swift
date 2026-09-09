import SwiftUI

struct HomeView: View {
    @EnvironmentObject var appState: AppState
    @Binding var selectedTab: Int

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.xl.rawValue) {
                    // Header with Connection Pulse (iOS 17+)
                    HStack {
                        VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                            Text("SyncFlow")
                                .font(DS.Font.title())
                                .foregroundColor(DS.Color.textPrimary)

                            Text(connectionSubtitle)
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.textMuted)
                        }

                        Spacer()

                        // Status Dot with pulse effect (iOS 17+)
                        HStack(spacing: DS.Spacing.xs.rawValue) {
                            if #available(iOS 17.0, *) {
                                Image(systemName: appState.isConnected ? "circle.fill" : "circle.dotted")
                                    .font(.system(size: 14))
                                    .foregroundColor(appState.isConnected ? DS.Color.success : DS.Color.warning)
                                    .symbolEffect(.pulse, isActive: true)
                            } else {
                                Circle()
                                    .fill(appState.isConnected ? DS.Color.success : DS.Color.warning)
                                    .frame(width: 10, height: 10)
                            }

                            Text(appState.isConnected ? "Đã kết nối" : "Chưa kết nối")
                                .font(DS.Font.mono(12))
                                .foregroundColor(appState.isConnected ? DS.Color.success : DS.Color.warning)
                        }
                        .padding(.horizontal, DS.Spacing.sm.rawValue)
                        .padding(.vertical, DS.Spacing.xs.rawValue)
                        .background(DS.Color.surfaceHigh)
                        .cornerRadius(DS.Radius.iconBlock.rawValue)
                    }

                    // Main TransferCard (The ONLY element allowed to have shadow)
                    if let active = appState.transferManager.activeTransfers.first {
                        TransferCard(
                            fileName: active.name,
                            progress: active.progress,
                            speedText: active.formattedSpeed,
                            etaText: active.formattedEta,
                            bytesText: active.formattedProgressText,
                            statusText: active.status.description,
                            isTransferring: true,
                            onCancel: {
                                appState.transferManager.cancelTransfer(item: active)
                            }
                        )
                    } else {
                        // Idle card
                        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                            HStack {
                                Text("TRUYỀN TẢI")
                                    .font(DS.Font.mono(12))
                                    .fontWeight(.bold)
                                    .foregroundColor(DS.Color.textMuted)
                                Spacer()
                                Text("Sẵn sàng")
                                    .font(DS.Font.mono(12))
                                    .foregroundColor(DS.Color.primary)
                            }

                            HStack(spacing: DS.Spacing.lg.rawValue) {
                                ProgressRingView(progress: 0.0, size: 60, lineWidth: 6, showPercentText: false)
                                    .overlay(
                                        Image(systemName: "arrow.up.arrow.down")
                                            .font(.system(size: 20, weight: .semibold))
                                            .foregroundColor(DS.Color.primary)
                                    )

                                VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                                    Text("Chưa có tác vụ nào")
                                        .font(DS.Font.headline())
                                        .foregroundColor(DS.Color.textPrimary)

                                    Text("Chọn gửi hoặc nhận file bên dưới")
                                        .font(DS.Font.body())
                                        .foregroundColor(DS.Color.textMuted)
                                }
                            }
                        }
                        .padding(DS.Spacing.xl.rawValue)
                        .background(DS.Color.surface)
                        .cornerRadius(DS.Radius.card.rawValue)
                        .shadow(color: SwiftUI.Color.black.opacity(0.15), radius: 16, x: 0, y: 4)
                    }

                    // Quick Action Buttons (PrimaryButton: Radius 10)
                    VStack(spacing: DS.Spacing.md.rawValue) {
                        PrimaryButton(
                            title: "Gửi lên máy tính",
                            icon: "arrow.up.doc.fill",
                            action: { selectedTab = 1 }
                        )

                        PrimaryButton(
                            title: "Nhận từ máy tính",
                            icon: "arrow.down.doc.fill",
                            action: { selectedTab = 2 }
                        )
                    }

                    // Recent Transfers List
                    VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                        Text("HOẠT ĐỘNG GẦN ĐÂY")
                            .font(DS.Font.mono(12))
                            .fontWeight(.bold)
                            .foregroundColor(DS.Color.textMuted)

                        if appState.transferManager.completedTransfers.isEmpty {
                            HStack(spacing: DS.Spacing.md.rawValue) {
                                ZStack {
                                    RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                        .fill(.ultraThinMaterial)
                                        .frame(width: 32, height: 32)
                                    Image(systemName: "tray")
                                        .font(.system(size: 15, weight: .medium))
                                        .foregroundColor(DS.Color.textMuted)
                                }
                                Text("Chưa có lịch sử truyền file")
                                    .font(DS.Font.body())
                                    .foregroundColor(DS.Color.textMuted)
                            }
                            .padding(DS.Spacing.lg.rawValue)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(DS.Color.surface)
                            .cornerRadius(DS.Radius.card.rawValue)
                        } else {
                            VStack(spacing: DS.Spacing.sm.rawValue) {
                                ForEach(appState.transferManager.completedTransfers.prefix(5)) { item in
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
                                            Text(item.formattedProgressText)
                                                .font(DS.Font.mono(12))
                                                .foregroundColor(DS.Color.textMuted)
                                        }

                                        Spacer()

                                        Text(item.status.description)
                                            .font(DS.Font.mono(12))
                                            .foregroundColor(item.status == .completed ? DS.Color.success : DS.Color.warning)
                                    }
                                    .padding(DS.Spacing.md.rawValue)
                                    .background(DS.Color.surface)
                                    .cornerRadius(DS.Radius.card.rawValue)
                                }
                            }
                        }
                    }
                }
                .padding(DS.Spacing.lg.rawValue)
            }
            .background(DS.Color.background.ignoresSafeArea())
        }
    }

    private var connectionSubtitle: String {
        if case .connected(let name) = appState.connectionState {
            return "Đã kết nối với \(name)"
        } else if case .connecting = appState.connectionState {
            return "Đang tìm máy tính..."
        }
        return "Mở Wi-Fi cùng mạng LAN với máy tính"
    }

    private func iconFor(ext: String) -> String {
        let lower = ext.lowercased()
        if ["png", "jpg", "jpeg", "heic", "dng"].contains(lower) { return "photo.fill" }
        if ["mp4", "mov", "hevc"].contains(lower) { return "film.fill" }
        if ["pdf", "doc", "docx", "txt"].contains(lower) { return "doc.text.fill" }
        return "doc.fill"
    }
}
