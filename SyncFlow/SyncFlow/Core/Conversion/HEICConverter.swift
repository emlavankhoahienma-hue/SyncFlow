import Foundation
import ImageIO
import UniformTypeIdentifiers

class HEICConverter {
    static let shared = HEICConverter()

    enum ConversionError: LocalizedError {
        case sourceCreationFailed
        case destinationCreationFailed
        case finalizeFailed

        var errorDescription: String? {
            switch self {
            case .sourceCreationFailed:
                return "Không thể mở file HEIC nguồn"
            case .destinationCreationFailed:
                return "Không thể tạo file PNG đích"
            case .finalizeFailed:
                return "Không thể hoàn tất chuyển đổi PNG"
            }
        }
    }

    /// Converts a HEIC/HEIF image URL to a temporary PNG file preserving full quality and color depth.
    func convertToPNG(sourceURL: URL) async throws -> URL {
        return try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                guard let imageSource = CGImageSourceCreateWithURL(sourceURL as CFURL, nil) else {
                    continuation.resume(throwing: ConversionError.sourceCreationFailed)
                    return
                }

                let tempOutputURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(UUID().uuidString)
                    .appendingPathExtension("png")

                guard let destination = CGImageDestinationCreateWithURL(
                    tempOutputURL as CFURL,
                    UTType.png.identifier as CFString,
                    1,
                    nil
                ) else {
                    continuation.resume(throwing: ConversionError.destinationCreationFailed)
                    return
                }

                // Copy all properties to preserve color profile, orientation, etc.
                let options: [CFString: Any] = [
                    kCGImageDestinationLossless: true,
                    kCGImageSourceShouldCache: false
                ]

                CGImageDestinationAddImageFromSource(destination, imageSource, 0, options as CFDictionary)

                if CGImageDestinationFinalize(destination) {
                    continuation.resume(returning: tempOutputURL)
                } else {
                    continuation.resume(throwing: ConversionError.finalizeFailed)
                }
            }
        }
    }
}
