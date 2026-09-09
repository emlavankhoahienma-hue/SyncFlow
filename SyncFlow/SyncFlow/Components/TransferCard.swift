import SwiftUI

struct TransferCard: View {
    let fileName: String
    let progress: Double
    let speedText: String
    let etaText: String
    let bytesText: String
    let statusText: String
    var isTransferring: Bool = true
    var onCancel: (() -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: DS.Spacing.md.rawValue) {
            // Header Row
            HStack {
                Text("TRUYỀN TẢI HIỆN TẠI")
                    .font(DS.Font.mono(12))
                    .fontWeight(.bold)
                    .foregroundColor(DS.Color.textMuted)

                Spacer()

                HStack(spacing: DS.Spacing.xs.rawValue) {
                    Circle()
                        .fill(isTransferring ? DS.Color.primary : DS.Color.success)
                        .frame(width: 8, height: 8)
                    Text(statusText)
                        .font(DS.Font.mono(12))
                        .foregroundColor(isTransferring ? DS.Color.primary : DS.Color.success)
                }
            }

            // Main Content Row
            HStack(spacing: DS.Spacing.lg.rawValue) {
                ProgressRingView(progress: progress, size: 60, lineWidth: 6)

                VStack(alignment: .leading, spacing: DS.Spacing.xs.rawValue) {
                    Text(fileName)
                        .font(DS.Font.headline())
                        .foregroundColor(DS.Color.textPrimary)
                        .lineLimit(1)
                        .truncationMode(.middle)

                    Text(bytesText)
                        .font(DS.Font.mono(13))
                        .foregroundColor(DS.Color.textMuted)

                    HStack(spacing: DS.Spacing.md.rawValue) {
                        Text(speedText)
                            .font(DS.Font.mono(13))
                            .fontWeight(.medium)
                            .foregroundColor(DS.Color.primary)

                        if !etaText.isEmpty {
                            Text(etaText)
                                .font(DS.Font.mono(12))
                                .foregroundColor(DS.Color.textMuted)
                        }
                    }
                }

                Spacer()

                if let onCancel = onCancel, isTransferring {
                    Button(action: onCancel) {
                        ZStack {
                            RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                                .fill(.ultraThinMaterial)
                                .frame(width: 32, height: 32)
                            Image(systemName: "xmark")
                                .font(.system(size: 13, weight: .bold))
                                .foregroundColor(DS.Color.textMuted)
                        }
                    }
                }
            }
        }
        .padding(DS.Spacing.xl.rawValue)
        .background(DS.Color.surface)
        .cornerRadius(DS.Radius.card.rawValue)
        // Design System Rule: TransferCard is the ONLY element allowed to have a shadow
        .shadow(color: SwiftUI.Color.black.opacity(0.20), radius: 16, x: 0, y: 6)
    }
}
