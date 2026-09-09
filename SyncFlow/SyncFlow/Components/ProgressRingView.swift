import SwiftUI

struct ProgressRingView: View {
    var progress: Double // 0.0 to 1.0
    var lineWidth: CGFloat = 8
    var size: CGFloat = 72
    var showPercentText: Bool = true

    var body: some View {
        ZStack {
            // Background Ring
            Circle()
                .stroke(DS.Color.surfaceHigh, lineWidth: lineWidth)
                .frame(width: size, height: size)

            // Progress Ring
            Circle()
                .trim(from: 0.0, to: CGFloat(min(max(progress, 0.0), 1.0)))
                .stroke(
                    DS.Color.primary,
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(Angle(degrees: -90))
                .frame(width: size, height: size)
                .animation(.easeInOut(duration: 0.25), value: progress)

            if showPercentText {
                Text(String(format: "%.0f%%", progress * 100))
                    .font(DS.Font.mono(14))
                    .fontWeight(.bold)
                    .foregroundColor(DS.Color.textPrimary)
            }
        }
    }
}
