import SwiftUI
import UniformTypeIdentifiers

struct AnyFilePicker: UIViewControllerRepresentable {
    @Binding var selectedItems: [SelectedMediaItem]
    @Environment(\.presentationMode) var presentationMode

    func makeUIViewController(context: Context) -> UIDocumentPickerViewController {
        // Mandated: [.data, .content] covers thousands of file formats without hardcoding
        let picker = UIDocumentPickerViewController(
            forOpeningContentTypes: [.data, .content],
            asCopy: true
        )
        picker.allowsMultipleSelection = true
        picker.shouldShowFileExtensions = true
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: UIDocumentPickerViewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    class Coordinator: NSObject, UIDocumentPickerDelegate {
        let parent: AnyFilePicker

        init(_ parent: AnyFilePicker) {
            self.parent = parent
        }

        func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL]) {
            parent.presentationMode.wrappedValue.dismiss()

            for sourceURL in urls {
                let isAccessing = sourceURL.startAccessingSecurityScopedResource()
                defer {
                    if isAccessing {
                        sourceURL.stopAccessingSecurityScopedResource()
                    }
                }

                let tempDir = FileManager.default.temporaryDirectory
                let uniqueName = "\(UUID().uuidString)_\(sourceURL.lastPathComponent)"
                let destination = tempDir.appendingPathComponent(uniqueName)

                do {
                    try? FileManager.default.removeItem(at: destination)
                    try FileManager.default.copyItem(at: sourceURL, to: destination)
                    let attrs = try FileManager.default.attributesOfItem(atPath: destination.path)
                    let size = (attrs[.size] as? Int64) ?? 0

                    let item = SelectedMediaItem(
                        name: sourceURL.deletingPathExtension().lastPathComponent,
                        ext: sourceURL.pathExtension.lowercased(),
                        tempURL: destination,
                        size: size
                    )

                    DispatchQueue.main.async {
                        self.parent.selectedItems.append(item)
                    }
                } catch {
                    // ignore error
                }
            }
        }
    }
}
