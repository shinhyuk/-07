import SwiftUI

struct CalculatorView: View {
    @StateObject private var viewModel = CalculatorViewModel()

    let buttons: [[CalcButton]] = [
        [.clear, .negate, .percent, .divide],
        [.seven, .eight, .nine, .multiply],
        [.four, .five, .six, .subtract],
        [.one, .two, .three, .add],
        [.zero, .decimal, .equals]
    ]

    var body: some View {
        GeometryReader { geometry in
            let spacing: CGFloat = 12
            let totalSpacing = spacing * 5 // 4 gaps + 2 side paddings
            let buttonSize = (geometry.size.width - totalSpacing) / 4

            VStack(spacing: 0) {
                Spacer()

                // Display
                VStack(alignment: .trailing, spacing: 4) {
                    Text(viewModel.expression)
                        .font(.system(size: 20))
                        .foregroundColor(.gray)
                        .lineLimit(1)
                        .minimumScaleFactor(0.5)

                    Text(viewModel.displayValue)
                        .font(.system(size: displayFontSize(for: viewModel.displayValue), weight: .light))
                        .foregroundColor(.white)
                        .lineLimit(1)
                        .minimumScaleFactor(0.4)
                }
                .frame(maxWidth: .infinity, alignment: .trailing)
                .padding(.horizontal, 24)
                .padding(.bottom, 12)

                // Buttons
                VStack(spacing: spacing) {
                    ForEach(buttons.indices, id: \.self) { rowIndex in
                        HStack(spacing: spacing) {
                            ForEach(buttons[rowIndex], id: \.rawValue) { button in
                                CalculatorButtonView(
                                    button: button,
                                    viewModel: viewModel,
                                    size: buttonSize,
                                    spacing: spacing
                                )
                            }
                        }
                    }
                }
                .padding(.horizontal, spacing)
                .padding(.bottom, spacing)
            }
        }
        .background(Color.black)
        .ignoresSafeArea()
    }

    private func displayFontSize(for text: String) -> CGFloat {
        if text.count > 12 { return 40 }
        if text.count > 8 { return 56 }
        return 80
    }
}

struct CalculatorButtonView: View {
    let button: CalcButton
    let viewModel: CalculatorViewModel
    let size: CGFloat
    let spacing: CGFloat

    @State private var isPressed = false

    private var isWideButton: Bool {
        button == .zero
    }

    private var isActiveOperator: Bool {
        viewModel.activeOperator == button
    }

    private var backgroundColor: Color {
        let type = viewModel.buttonType(for: button)
        if type == .operation {
            return isActiveOperator ? .white : .orange
        } else if type == .function_btn {
            return Color(white: 0.65)
        } else {
            return Color(white: 0.2)
        }
    }

    private var foregroundColor: Color {
        let type = viewModel.buttonType(for: button)
        if type == .operation {
            return isActiveOperator ? .orange : .white
        } else if type == .function_btn {
            return .black
        } else {
            return .white
        }
    }

    private var buttonLabel: String {
        if button == .clear {
            return viewModel.clearButtonText
        }
        return button.rawValue
    }

    var body: some View {
        Button(action: {
            viewModel.buttonTapped(button)
        }) {
            Text(buttonLabel)
                .font(.system(size: isWideButton ? 32 : (viewModel.buttonType(for: button) == .function_btn ? 28 : 32)))
                .fontWeight(viewModel.buttonType(for: button) == .operation ? .medium : .regular)
                .frame(
                    width: isWideButton ? size * 2 + spacing : size,
                    height: size
                )
                .background(backgroundColor)
                .foregroundColor(foregroundColor)
                .clipShape(isWideButton ? AnyShape(Capsule()) : AnyShape(Circle()))
        }
        .buttonStyle(CalculatorButtonStyle())
    }
}

struct CalculatorButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .brightness(configuration.isPressed ? 0.3 : 0)
            .animation(.easeOut(duration: 0.1), value: configuration.isPressed)
    }
}

// AnyShape for iOS 15 compatibility
struct AnyShape: Shape {
    private let pathBuilder: (CGRect) -> Path

    init<S: Shape>(_ shape: S) {
        pathBuilder = { rect in
            shape.path(in: rect)
        }
    }

    func path(in rect: CGRect) -> Path {
        pathBuilder(rect)
    }
}

#Preview {
    CalculatorView()
        .preferredColorScheme(.dark)
}
