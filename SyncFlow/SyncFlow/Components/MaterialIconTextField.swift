import SwiftUI

struct MaterialIconTextField: View {
    let systemIcon: String
    let placeholder: String
    @Binding var text: String
    var keyboardType: UIKeyboardType = .default
    var autocapitalization: TextInputAutocapitalization = .never

    @FocusState private var isFocused: Bool

    var body: some View {
        HStack(spacing: DS.Spacing.md.rawValue) {
            // Material Icon Box (32x32, cornerRadius 8, ultraThinMaterial)
            ZStack {
                RoundedRectangle(cornerRadius: DS.Radius.iconBlock.rawValue)
                    .fill(.ultraThinMaterial)
                    .frame(width: 32, height: 32)
                
                Image(systemName: systemIcon)
                    .font(.system(size: 15, weight: .medium))
                    .foregroundColor(DS.Color.primary)
            }

            // Text Input Field with 0.5px border and focus ring
            ZStack(alignment: .leading) {
                if text.isEmpty {
                    Text(placeholder)
                        .font(DS.Font.body())
                        .foregroundColor(DS.Color.textMuted)
                        .padding(.horizontal, DS.Spacing.md.rawValue)
                }

                TextField("", text: $text)
                    .font(DS.Font.body())
                    .foregroundColor(DS.Color.textPrimary)
                    .keyboardType(keyboardType)
                    .textInputAutocapitalization(autocapitalization)
                    .focused($isFocused)
                    .padding(.horizontal, DS.Spacing.md.rawValue)
                    .padding(.vertical, DS.Spacing.sm.rawValue + 2)
            }
            .frame(height: 44)
            .background(DS.Color.surface)
            .cornerRadius(DS.Radius.input.rawValue)
            .overlay(
                RoundedRectangle(cornerRadius: DS.Radius.input.rawValue)
                    .strokeBorder(
                        isFocused ? DS.Color.primary.opacity(0.6) : DS.Color.textPrimary.opacity(0.2),
                        lineWidth: 0.5
                    )
            )
        }
    }
}
