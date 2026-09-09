import SwiftUI

struct PrimaryButton: View {
    let title: String
    var icon: String? = nil
    var isFullWidth: Bool = true
    var isEnabled: Bool = true
    let action: () -> Void

    @State private var isPressed: Bool = false

    var body: some View {
        Button(action: {
            if isEnabled {
                action()
            }
        }) {
            HStack(spacing: DS.Spacing.sm.rawValue) {
                if let icon = icon {
                    Image(systemName: icon)
                        .font(.system(size: 16, weight: .semibold))
                }
                Text(title)
                    .font(DS.Font.headline())
                    .foregroundColor(Color.white)
            }
            .frame(maxWidth: isFullWidth ? .infinity : nil)
            .padding(.vertical, DS.Spacing.md.rawValue)
            .padding(.horizontal, DS.Spacing.lg.rawValue)
            .background(DS.Color.primary)
            .cornerRadius(DS.Radius.button.rawValue)
            .opacity(isEnabled ? 1.0 : 0.4)
            .scaleEffect(isPressed ? 0.95 : 1.0)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isPressed)
        }
        .disabled(!isEnabled)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    if isEnabled && !isPressed {
                        isPressed = true
                        let generator = UIImpactFeedbackGenerator(style: .medium)
                        generator.prepare()
                        generator.impactOccurred()
                    }
                }
                .onEnded { _ in
                    isPressed = false
                }
        )
    }
}
