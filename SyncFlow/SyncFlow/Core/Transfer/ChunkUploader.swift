import Foundation
import CommonCrypto

class ChunkUploader {
    static let chunkSize: Int = 1024 * 1024 // Mandated 1MB constant

    private var isCancelled = false
    private var isPaused = false

    func cancel() {
        isCancelled = true
    }

    func pause() {
        isPaused = true
    }

    func resume() {
        isPaused = false
    }

    /// Uploads a file chunk-by-chunk to the FastAPI desktop server.
    func upload(
        item: TransferItem,
        serverBaseURL: URL,
        onProgress: @escaping (Int64, Double, Double) -> Void
    ) async throws {
        guard let fileURL = item.fileURL else {
            throw NSError(domain: "ChunkUploader", code: 400, userInfo: [NSLocalizedDescriptionKey: "Không tìm thấy URL file"])
        }

        let fileHandle = try FileHandle(forReadingFrom: fileURL)
        defer {
            try? fileHandle.close()
        }

        let totalSize = item.size

        // Calculate SHA-256 on disk stream
        item.status = .converting("Tính mã kiểm tra")
        let sha256Hex = try computeSHA256(for: fileURL)
        item.sha256 = sha256Hex

        // Step 1: Init upload
        let initURL = serverBaseURL.appendingPathComponent("upload/init")
        var initReq = URLRequest(url: initURL)
        initReq.httpMethod = "POST"
        initReq.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let metaPayload: [String: Any] = [
            "meta": [
                "file_id": item.id.uuidString,
                "name": item.name,
                "ext": item.ext,
                "mime": "application/octet-stream",
                "size": totalSize,
                "sha256": sha256Hex,
                "converted_ext": item.targetExtension as Any,
                "device": "iPhone"
            ]
        ]
        initReq.httpBody = try JSONSerialization.data(withJSONObject: metaPayload)

        let (initData, initResp) = try await URLSession.shared.data(for: initReq)
        guard let httpInit = initResp as? HTTPURLResponse, httpInit.statusCode == 200 else {
            throw NSError(domain: "ChunkUploader", code: 500, userInfo: [NSLocalizedDescriptionKey: "Khởi tạo tải lên thất bại"])
        }

        guard let json = try JSONSerialization.jsonObject(with: initData) as? [String: Any],
              let transferId = json["transfer_id"] as? String,
              let resumeOffset = json["resume_offset"] as? Int64 else {
            throw NSError(domain: "ChunkUploader", code: 500, userInfo: [NSLocalizedDescriptionKey: "Dữ liệu khởi tạo không hợp lệ"])
        }

        // Seek to resume offset
        try fileHandle.seek(toOffset: UInt64(resumeOffset))
        var currentBytes: Int64 = resumeOffset
        var chunkIndex: Int = Int(resumeOffset / Int64(Self.chunkSize))

        item.status = .inProgress

        var lastTime = Date()
        var lastBytes = currentBytes

        // Step 2: Upload chunks sequentially
        while currentBytes < totalSize {
            if isCancelled {
                throw NSError(domain: "ChunkUploader", code: -999, userInfo: [NSLocalizedDescriptionKey: "Tác vụ đã bị hủy"])
            }
            while isPaused {
                try await Task.sleep(nanoseconds: 200_000_000)
                if isCancelled {
                    throw NSError(domain: "ChunkUploader", code: -999, userInfo: [NSLocalizedDescriptionKey: "Tác vụ đã bị hủy"])
                }
            }

            let bytesToRead = min(Int64(Self.chunkSize), totalSize - currentBytes)
            guard let chunkData = try fileHandle.read(upToCount: Int(bytesToRead)), !chunkData.isEmpty else {
                break
            }

            let chunkURL = serverBaseURL.appendingPathComponent("upload/chunk/\(transferId)")
            var chunkReq = URLRequest(url: chunkURL)
            chunkReq.httpMethod = "POST"
            chunkReq.setValue("application/octet-stream", forHTTPHeaderField: "Content-Type")
            chunkReq.setValue(String(chunkIndex), forHTTPHeaderField: "X-Chunk-Index")
            chunkReq.httpBody = chunkData

            let (_, chunkResp) = try await URLSession.shared.data(for: chunkReq)
            guard let httpChunk = chunkResp as? HTTPURLResponse, httpChunk.statusCode == 200 else {
                throw NSError(domain: "ChunkUploader", code: 502, userInfo: [NSLocalizedDescriptionKey: "Lỗi gửi chunk \(chunkIndex)"])
            }

            currentBytes += Int64(chunkData.count)
            chunkIndex += 1

            let now = Date()
            let timeDiff = now.timeIntervalSince(lastTime)
            if timeDiff >= 0.25 {
                let speed = Double(currentBytes - lastBytes) / timeDiff
                let remaining = max(0, totalSize - currentBytes)
                let eta = speed > 0 ? Double(remaining) / speed : 0.0
                onProgress(currentBytes, speed, eta)
                lastTime = now
                lastBytes = currentBytes
            }
        }

        // Step 3: Complete upload and verify SHA-256
        let completeURL = serverBaseURL.appendingPathComponent("upload/complete/\(transferId)")
        var compReq = URLRequest(url: completeURL)
        compReq.httpMethod = "POST"

        let (compData, compResp) = try await URLSession.shared.data(for: compReq)
        guard let httpComp = compResp as? HTTPURLResponse, httpComp.statusCode == 200 else {
            throw NSError(domain: "ChunkUploader", code: 500, userInfo: [NSLocalizedDescriptionKey: "Xác thực tải lên thất bại"])
        }

        guard let compJson = try JSONSerialization.jsonObject(with: compData) as? [String: Any],
              let verified = compJson["verified"] as? Bool, verified else {
            let msg = (try? JSONSerialization.jsonObject(with: compData) as? [String: Any])?["message"] as? String ?? "Mã SHA-256 không khớp"
            throw NSError(domain: "ChunkUploader", code: 400, userInfo: [NSLocalizedDescriptionKey: msg])
        }

        onProgress(totalSize, 0, 0)
    }

    private func computeSHA256(for url: URL) throws -> String {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }

        var context = CC_SHA256_CTX()
        CC_SHA256_Init(&context)

        while let chunk = try handle.read(upToCount: Self.chunkSize), !chunk.isEmpty {
            chunk.withUnsafeBytes { buffer in
                _ = CC_SHA256_Update(&context, buffer.baseAddress, CC_LONG(buffer.count))
            }
        }

        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        CC_SHA256_Final(&digest, &context)

        return digest.map { String(format: "%02x", $0) }.joined()
    }
}
