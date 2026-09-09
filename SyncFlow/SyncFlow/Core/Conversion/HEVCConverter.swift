import Foundation
import AVFoundation

class HEVCConverter {
    static let shared = HEVCConverter()

    enum ConversionError: LocalizedError {
        case exportSessionCreationFailed
        case exportFailed(String)
        case unsupportedFormat

        var errorDescription: String? {
            switch self {
            case .exportSessionCreationFailed:
                return "Không thể khởi tạo phiên xuất video"
            case .exportFailed(let reason):
                return "Lỗi xuất video: \(reason)"
            case .unsupportedFormat:
                return "Định dạng video không được hỗ trợ"
            }
        }
    }

    /// Converts HEVC/QuickTime .mov to MP4 (with fallback to Passthrough for HDR videos as specified in Pitfall 3).
    func convertToMP4(sourceURL: URL) async throws -> URL {
        let asset = AVURLAsset(url: sourceURL)

        // Try highest quality preset first
        do {
            return try await performExport(asset: asset, presetName: AVAssetExportPresetHighestQuality)
        } catch {
            // Pitfall 3: MOV with HDR can fail with highest quality -> retry preset Passthrough
            return try await performExport(asset: asset, presetName: AVAssetExportPresetPassthrough)
        }
    }

    private func performExport(asset: AVAsset, presetName: String) async throws -> URL {
        let tempOutputURL = FileManager.default.temporaryDirectory
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mp4")

        guard let exportSession = AVAssetExportSession(asset: asset, presetName: presetName) else {
            throw ConversionError.exportSessionCreationFailed
        }

        exportSession.outputURL = tempOutputURL
        exportSession.outputFileType = .mp4
        exportSession.shouldOptimizeForNetworkUse = true

        await exportSession.export()

        switch exportSession.status {
        case .completed:
            return tempOutputURL
        case .failed:
            let errorMsg = exportSession.error?.localizedDescription ?? "Không xác định"
            throw ConversionError.exportFailed(errorMsg)
        case .cancelled:
            throw ConversionError.exportFailed("Tác vụ bị hủy")
        default:
            throw ConversionError.exportFailed("Trạng thái xuất không hợp lệ")
        }
    }
}
