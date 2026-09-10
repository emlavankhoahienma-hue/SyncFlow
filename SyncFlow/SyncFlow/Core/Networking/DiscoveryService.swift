import Foundation
import Network

class DiscoveryService: NSObject, ObservableObject, NetServiceBrowserDelegate, NetServiceDelegate {
    @Published var discoveredServers: [DiscoveredServer] = []
    @Published var isSearching = false

    private var browser: NetServiceBrowser?
    private var resolvingServices: [NetService] = []

    struct DiscoveredServer: Identifiable, Hashable {
        let id = UUID()
        let name: String
        let hostName: String
        let port: Int
        let ipAddress: String

        var baseURL: URL? {
            URL(string: "http://\(ipAddress):\(port)")
        }
    }

    func startDiscovery() {
        stopDiscovery()
        isSearching = true
        browser = NetServiceBrowser()
        browser?.delegate = self
        browser?.searchForServices(ofType: "_syncflow._tcp", inDomain: "local.")
    }

    func stopDiscovery() {
        isSearching = false
        browser?.stop()
        browser = nil
        resolvingServices.removeAll()
    }

    // MARK: - NetServiceBrowserDelegate
    func netServiceBrowser(_ browser: NetServiceBrowser, didFind service: NetService, moreComing: Bool) {
        resolvingServices.append(service)
        service.delegate = self
        service.resolve(withTimeout: 5.0)
    }

    func netServiceBrowser(_ browser: NetServiceBrowser, didRemove service: NetService, moreComing: Bool) {
        DispatchQueue.main.async {
            self.discoveredServers.removeAll { $0.name == service.name }
        }
    }

    // MARK: - NetServiceDelegate
    func netServiceDidResolveAddress(_ sender: NetService) {
        resolvingServices.removeAll { $0 == sender }
        guard let addresses = sender.addresses else { return }

        for addressData in addresses {
            var hostname = [CChar](repeating: 0, count: Int(NI_MAXHOST))
            addressData.withUnsafeBytes { rawBuffer in
                guard let socketAddress = rawBuffer.baseAddress?.assumingMemoryBound(to: sockaddr.self) else { return }
                if socketAddress.pointee.sa_family == AF_INET { // IPv4
                    if getnameinfo(socketAddress, socklen_t(addressData.count), &hostname, socklen_t(hostname.count), nil, 0, NI_NUMERICHOST) == 0 {
                        let ip = String(cString: hostname)
                        DispatchQueue.main.async {
                            let server = DiscoveredServer(
                                name: sender.name,
                                hostName: sender.hostName ?? "Desktop",
                                port: sender.port,
                                ipAddress: ip
                            )
                            if !self.discoveredServers.contains(where: { $0.ipAddress == ip && $0.port == server.port }) {
                                self.discoveredServers.append(server)
                            }
                        }
                    }
                }
            }
        }
    }
}
