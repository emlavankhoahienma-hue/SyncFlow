import SwiftUI

struct SendView: View {
    @EnvironmentObject var appState: AppState
    @Binding var selectedTab: Int

    @State private var selectedSegment = 0 // 0: Photo & Video, 1: All Files
    @State private var selectedItems: [SelectedMediaItem] = []
    @State private var showPhotoPicker = false
    @State private var showFilePicker = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Segmented Control
                Picker("", selection: $selectedSegment) {
                    Text("Ảnh & Video").tag(0)
                    Text("Mọi loại file").tag(1)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, DS.Spacing.lg.rawValue)
                .padding(.vertical, DS.Spacing.md.rawValue)
                .background(DS.Color.surface)

                ScrollView {
                    VStack(alignment: .leading, spacing: DS.Spacing.xl.rawValue) {
                        // Picker Trigger Button
                        Button(action: {
                            if selectedSegment == 0 {
                                showPhotoPicker = true
                            } else {
                                showFilePicker = true
                            }
                        }) {
                            VStack(spacing: DS.Spacing.md.rawValue) {
                                ZStack {
                                    RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                                        .fill(.ultraThinMaterial)
                                        .frame(width: 56, height: 56)
                                    Image(systemName: selectedSegment == 0 ? "photo.on.rectangle.angled" : "folder.badge.plus")
                                        .font(.system(size: 26))
                                        .foregroundColor(DS.Color.primary)
                                }

                                Text(selectedSegment == 0 ? "Chọn ảnh hoặc video từ Thư viện" : "Chọn tài liệu, file nén từ Files")
                                    .font(DS.Font.headline())
                                    .foregroundColor(DS.Color.textPrimary)

                                Text("Hỗ trợ mọi định dạng (RAW, ProRAW, HEIC, 4K MOV, ZIP, PDF...)")
                                    .font(DS.Font.body())
                                    .foregroundColor(DS.Color.textMuted)
                                    .multilineTextAlignment(.center)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(DS.Spacing.xxl.rawValue)
                            .background(DS.Color.surface)
                            .cornerRadius(DS.Radius.card.rawValue)
                            .overlay(
                                RoundedRectangle(cornerRadius: DS.Radius.card.rawValue)
                                    .strokeBorder(DS.Color.textPrimary.opacity(0.1), lineWidth: 1)
                            )
                        }

                        // Auto Convert Toggle
                        HStack(spacing: DS.Spacing.md.rawValue) {
                            ZStack {
                                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                    .fill(.ultraThinMaterial)
                                    .frame(width: 32, height: 32)
                                Image(systemName: "arrow.triangle.2.circlepath")
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundColor(DS.Color.primary)
                            }

                            VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                                Text("Tự động chuyển đổi định dạng")
                                    .font(DS.Font.headline())
                                    .foregroundColor(DS.Color.textPrimary)
                                Text("HEIC→PNG và MOV→MP4 (giữ chuẩn CRF 18)")
                                    .font(DS.Font.mono(11))
                                    .foregroundColor(DS.Color.textMuted)
                            }

                            Spacer()

                            Toggle("", isOn: $appState.autoConvertEnabled)
                                .labelsHidden()
                                .tint(DS.Color.primary)
                        }
                        .padding(DS.Spacing.lg.rawValue)
                        .background(DS.Color.surface)
                        .cornerRadius(DS.Radius.card.rawValue)

                        // Selected Items Preview
                        if !selectedItems.isEmpty {
                            VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                                HStack {
                                    Text("ĐÃ CHỌN (\(selectedItems.count))")
                                        .font(DS.Font.mono(12))
                                        .fontWeight(.bold)
                                        .foregroundColor(DS.Color.textMuted)

                                    Spacer()

                                    Button("Xóa tất cả") {
                                        selectedItems.removeAll()
                                    }
                                    .font(DS.Font.mono(12))
                                    .foregroundColor(DS.Color.warning)
                                }

                                VStack(spacing: DS.Spacing.sm.rawValue) {
                                    ForEach(selectedItems) { item in
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

                                                Text(formatBytes(item.size))
                                                    .font(DS.Font.mono(12))
                                                    .foregroundColor(DS.Color.textMuted)
                                            }

                                            Spacer()

                                            if let badge = conversionBadge(for: item.ext) {
                                                FormatBadge(text: badge)
                                            }

                                            Button(action: {
                                                selectedItems.removeAll { $0.id == item.id }
                                            }) {
                                                Image(systemName: "xmark.circle.fill")
                                                    .foregroundColor(DS.Color.textMuted)
                                                    .font(.system(size: 18))
                                            }
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

                // Bottom Action Button
                VStack(spacing: 0) {
                    Divider()
                        .background(DS.Color.surfaceHigh)

                    PrimaryButton(
                        title: "Bắt đầu gửi lên máy tính",
                        icon: "paperplane.fill",
                        isEnabled: !selectedItems.isEmpty && appState.isConnected,
                        action: startUpload
                    )
                    .padding(DS.Spacing.lg.rawValue)
                }
                .background(DS.Color.surface)
            }
            .background(DS.Color.background.ignoresSafeArea())
            .navigationTitle("Gửi file")
            .sheet(isPresented: $showPhotoPicker) {
                PhotoVideoPicker(selectedItems: $selectedItems)
            }
            .sheet(isPresented: $showFilePicker) {
                AnyFilePicker(selectedItems: $selectedItems)
            }
        }
    }

    private func startUpload() {
        guard let serverURL = appState.serverBaseURL else { return }

        for item in selectedItems {
            appState.transferManager.enqueueUpload(
                name: item.name,
                ext: item.ext,
                fileURL: item.tempURL,
                size: item.size,
                autoConvert: appState.autoConvertEnabled,
                serverURL: serverURL
            )
        }

        selectedItems.removeAll()
        selectedTab = 3 // Navigate to Progress tab
    }

    private func formatBytes(_ bytes: Int64) -> String {
        let mb = Double(bytes) / (1024 * 1024)
        return String(format: "%.1f MB", mb)
    }

    private func conversionBadge(for ext: String) -> String? {
        guard appState.autoConvertEnabled else { return nil }
        let lower = ext.lowercased()
        if ["heic", "heif"].contains(lower) { return "HEIC → PNG" }
        if ["mov", "hevc"].contains(lower) { return "MOV → MP4" }
        return nil
    }

    private func iconFor(ext: String) -> String {
        let lower = ext.lowercased()
        if ["png", "jpg", "jpeg", "heic", "dng"].contains(lower) { return "photo.fill" }
        if ["mp4", "mov", "hevc"].contains(lower) { return "film.fill" }
        return "doc.fill"
    }
}
