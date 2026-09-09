import SwiftUI
import PhotosUI

struct SelectedMediaItem: Identifiable {
    let id = UUID()
    let name: String
    let ext: String
    let tempURL: URL
    let size: Int64
}

struct PhotoVideoPicker: UIViewControllerRepresentable {
    @Binding var selectedItems: [SelectedMediaItem]
    @Environment(\.presentationMode) var presentationMode

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        // Mandated: .any(of: [.images, .videos]) supports all Photo Library formats
        config.filter = .any(of: [.images, .videos])
        config.selectionLimit = 0 // 0 means multiple selection

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: PhotoVideoPicker

        init(_ parent: PhotoVideoPicker) {
            self.parent = parent
        }

        func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            parent.presentationMode.wrappedValue.dismiss()
            guard !results.isEmpty else { return }

            for result in results {
                let provider = result.itemProvider

                // Pitfall 2: Load file directly via loadFileRepresentation or loadDataRepresentation
                // DO NOT load into UIImage (destroys metadata/EXIF/depth).
                if let typeIdentifier = provider.registeredTypeIdentifiers.first {
                    provider.loadFileRepresentation(forTypeIdentifier: typeIdentifier) { url, error in
                        guard let sourceURL = url, error == nil else { return }

                        let tempDir = FileManager.default.temporaryDirectory
                        let uniqueName = "\(UUID().uuidString)_\(sourceURL.lastPathComponent)"
                        let destination = tempDir.appendingPathComponent(uniqueName)

                        do {
                            try? FileManager.default.removeItem(at: destination)
                            try FileManager.default.copyItem(at: sourceURL, to: destination)
                            let attrs = try FileManager.default.attributesOfItem(atPath: destination.path)
                            let size = (attrs[.size] as? Int64) ?? 0

                            let mediaItem = SelectedMediaItem(
                                name: sourceURL.deletingPathExtension().lastPathComponent,
                                ext: sourceURL.pathExtension.lowercased(),
                                tempURL: destination,
                                size: size
                            )

                            DispatchQueue.main.async {
                                self.parent.selectedItems.append(mediaItem)
                            }
                        } catch {
                            // ignore copy error
                        }
                    }
                }
            }
        }
    }
}
