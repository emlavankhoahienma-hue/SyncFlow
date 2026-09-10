import SwiftUI
import Combine

enum ConnectionState {
    case disconnected
    case connecting
    case connected(serverName: String)
}

@MainActor
class AppState: ObservableObject {
    @Published var serverIP: String = "192.168.1.100" {
        didSet {
            UserDefaults.standard.set(serverIP, forKey: "syncflow_server_ip")
        }
    }
    @Published var serverPort: Int = 8765
    @Published var connectionState: ConnectionState = .disconnected
    @Published var autoDiscoverEnabled: Bool = true
    @Published var autoConvertEnabled: Bool = true

    let transferManager = TransferManager()
    let discoveryService = DiscoveryService()
    let syncWebSocket = SyncWebSocket()

    private var cancellables = Set<AnyCancellable>()

    var serverBaseURL: URL? {
        let cleaned = serverIP.trimmingCharacters(in: .whitespacesAndNewlines)
        return URL(string: "http://\(cleaned):\(serverPort)")
    }

    var isConnected: Bool {
        if case .connected = connectionState { return true }
        return false
    }

    init() {
        if let savedIP = UserDefaults.standard.string(forKey: "syncflow_server_ip"), !savedIP.isEmpty {
            self.serverIP = savedIP
        }

        // Forward nested transferManager changes to AppState
        transferManager.objectWillChange
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                self?.objectWillChange.send()
            }
            .store(in: &cancellables)

        // Hook WebSocket events from desktop server
        syncWebSocket.onDoneReceived = { [weak self] transferId, path in
            DispatchQueue.main.async {
                NotificationCenter.default.post(name: .transferDidComplete, object: path)
                self?.objectWillChange.send()
            }
        }

        // Hook Bonjour discovery results
        discoveryService.$discoveredServers
            .sink { [weak self] servers in
                guard let self = self, self.autoDiscoverEnabled else { return }
                if let firstServer = servers.first, !self.isConnected {
                    self.serverIP = firstServer.ipAddress
                    self.serverPort = firstServer.port
                    Task {
                        await self.connect()
                    }
                }
            }
            .store(in: &cancellables)

        // Start discovery if enabled
        if autoDiscoverEnabled {
            discoveryService.startDiscovery()
        }
    }

    func connect(toIP ip: String, port: Int = 8765) async -> Bool {
        self.serverIP = ip.trimmingCharacters(in: .whitespacesAndNewlines)
        self.serverPort = port
        await connect()
        return isConnected
    }

    func connect() async {
        guard let url = serverBaseURL else { return }
        connectionState = .connecting

        for attempt in 1...2 {
            do {
                let (deviceName, _) = try await APIClient.shared.checkHealth(serverURL: url)
                
                // Perform zero-secret E2EE handshake
                do {
                    try await CryptoManager.shared.performHandshake(serverURL: url)
                } catch {
                    print("E2EE Handshake notice: \(error)")
                }

                connectionState = .connected(serverName: deviceName)
                syncWebSocket.connect(to: url)
                return
            } catch {
                if attempt < 2 {
                    try? await Task.sleep(nanoseconds: 300_000_000)
                }
            }
        }
        connectionState = .disconnected
    }

    func disconnect() {
        CryptoManager.shared.resetSession()
        syncWebSocket.disconnect()
        connectionState = .disconnected
    }
}
