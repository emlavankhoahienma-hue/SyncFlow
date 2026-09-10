import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var appState: AppState

    @State private var inputIP: String = ""
    @State private var isConnecting = false
    @State private var connectionFeedback: String?
    @State private var showingQRScanner = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DS.Spacing.xl.rawValue) {
                    // Manual IP & QR Connection Card
                    VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                        Text("KẾT NỐI MÁY TÍNH")
                            .font(DS.Font.mono(12))
                            .fontWeight(.bold)
                            .foregroundColor(DS.Color.textMuted)

                        Button(action: {
                            showingQRScanner = true
                        }) {
                            HStack(spacing: DS.Spacing.sm.rawValue) {
                                Image(systemName: "qrcode.viewfinder")
                                    .font(.system(size: 16, weight: .semibold))
                                Text("Quét mã QR trên máy tính")
                                    .font(DS.Font.headline())
                            }
                            .foregroundColor(Color.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 48)
                            .background(DS.Color.surfaceHigh)
                            .cornerRadius(DS.Radius.button.rawValue)
                            .overlay(
                                RoundedRectangle(cornerRadius: DS.Radius.button.rawValue)
                                    .stroke(DS.Color.primary.opacity(0.7), lineWidth: 1)
                            )
                        }

                        HStack {
                            VStack { Divider().background(DS.Color.border) }
                            Text("HOẶC NHẬP IP")
                                .font(DS.Font.mono(10))
                                .foregroundColor(DS.Color.textMuted)
                            VStack { Divider().background(DS.Color.border) }
                        }
                        .padding(.vertical, DS.Spacing.xs.rawValue)

                        MaterialIconTextField(
                            systemIcon: "network",
                            placeholder: "Nhập địa chỉ IP máy tính (VD: 192.168.1.5)",
                            text: $inputIP,
                            keyboardType: .decimalPad
                        )

                        PrimaryButton(
                            title: isConnecting ? "Đang kết nối..." : "Kết nối",
                            icon: "bolt.fill",
                            isEnabled: !inputIP.trimmingCharacters(in: .whitespaces).isEmpty && !isConnecting,
                            action: {
                                Task { await connectManual() }
                            }
                        )

                        if let feedback = connectionFeedback {
                            Text(feedback)
                                .font(DS.Font.mono(12))
                                .foregroundColor(appState.isConnected ? DS.Color.success : DS.Color.warning)
                        }
                    }
                    .padding(DS.Spacing.lg.rawValue)
                    .background(DS.Color.surface)
                    .cornerRadius(DS.Radius.card.rawValue)

                    // Auto-Discovery Section (Bonjour)
                    VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
                        HStack(spacing: DS.Spacing.md.rawValue) {
                            ZStack {
                                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                    .fill(.ultraThinMaterial)
                                    .frame(width: 32, height: 32)
                                Image(systemName: "bonjour")
                                    .font(.system(size: 15, weight: .medium))
                                    .foregroundColor(DS.Color.primary)
                            }

                            VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                                Text("Tự động dò tìm (Bonjour / mDNS)")
                                    .font(DS.Font.headline())
                                    .foregroundColor(DS.Color.textPrimary)
                                Text("Tự phát hiện ứng dụng trên máy tính cùng Wi-Fi")
                                    .font(DS.Font.body())
                                    .foregroundColor(DS.Color.textMuted)
                            }

                            Spacer()

                            Toggle("", isOn: $appState.autoDiscoverEnabled)
                                .labelsHidden()
                                .tint(DS.Color.primary)
                                .onChange(of: appState.autoDiscoverEnabled) { _, enabled in
                                    if enabled {
                                        appState.discoveryService.startDiscovery()
                                    } else {
                                        appState.discoveryService.stopDiscovery()
                                    }
                                }
                        }

                        if appState.autoDiscoverEnabled && !appState.discoveryService.discoveredServers.isEmpty {
                            Divider()
                                .background(DS.Color.surfaceHigh)

                            Text("MÁY TÍNH ĐÃ PHÁT HIỆN")
                                .font(DS.Font.mono(11))
                                .foregroundColor(DS.Color.textMuted)

                            ForEach(appState.discoveryService.discoveredServers) { server in
                                Button(action: {
                                    inputIP = server.ipAddress
                                    Task { await connectManual() }
                                }) {
                                    HStack {
                                        Image(systemName: "display")
                                            .foregroundColor(DS.Color.primary)
                                        Text(server.name)
                                            .font(DS.Font.headline())
                                            .foregroundColor(DS.Color.textPrimary)
                                        Spacer()
                                        Text(server.ipAddress)
                                            .font(DS.Font.mono(12))
                                            .foregroundColor(DS.Color.textMuted)
                                    }
                                    .padding(.vertical, DS.Spacing.xs.rawValue)
                                }
                            }
                        }
                    }
                    .padding(DS.Spacing.lg.rawValue)
                    .background(DS.Color.surface)
                    .cornerRadius(DS.Radius.card.rawValue)

                    // About App Section
                    VStack(alignment: .leading, spacing: DS.Spacing.sm.rawValue) {
                        Text("THÔNG TIN")
                            .font(DS.Font.mono(12))
                            .fontWeight(.bold)
                            .foregroundColor(DS.Color.textMuted)

                        HStack {
                            Text("Phiên bản")
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.textPrimary)
                            Spacer()
                            Text("1.0.3")
                                .font(DS.Font.mono(13))
                                .foregroundColor(DS.Color.textMuted)
                        }
                        .padding(DS.Spacing.md.rawValue)
                        .background(DS.Color.surface)
                        .cornerRadius(DS.Radius.card.rawValue)

                        HStack {
                            Text("Chế độ mạng")
                                .font(DS.Font.body())
                                .foregroundColor(DS.Color.textPrimary)
                            Spacer()
                            Text("LAN Direct (Chunked 1MB)")
                                .font(DS.Font.mono(13))
                                .foregroundColor(DS.Color.textMuted)
                        }
                        .padding(DS.Spacing.md.rawValue)
                        .background(DS.Color.surface)
                        .cornerRadius(DS.Radius.card.rawValue)
                    }
                }
                .padding(DS.Spacing.lg.rawValue)
            }
            .background(DS.Color.background.ignoresSafeArea())
            .navigationTitle("Cài đặt")
            .onAppear {
                inputIP = appState.serverIP
            }
            .sheet(isPresented: $showingQRScanner) {
                QRScannerView { scannedIP, scannedPort in
                    inputIP = scannedIP
                    Task {
                        isConnecting = true
                        connectionFeedback = "Đang kết nối đến \(scannedIP)..."
                        let ok = await appState.connect(toIP: scannedIP, port: scannedPort)
                        isConnecting = false
                        if ok {
                            connectionFeedback = "Kết nối thành công qua mã QR!"
                        } else {
                            connectionFeedback = "Không thể kết nối đến \(scannedIP):\(scannedPort)"
                        }
                    }
                }
            }
        }
    }

    private func connectManual() async {
        isConnecting = true
        connectionFeedback = nil
        appState.serverIP = inputIP.trimmingCharacters(in: .whitespaces)

        await appState.connect()
        isConnecting = false

        if appState.isConnected {
            connectionFeedback = "Kết nối thành công!"
        } else {
            connectionFeedback = "Không thể kết nối tới máy chủ. Vui lòng kiểm tra IP và cổng 8765."
        }
    }
}
