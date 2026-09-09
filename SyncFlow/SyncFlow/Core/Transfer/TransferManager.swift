import Foundation
import SwiftUI
import UIKit

@MainActor
class TransferManager: ObservableObject {
    @Published var queue: [TransferItem] = []
    @Published var activeTransfers: [TransferItem] = []
    @Published var completedTransfers: [TransferItem] = []

    private let maxConcurrentTransfers = 2 // Mandated maximum 2 concurrent transfers
    private var uploaderMap: [UUID: ChunkUploader] = [:]
    private var tasksMap: [UUID: Task<Void, Never>] = [:]

    func enqueueUpload(
        name: String,
        ext: String,
        fileURL: URL,
        size: Int64,
        autoConvert: Bool,
        serverURL: URL
    ) {
        let item = TransferItem(
            name: name,
            ext: ext,
            fileURL: fileURL,
            size: size,
            direction: .upload,
            targetExtension: autoConvert ? getTargetExtension(for: ext) : nil
        )

        queue.append(item)
        processQueue(serverURL: serverURL)
    }

    func enqueueDownload(
        fileItem: RemoteFileItem,
        serverURL: URL
    ) {
        let item = TransferItem(
            name: fileItem.name,
            ext: fileItem.ext,
            fileId: fileItem.fileId,
            size: fileItem.size,
            direction: .download
        )

        queue.append(item)
        processQueue(serverURL: serverURL)
    }

    func processQueue(serverURL: URL) {
        while activeTransfers.count < maxConcurrentTransfers && !queue.isEmpty {
            let nextItem = queue.removeFirst()
            activeTransfers.append(nextItem)

            let task = Task {
                if nextItem.direction == .upload {
                    await self.executeUpload(item: nextItem, serverURL: serverURL)
                } else {
                    await self.executeDownload(item: nextItem, serverURL: serverURL)
                }
                self.activeTransfers.removeAll { $0.id == nextItem.id }
                self.completedTransfers.insert(nextItem, at: 0)
                self.tasksMap.removeValue(forKey: nextItem.id)
                self.uploaderMap.removeValue(forKey: nextItem.id)
                self.processQueue(serverURL: serverURL)
            }
            tasksMap[nextItem.id] = task
        }
    }

    private func executeUpload(item: TransferItem, serverURL: URL) async {
        guard var sourceURL = item.fileURL else {
            item.status = .failed("Không có URL nguồn")
            return
        }

        // Conversion Phase
        let extLower = item.ext.lowercased()
        if let targetExt = item.targetExtension {
            if ["heic", "heif"].contains(extLower) && targetExt == "png" {
                item.status = .converting("HEIC → PNG")
                do {
                    let convertedURL = try await HEICConverter.shared.convertToPNG(sourceURL: sourceURL)
                    sourceURL = convertedURL
                    item.fileURL = convertedURL
                } catch {
                    // Fallback to original file + warning as mandated by Section 6
                    item.targetExtension = nil
                }
            } else if ["mov", "hevc"].contains(extLower) && targetExt == "mp4" {
                item.status = .converting("HEVC → MP4")
                do {
                    let convertedURL = try await HEVCConverter.shared.convertToMP4(sourceURL: sourceURL)
                    sourceURL = convertedURL
                    item.fileURL = convertedURL
                } catch {
                    // Fallback to original file
                    item.targetExtension = nil
                }
            }
        }

        // Upload Phase
        let uploader = ChunkUploader()
        uploaderMap[item.id] = uploader

        do {
            try await uploader.upload(item: item, serverBaseURL: serverURL) { bytes, speed, eta in
                DispatchQueue.main.async {
                    item.bytesTransferred = bytes
                    item.speedBps = speed
                    item.etaSeconds = eta
                }
            }
            item.status = .completed
            triggerSuccessFeedback()
        } catch {
            item.status = .failed(error.localizedDescription)
            triggerErrorFeedback()
        }
    }

    private func executeDownload(item: TransferItem, serverURL: URL) async {
        guard let fileId = item.fileId else {
            item.status = .failed("Mã file tải về không hợp lệ")
            return
        }

        let remoteItem = RemoteFileItem(
            fileId: fileId,
            name: item.name,
            ext: item.ext,
            mime: "application/octet-stream",
            size: item.size,
            device: "Desktop"
        )

        item.status = .inProgress
        do {
            let localURL = try await APIClient.shared.downloadFile(fileItem: remoteItem, serverURL: serverURL) { bytes, speed, eta in
                DispatchQueue.main.async {
                    item.bytesTransferred = bytes
                    item.speedBps = speed
                    item.etaSeconds = eta
                }
            }
            item.fileURL = localURL
            item.status = .completed
            triggerSuccessFeedback()
        } catch {
            item.status = .failed(error.localizedDescription)
            triggerErrorFeedback()
        }
    }

    func cancelTransfer(item: TransferItem) {
        if let uploader = uploaderMap[item.id] {
            uploader.cancel()
        }
        if let task = tasksMap[item.id] {
            task.cancel()
        }
        activeTransfers.removeAll { $0.id == item.id }
        queue.removeAll { $0.id == item.id }
        item.status = .failed("Đã hủy")
        completedTransfers.insert(item, at: 0)
    }

    func cancelAll() {
        for item in activeTransfers {
            cancelTransfer(item: item)
        }
        queue.removeAll()
    }

    private func getTargetExtension(for ext: String) -> String? {
        let lower = ext.lowercased()
        if ["heic", "heif"].contains(lower) { return "png" }
        if ["mov", "hevc"].contains(lower) { return "mp4" }
        return nil
    }

    private func triggerSuccessFeedback() {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(.success)
    }

    private func triggerErrorFeedback() {
        let generator = UINotificationFeedbackGenerator()
        generator.prepare()
        generator.notificationOccurred(.error)
    }
}
