// DesignSystem.swift — toàn app chỉ dùng token này, cấm hardcode màu/spacing rời rạc
import SwiftUI

enum DS {
    enum Color {
        static let primary     = SwiftUI.Color(red: 226/255, green: 114/255, blue: 91/255) // Terra Cotta #E2725B
        static let background  = SwiftUI.Color(red: 22/255,  green: 24/255,  blue: 29/255)  // #16181D — CẤM đen #000
        static let surface     = SwiftUI.Color(red: 28/255,  green: 30/255,  blue: 36/255)
        static let surfaceHigh = SwiftUI.Color(red: 36/255,  green: 39/255,  blue: 46/255)
        static let textPrimary = SwiftUI.Color.primary   // system (tự đổi Dark/Light)
        static let textMuted   = SwiftUI.Color.secondary
        static let success     = SwiftUI.Color(red: 88/255,  green: 186/255, blue: 137/255)
        static let warning     = SwiftUI.Color(red: 240/255, green: 180/255, blue: 90/255)
    }

    enum Spacing: CGFloat {   // CHỈ được dùng bội số của 4
        case xs = 4, sm = 8, md = 12, lg = 16, xl = 20, xxl = 24, xxxl = 32
    }

    enum Radius: CGFloat {
        case button = 10        // PrimaryButton — CẤM 15-20
        case input = 12
        case card = 16
        case iconBlock = 8      // khối icon material
    }

    enum Font {
        static func title(_ weight: SwiftUI.Font.Weight = .bold) -> SwiftUI.Font {
            .system(.title, design: .rounded).weight(weight)   // tiêu đề bắt buộc rounded
        }
        static func headline() -> SwiftUI.Font { .system(.headline, design: .rounded) }
        static func mono(_ size: CGFloat = 14) -> SwiftUI.Font {
            .system(size: size, design: .monospaced)           // số / tốc độ / dung lượng
        }
        static func body() -> SwiftUI.Font { .system(.body, design: .default) }
    }
}
