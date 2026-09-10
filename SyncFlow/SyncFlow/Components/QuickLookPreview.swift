import SwiftUI
import QuickLook

/// Native Apple QuickLook Preview for inspecting images, videos, PDFs, office documents, and files.
struct QuickLookPreview: UIViewControllerRepresentable {
    let url: URL

    @Environment(\.presentationMode) var presentationMode

    func makeUIViewController(context: Context) -> QLPreviewController {
        let controller = QLPreviewController()
        controller.dataSource = context.coordinator
        controller.delegate = context.coordinator
        return controller
    }

    func updateUIViewController(_ uiViewController: QLPreviewController, context: Context) {}

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    class Coordinator: NSObject, QLPreviewControllerDataSource, QLPreviewControllerDelegate {
        let parent: QuickLookPreview

        init(parent: QuickLookPreview) {
            self.parent = parent
        }

        func numberOfPreviewItems(in controller: QLPreviewController) -> Int {
            return 1
        }

        func previewController(_ controller: QLPreviewController, previewItemAt index: Int) -> QLPreviewItem {
            return parent.url as NSURL
        }

        func previewControllerDidDismiss(_ controller: QLPreviewController) {
            parent.presentationMode.wrappedValue.dismiss()
        }
    }
}
