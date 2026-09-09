import Foundation

class SyncWebSocket: ObservableObject {
    private var webSocketTask: URLSessionWebSocketTask?
    private var isConnected = false
    private var serverURL: URL?

    var onProgressReceived: ((String, Int64, Int64, Double, Double) -> Void)?
    var onDoneReceived: ((String, String) -> Void)?
    var onErrorReceived: ((String, String) -> Void)?

    func connect(to baseHttpURL: URL) {
        disconnect()

        guard var components = URLComponents(url: baseHttpURL, resolvingAgainstBaseURL: false) else { return }
        components.scheme = components.scheme == "https" ? "wss" : "ws"
        components.path = "/ws"

        guard let wsURL = components.url else { return }
        self.serverURL = wsURL

        let session = URLSession(configuration: .default)
        webSocketTask = session.webSocketTask(with: wsURL)
        webSocketTask?.resume()
        isConnected = true
        listen()
    }

    func disconnect() {
        isConnected = false
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
    }

    private func listen() {
        webSocketTask?.receive { [weak self] result in
            guard let self = self, self.isConnected else { return }

            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    self.handleMessage(text: text)
                case .data(let data):
                    if let text = String(data: data, encoding: .utf8) {
                        self.handleMessage(text: text)
                    }
                @unknown default:
                    break
                }
                self.listen()

            case .failure:
                self.isConnected = false
                // Attempt reconnect after 3 seconds
                DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                    if let sURL = self.serverURL {
                        self.connect(to: sURL)
                    }
                }
            }
        }
    }

    private func handleMessage(text: String) {
        guard let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else {
            return
        }

        DispatchQueue.main.async {
            switch type {
            case "progress":
                if let transferId = json["transfer_id"] as? String,
                   let sent = json["sent"] as? Int64,
                   let total = json["total"] as? Int64,
                   let speed = json["speed_bps"] as? Double,
                   let eta = json["eta_s"] as? Double {
                    self.onProgressReceived?(transferId, sent, total, speed, eta)
                }
            case "done":
                if let transferId = json["transfer_id"] as? String,
                   let path = json["path"] as? String {
                    self.onDoneReceived?(transferId, path)
                }
            case "error":
                if let transferId = json["transfer_id"] as? String,
                   let msg = json["message"] as? String {
                    self.onErrorReceived?(transferId, msg)
                }
            default:
                break
            }
        }
    }
}
