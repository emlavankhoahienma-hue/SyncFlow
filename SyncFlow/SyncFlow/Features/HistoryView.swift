import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var appState: AppState

    @State private var previewItem: URLItem?
    @State private var shareItem: URLItem?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.lg.rawValue) {
                    if appState.transferManager.completedTransfers.isEmpty {
                        VStack(spacing: DS.Spacing.md.rawValue) {
                            ZStack {
                                RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                                    .fill(.ultraThinMaterial)
                                    .frame(width: 56, height: 56)
                                Image(systemName: "clock.arrow.circlepath")
                                    .font(.system(size: 26))
                                    .foregroundColor(DS.Color.textMuted)
                            }

                            Text("Lịch sử trống")
                                .font(DS.Font.headline())
                                .foregroundColor(DS.Color.textPrimary)

                            Text("Các file đã truyền thành công hoặc thất bại sẽ được ghi nhận tại đây.")
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
                            ForEach(appState.transferManager.completedTransfers) { item in
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
                                                Image(systemName: item.direction == .upload ? "arrow.up" : "arrow.down")
                                                    .font(.system(size: 15, weight: .bold))
                                                    .foregroundColor(DS.Color.primary)
                                            }

                                            VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                                                Text(item.name)
                                                    .font(DS.Font.headline())
                                                    .foregroundColor(DS.Color.textPrimary)
                                                    .lineLimit(1)

                                                Text(item.fileURL != nil ? "\(item.formattedProgressText) • Chạm để xem" : item.formattedProgressText)
                                                    .font(DS.Font.mono(12))
                                                    .foregroundColor(DS.Color.textMuted)
                                            }
                                        }
                                    }
                                    .buttonStyle(.plain)

                                    Spacer()

                                    if let url = item.fileURL {
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
                                    } else {
                                        Text(item.status.description)
                                            .font(DS.Font.mono(12))
                                            .foregroundColor(item.status == .completed ? DS.Color.success : DS.Color.warning)
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
            .navigationTitle("Lịch sử")
            .toolbar {
                if !appState.transferManager.completedTransfers.isEmpty {
                    ToolbarItem(placement: .navigationBarTrailing) {
                        Button("Xóa tất cả") {
                            appState.transferManager.completedTransfers.removeAll()
                        }
                        .font(DS.Font.mono(13))
                        .foregroundColor(DS.Color.warning)
                    }
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
}
