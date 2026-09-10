import Foundation
import CryptoKit

/// Zero-Secret End-to-End Encryption (E2EE) Manager using Apple CryptoKit.
/// Uses ephemeral Curve25519 ECDH key agreement + HKDF-SHA256 + AES-256-GCM.
/// Zero keys or secrets are ever stored in Git, disk, or UserDefaults.
public class CryptoManager {
    public static let shared = CryptoManager()

    private let hkdfSalt = "SyncFlow-E2EE-v1".data(using: .utf8)!
    private let hkdfInfo = "syncflow-file-transfer".data(using: .utf8)!

    private var privateKey: Curve25519.KeyAgreement.PrivateKey
    private var sessionKey: SymmetricKey?

    public private(set) var sessionID: String?
    public private(set) var isE2EEActive: Bool = false

    private init() {
        // Generate fresh ephemeral Curve25519 keypair in RAM
        self.privateKey = Curve25519.KeyAgreement.PrivateKey()
    }

    /// Reset keypair and session on disconnect
    public func resetSession() {
        self.privateKey = Curve25519.KeyAgreement.PrivateKey()
        self.sessionKey = nil
        self.sessionID = nil
        self.isE2EEActive = false
    }

    /// Returns the raw 32-byte public key encoded in Base64
    public var publicKeyBase64: String {
        return privateKey.publicKey.rawRepresentation.base64EncodedString()
    }

    /// Performs ECDH handshake guarded by PC screen PIN or QR Pairing Token.
    /// If expectedFingerprint is supplied (from QR code), verifies server ephemeral public key to prevent rogue MITM servers.
    public func performHandshake(serverURL: URL, pin: String? = nil, pairingToken: String? = nil, expectedFingerprint: String? = nil) async throws {
        let handshakeURL = serverURL.appendingPathComponent("auth/handshake")
        var request = URLRequest(url: handshakeURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 6.0

        let timestamp = Int(Date().timeIntervalSince1970)
        let nonce = UUID().uuidString

        var payload: [String: Any] = [
            "client_public_key": publicKeyBase64,
            "timestamp": timestamp,
            "nonce": nonce
        ]
        if let p = pin, !p.isEmpty {
            payload["pin"] = p
        }
        if let t = pairingToken, !t.isEmpty {
            payload["pairing_token"] = t
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: payload)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse else {
            throw NSError(domain: "CryptoManager", code: 500, userInfo: [NSLocalizedDescriptionKey: "Không có phản hồi từ máy chủ"])
        }

        if httpResponse.statusCode != 200 {
            var errorMsg = "Xác thực handshake thất bại: HTTP \(httpResponse.statusCode)"
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let detail = json["detail"] as? String {
                errorMsg = detail
            }
            throw NSError(domain: "CryptoManager", code: httpResponse.statusCode, userInfo: [NSLocalizedDescriptionKey: errorMsg])
        }

        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let serverKeyB64 = json["server_public_key"] as? String,
              let serverKeyData = Data(base64Encoded: serverKeyB64) else {
            throw NSError(domain: "CryptoManager", code: 500, userInfo: [NSLocalizedDescriptionKey: "Phản hồi handshake không hợp lệ"])
        }

        // Anti-MITM: Verify server public key fingerprint if provided by QR code
        if let expFp = expectedFingerprint, !expFp.isEmpty {
            let digest = SHA256.hash(data: serverKeyData)
            let hex = digest.map { String(format: "%02x", $0) }.joined()
            let computedFp = String(hex.prefix(8))
            if computedFp.lowercased() != expFp.lowercased() {
                throw NSError(
                    domain: "CryptoManager",
                    code: 403,
                    userInfo: [NSLocalizedDescriptionKey: "Cảnh báo MITM / Rogue Server! Khóa công khai máy chủ (\(computedFp)) không khớp với mã QR (\(expFp))."]
                )
            }
        }

        self.sessionID = json["session_id"] as? String

        // Import server public key
        let serverPublicKey = try Curve25519.KeyAgreement.PublicKey(rawRepresentation: serverKeyData)

        // Perform ECDH Key Agreement
        let sharedSecret = try privateKey.sharedSecretFromKeyAgreement(with: serverPublicKey)

        // HKDF-SHA256 Session Key Derivation (AES-256 = 32 bytes)
        let derivedKey = sharedSecret.hkdfDerivedSymmetricKey(
            using: SHA256.self,
            salt: hkdfSalt,
            sharedInfo: hkdfInfo,
            outputByteCount: 32
        )

        self.sessionKey = derivedKey
        self.isE2EEActive = true
    }

    /// Encrypts a chunk of data with AES-256-GCM.
    /// Wire format: [12 bytes Nonce] + [Ciphertext] + [16 bytes Tag] (CryptoKit combined format)
    public func encryptChunk(_ data: Data) throws -> Data {
        guard isE2EEActive, let key = sessionKey else {
            return data
        }

        let sealedBox = try AES.GCM.seal(data, using: key)
        guard let combined = sealedBox.combined else {
            throw NSError(domain: "CryptoManager", code: 500, userInfo: [NSLocalizedDescriptionKey: "Mã hóa chunk thất bại"])
        }
        return combined
    }

    /// Decrypts an AES-256-GCM chunk.
    /// Wire format: [12 bytes Nonce] + [Ciphertext] + [16 bytes Tag]
    public func decryptChunk(_ encryptedData: Data) throws -> Data {
        guard isE2EEActive, let key = sessionKey else {
            return encryptedData
        }

        let sealedBox = try AES.GCM.SealedBox(combined: encryptedData)
        return try AES.GCM.open(sealedBox, using: key)
    }
}
