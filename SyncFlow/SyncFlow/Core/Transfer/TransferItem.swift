import Foundation
import SwiftUI

enum TransferDirection {
    case upload
    case download
}

enum TransferStatus: Equatable {
    case waiting
    case converting(String)
    case inProgress
    case paused
    case completed
    case failed(String)

    var description: String {
        switch self {
        case .waiting: return "Đang chờ"
        case .converting(let type): return "Đang chuyển đổi (\(type))..."
        case .inProgress: return "Đang truyền"
        case .paused: return "Tạm dừng"
        case .completed: return "Hoàn tất"
        case .failed(let err): return "Lỗi: \(err)"
        }
    }
}

class TransferItem: Identifiable, ObservableObject {
    let id: UUID
    let name: String
    let ext: String
    var fileURL: URL?
    var fileId: String? // for download from server
    let size: Int64
    let direction: TransferDirection
    var targetExtension: String?

    @Published var status: TransferStatus = .waiting
    @Published var bytesTransferred: Int64 = 0
    @Published var speedBps: Double = 0.0
    @Published var etaSeconds: Double = 0.0
    @Published var sha256: String?

    var progress: Double {
        guard size > 0 else { return 0.0 }
        return Double(bytesTransferred) / Double(size)
    }

    var formattedSpeed: String {
        let mbps = speedBps / (1024 * 1024)
        return String(format: "%.1f MB/s", mbps)
    }

    var formattedProgressText: String {
        let curMB = Double(bytesTransferred) / (1024 * 1024)
        let totalMB = Double(size) / (1024 * 1024)
        return String(format: "%.1f MB / %.1f MB", curMB, totalMB)
    }

    var formattedEta: String {
        if etaSeconds <= 0 || status != .inProgress { return "" }
        return String(format: "ETA: %.0fs", etaSeconds)
    }

    init(
        id: UUID = UUID(),
        name: String,
        ext: String,
        fileURL: URL? = nil,
        fileId: String? = nil,
        size: Int64,
        direction: TransferDirection = .upload,
        targetExtension: String? = nil
    ) {
        self.id = id
        self.name = name
        self.ext = ext
        self.fileURL = fileURL
        self.fileId = fileId
        self.size = size
        self.direction = direction
        self.targetExtension = targetExtension
    }
}
