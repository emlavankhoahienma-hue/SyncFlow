import SwiftUI

@main
struct SyncFlowApp: App {
    @StateObject private var appState = AppState()
    @State private var selectedTab = 0

    var body: some Scene {
        WindowGroup {
            TabView(selection: $selectedTab) {
                HomeView(selectedTab: $selectedTab)
                    .tabItem {
                        Label("Trang chủ", systemImage: "house.fill")
                    }
                    .tag(0)

                SendView(selectedTab: $selectedTab)
                    .tabItem {
                        Label("Gửi", systemImage: "arrow.up.circle.fill")
                    }
                    .tag(1)

                ReceiveView(selectedTab: $selectedTab)
                    .tabItem {
                        Label("Nhận", systemImage: "arrow.down.circle.fill")
                    }
                    .tag(2)

                ProgressViewScreen()
                    .tabItem {
                        Label("Tiến độ", systemImage: "chart.bar.fill")
                    }
                    .tag(3)

                HistoryView()
                    .tabItem {
                        Label("Lịch sử", systemImage: "clock.fill")
                    }
                    .tag(4)

                SettingsView()
                    .tabItem {
                        Label("Cài đặt", systemImage: "gearshape.fill")
                    }
                    .tag(5)
            }
            .tint(DS.Color.primary)
            .environmentObject(appState)
            .preferredColorScheme(.dark) // Mandated by Design System (Dark-first app)
        }
    }
}
