import Foundation

struct RemoteFileItem: Identifiable, Codable {
    let fileId: String
    let name: String
    let ext: String
    let mime: String
    let size: Int64
    let device: String

    var id: String { fileId }

    enum CodingKeys: String, CodingKey {
        case fileId = "file_id"
        case name
        case ext
        case mime
        case size
        case device
    }

    var formattedSize: String {
        let mb = Double(size) / (1024 * 1024)
        return String(format: "%.1f MB", mb)
    }
}

class APIClient {
    static let shared = APIClient()

    func checkHealth(serverURL: URL) async throws -> (deviceName: String, version: String) {
        let healthURL = serverURL.appendingPathComponent("health")
        var req = URLRequest(url: healthURL)
        req.timeoutInterval = 3.0

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
            throw NSError(domain: "APIClient", code: 500, userInfo: [NSLocalizedDescriptionKey: "Máy chủ không phản hồi"])
        }

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let name = json["device_name"] as? String,
              let ver = json["version"] as? String else {
            throw NSError(domain: "APIClient", code: 500, userInfo: [NSLocalizedDescriptionKey: "Dữ liệu trả về không đúng"])
        }

        return (name, ver)
    }

    func fetchFiles(serverURL: URL) async throws -> [RemoteFileItem] {
        let filesURL = serverURL.appendingPathComponent("files")
        var req = URLRequest(url: filesURL)
        req.timeoutInterval = 5.0
        if let sessionID = CryptoManager.shared.sessionID {
            req.setValue(sessionID, forHTTPHeaderField: "X-Session-ID")
        }

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
            throw NSError(domain: "APIClient", code: 500, userInfo: [NSLocalizedDescriptionKey: "Không thể lấy danh sách file"])
        }

        let decoder = JSONDecoder()
        return try decoder.decode([RemoteFileItem].self, from: data)
    }

    func downloadFile(
        fileItem: RemoteFileItem,
        serverURL: URL,
        onProgress: @escaping (Int64, Double, Double) -> Void
    ) async throws -> URL {
        let downloadURL = serverURL.appendingPathComponent("download/\(fileItem.fileId)")
        let docsDir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let destinationURL = docsDir.appendingPathComponent(fileItem.name)

        var existingBytes: Int64 = 0
        if FileManager.default.fileExists(atPath: destinationURL.path) {
            let attrs = try FileManager.default.attributesOfItem(atPath: destinationURL.path)
            existingBytes = (attrs[.size] as? Int64) ?? 0
            if existingBytes >= fileItem.size {
                return destinationURL // Already complete
            } else if existingBytes > fileItem.size {
                // Stale or invalid size, reset
                try? FileManager.default.removeItem(at: destinationURL)
                existingBytes = 0
            }
        }

        var req = URLRequest(url: downloadURL)
        req.timeoutInterval = 60.0
        if let sessionID = CryptoManager.shared.sessionID {
            req.setValue(sessionID, forHTTPHeaderField: "X-Session-ID")
        }
        if CryptoManager.shared.isE2EEActive {
            req.setValue("1", forHTTPHeaderField: "X-Encrypted")
        }
        if existingBytes > 0 {
            req.setValue("bytes=\(existingBytes)-", forHTTPHeaderField: "Range")
        }

        let (asyncBytes, resp) = try await URLSession.shared.bytes(for: req)
        guard let http = resp as? HTTPURLResponse, (http.statusCode == 200 || http.statusCode == 206) else {
            let code = (resp as? HTTPURLResponse)?.statusCode ?? 500
            throw NSError(domain: "APIClient", code: code, userInfo: [NSLocalizedDescriptionKey: "Lỗi tải file: HTTP \(code)"])
        }

        let fileHandle: FileHandle
        if existingBytes > 0 && FileManager.default.fileExists(atPath: destinationURL.path) {
            fileHandle = try FileHandle(forWritingTo: destinationURL)
            try fileHandle.seekToEnd()
        } else {
            FileManager.default.createFile(atPath: destinationURL.path, contents: nil)
            fileHandle = try FileHandle(forWritingTo: destinationURL)
        }
        defer {
            try? fileHandle.synchronize()
            try? fileHandle.close()
        }

        var currentBytes: Int64 = existingBytes
        var lastTime = Date()
        var lastBytes = currentBytes

        let isEncrypted = (http.value(forHTTPHeaderField: "X-Encrypted") == "1")

        if isEncrypted {
            // Read framed encrypted chunks: [4 bytes length N] + [N bytes AES-GCM data]
            var streamBuffer = Data()
            var expectedLength: Int? = nil

            for try await byte in asyncBytes {
                streamBuffer.append(byte)

                while true {
                    if expectedLength == nil {
                        if streamBuffer.count >= 4 {
                            let lenBytes = streamBuffer.prefix(4)
                            let length = lenBytes.withUnsafeBytes { $0.load(as: UInt32.self).bigEndian }
                            expectedLength = Int(length)
                            streamBuffer.removeSubrange(0..<4)
                        } else {
                            break
                        }
                    }

                    if let length = expectedLength {
                        if streamBuffer.count >= length {
                            let encryptedChunk = streamBuffer.prefix(length)
                            streamBuffer.removeSubrange(0..<length)
                            expectedLength = nil

                            let decryptedChunk = try CryptoManager.shared.decryptChunk(Data(encryptedChunk))
                            try fileHandle.write(contentsOf: decryptedChunk)
                            currentBytes += Int64(decryptedChunk.count)

                            let now = Date()
                            let timeDiff = now.timeIntervalSince(lastTime)
                            if timeDiff >= 0.25 {
                                let speed = Double(currentBytes - lastBytes) / timeDiff
                                let remaining = max(0, fileItem.size - currentBytes)
                                let eta = speed > 0 ? Double(remaining) / speed : 0.0
                                onProgress(currentBytes, speed, eta)
                                lastTime = now
                                lastBytes = currentBytes
                            }
                        } else {
                            break
                        }
                    } else {
                        break
                    }
                }
            }
        } else {
            // Standard plaintext stream
            var buffer = Data()
            let bufferCapacity = 64 * 1024 // 64KB buffer for efficient disk writes

            for try await byte in asyncBytes {
                buffer.append(byte)
                if buffer.count >= bufferCapacity {
                    try fileHandle.write(contentsOf: buffer)
                    currentBytes += Int64(buffer.count)
                    buffer.removeAll(keepingCapacity: true)

                    let now = Date()
                    let timeDiff = now.timeIntervalSince(lastTime)
                    if timeDiff >= 0.25 {
                        let speed = Double(currentBytes - lastBytes) / timeDiff
                        let remaining = max(0, fileItem.size - currentBytes)
                        let eta = speed > 0 ? Double(remaining) / speed : 0.0
                        onProgress(currentBytes, speed, eta)
                        lastTime = now
                        lastBytes = currentBytes
                    }
                }
            }

            if !buffer.isEmpty {
                try fileHandle.write(contentsOf: buffer)
                currentBytes += Int64(buffer.count)
            }
        }

        try? fileHandle.synchronize()
        onProgress(fileItem.size, 0, 0)
        return destinationURL
    }
}
