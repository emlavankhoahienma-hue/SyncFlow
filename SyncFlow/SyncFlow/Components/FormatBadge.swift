import SwiftUI

struct FormatBadge: View {
    let text: String
    var isAccent: Bool = true

    var body: some View {
        Text(text)
            .font(DS.Font.mono(11))
            .fontWeight(.semibold)
            .foregroundColor(isAccent ? DS.Color.primary : DS.Color.textMuted)
            .padding(.horizontal, DS.Spacing.sm.rawValue)
            .padding(.vertical, DS.Spacing.xs.rawValue)
            .background(DS.Color.surfaceHigh)
            .cornerRadius(DS.Radius.iconBlock.rawValue)
    }
}
