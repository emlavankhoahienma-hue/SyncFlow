import SwiftUI
import AVFoundation

struct QRScannerView: View {
    @Environment(\.dismiss) private var dismiss
    var onCodeScanned: (String, Int) -> Void

    @State private var isTorchOn = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()

                // Camera Preview
                CameraPreviewView(onCodeDetected: { code in
                    handleScannedCode(code)
                }, onError: { err in
                    errorMessage = err
                })
                .ignoresSafeArea()

                // Scanner Overlay (Terra Cotta Viewfinder)
                VStack {
                    Spacer()

                    ZStack {
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(DS.Color.primary, lineWidth: 3)
                            .frame(width: 260, height: 260)
                            .background(Color.black.opacity(0.05))

                        // Corner markers
                        VStack {
                            HStack {
                                cornerMarker
                                Spacer()
                                cornerMarker.rotationEffect(.degrees(90))
                            }
                            Spacer()
                            HStack {
                                cornerMarker.rotationEffect(.degrees(-90))
                                Spacer()
                                cornerMarker.rotationEffect(.degrees(180))
                            }
                        }
                        .frame(width: 260, height: 260)
                    }

                    Text("Hướng camera vào mã QR trên màn hình máy tính")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.white)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                        .padding(.top, 24)

                    if let err = errorMessage {
                        Text(err)
                            .font(.system(size: 13))
                            .foregroundColor(.orange)
                            .padding(.top, 8)
                    }

                    Spacer()

                    // Flashlight toggle
                    Button(action: toggleTorch) {
                        HStack(spacing: 8) {
                            Image(systemName: isTorchOn ? "flashlight.on.fill" : "flashlight.off.fill")
                            Text(isTorchOn ? "Tắt đèn flash" : "Bật đèn flash")
                        }
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.white)
                        .padding(.horizontal, 20)
                        .padding(.vertical, 12)
                        .background(Color.white.opacity(0.2))
                        .cornerRadius(24)
                    }
                    .padding(.bottom, 40)
                }
            }
            .navigationTitle("Quét mã QR kết nối")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Đóng") {
                        dismiss()
                    }
                    .foregroundColor(DS.Color.primary)
                }
            }
        }
    }

    private var cornerMarker: some View {
        Path { path in
            path.move(to: CGPoint(x: 0, y: 24))
            path.addLine(to: CGPoint(x: 0, y: 0))
            path.addLine(to: CGPoint(x: 24, y: 0))
        }
        .stroke(DS.Color.primary, lineWidth: 4)
        .frame(width: 24, height: 24)
    }

    private func handleScannedCode(_ code: String) {
        let trimmed = code.trimmingCharacters(in: .whitespacesAndNewlines)
        var parsedIP: String?
        var parsedPort: Int = 8765

        // Case 1: URL format like http://192.168.1.15:8765 or syncflow://connect?ip=...
        if let url = URL(string: trimmed) {
            if let scheme = url.scheme, scheme == "syncflow",
               let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
               let items = components.queryItems {
                for q in items {
                    if q.name == "ip", let val = q.value {
                        parsedIP = val
                    } else if q.name == "port", let val = q.value, let p = Int(val) {
                        parsedPort = p
                    }
                }
            } else if let host = url.host {
                parsedIP = host
                if let p = url.port {
                    parsedPort = p
                }
            }
        }

        // Case 2: JSON format {"ip":"192.168.1.15","port":8765}
        if parsedIP == nil, let data = trimmed.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            if let ip = json["ip"] as? String {
                parsedIP = ip
            }
            if let p = json["port"] as? Int {
                parsedPort = p
            }
        }

        // Case 3: Raw IP or IP:Port (e.g. 192.168.1.15:8765 or 192.168.1.15)
        if parsedIP == nil {
            let cleaned = trimmed.replacingOccurrences(of: "http://", with: "")
                                 .replacingOccurrences(of: "https://", with: "")
            let parts = cleaned.split(separator: "/")
            if let first = parts.first {
                let ipPort = first.split(separator: ":")
                if ipPort.count == 2, let p = Int(ipPort[1]) {
                    parsedIP = String(ipPort[0])
                    parsedPort = p
                } else if ipPort.count == 1 {
                    parsedIP = String(ipPort[0])
                }
            }
        }

        if let ip = parsedIP, !ip.isEmpty {
            UINotificationFeedbackGenerator().notificationOccurred(.success)
            onCodeScanned(ip, parsedPort)
            dismiss()
        }
    }

    private func toggleTorch() {
        guard let device = AVCaptureDevice.default(for: .video), device.hasTorch else { return }
        do {
            try device.lockForConfiguration()
            isTorchOn.toggle()
            device.torchMode = isTorchOn ? .on : .off
            device.unlockForConfiguration()
        } catch {
            print("Torch error: \(error)")
        }
    }
}

// MARK: - Camera Preview with AVFoundation
struct CameraPreviewView: UIViewControllerRepresentable {
    var onCodeDetected: (String) -> Void
    var onError: (String) -> Void

    func makeUIViewController(context: Context) -> CameraViewController {
        let vc = CameraViewController()
        vc.onCodeDetected = onCodeDetected
        vc.onError = onError
        return vc
    }

    func updateUIViewController(_ uiViewController: CameraViewController, context: Context) {}
}

class CameraViewController: UIViewController, AVCaptureMetadataOutputObjectsDelegate {
    var onCodeDetected: ((String) -> Void)?
    var onError: ((String) -> Void)?

    private var captureSession: AVCaptureSession?
    private var previewLayer: AVCaptureVideoPreviewLayer?
    private var hasDetected = false

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .black
        setupCamera()
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        previewLayer?.frame = view.bounds
    }

    override func viewWillAppear(_ animated: Bool) {
        super.viewWillAppear(animated)
        if captureSession?.isRunning == false {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession?.startRunning()
            }
        }
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        if captureSession?.isRunning == true {
            captureSession?.stopRunning()
        }
    }

    private func setupCamera() {
        let status = AVCaptureDevice.authorizationStatus(for: .video)
        switch status {
        case .authorized:
            initCaptureSession()
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
                DispatchQueue.main.async {
                    if granted {
                        self?.initCaptureSession()
                    } else {
                        self?.onError?("Cần cấp quyền truy cập Camera trong Cài đặt để quét mã QR")
                    }
                }
            }
        case .denied, .restricted:
            onError?("Cần cấp quyền truy cập Camera trong Cài đặt để quét mã QR")
        @unknown default:
            break
        }
    }

    private func initCaptureSession() {
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            guard let self = self else { return }
            let session = AVCaptureSession()

            guard let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
                  let input = try? AVCaptureDeviceInput(device: device),
                  session.canAddInput(input) else {
                DispatchQueue.main.async {
                    self.onError?("Không thể khởi động Camera trên thiết bị này")
                }
                return
            }

            session.addInput(input)

            let metadataOutput = AVCaptureMetadataOutput()
            if session.canAddOutput(metadataOutput) {
                session.addOutput(metadataOutput)
                metadataOutput.setMetadataObjectsDelegate(self, queue: DispatchQueue.main)
                metadataOutput.metadataObjectTypes = [.qr]
            } else {
                DispatchQueue.main.async {
                    self.onError?("Không thể quét mã QR")
                }
                return
            }

            self.captureSession = session

            DispatchQueue.main.async {
                let preview = AVCaptureVideoPreviewLayer(session: session)
                preview.videoGravity = .resizeAspectFill
                preview.frame = self.view.bounds
                self.view.layer.addSublayer(preview)
                self.previewLayer = preview
            }

            session.startRunning()
        }
    }

    func metadataOutput(_ output: AVCaptureMetadataOutput, didOutput metadataObjects: [AVMetadataObject], from connection: AVCaptureConnection) {
        guard !hasDetected,
              let metadataObj = metadataObjects.first as? AVMetadataMachineReadableCodeObject,
              metadataObj.type == .qr,
              let stringValue = metadataObj.stringValue else {
            return
        }

        hasDetected = true
        captureSession?.stopRunning()
        onCodeDetected?(stringValue)
    }
}
