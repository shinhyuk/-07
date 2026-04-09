import SwiftUI

@main
struct iPhoneCalculatorApp: App {
    var body: some Scene {
        WindowGroup {
            CalculatorView()
                .preferredColorScheme(.dark)
        }
    }
}
