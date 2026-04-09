import Foundation

enum CalcButton: String {
    case zero = "0", one = "1", two = "2", three = "3", four = "4"
    case five = "5", six = "6", seven = "7", eight = "8", nine = "9"
    case add = "+", subtract = "−", multiply = "×", divide = "÷"
    case equals = "=", decimal = ".", negate = "+/−", percent = "%"
    case clear = "AC"
}

enum ButtonType {
    case number, operation, function_btn
}

class CalculatorViewModel: ObservableObject {
    @Published var displayValue: String = "0"
    @Published var expression: String = ""
    @Published var activeOperator: CalcButton? = nil

    private var currentInput: String = "0"
    private var previousInput: String = ""
    private var currentOperator: CalcButton? = nil
    private var shouldResetDisplay: Bool = false
    private var lastResult: Double? = nil
    private var lastOperator: CalcButton? = nil
    private var lastOperand: Double? = nil

    var clearButtonText: String {
        currentInput == "0" && currentOperator == nil ? "AC" : "C"
    }

    func buttonTapped(_ button: CalcButton) {
        switch button {
        case .zero, .one, .two, .three, .four, .five, .six, .seven, .eight, .nine:
            inputNumber(button.rawValue)
        case .decimal:
            inputDecimal()
        case .add, .subtract, .multiply, .divide:
            inputOperator(button)
        case .equals:
            calculate()
        case .clear:
            clearAll()
        case .negate:
            toggleNegate()
        case .percent:
            inputPercent()
        }
    }

    func buttonType(for button: CalcButton) -> ButtonType {
        switch button {
        case .zero, .one, .two, .three, .four, .five, .six, .seven, .eight, .nine, .decimal:
            return .number
        case .add, .subtract, .multiply, .divide, .equals:
            return .operation
        case .clear, .negate, .percent:
            return .function_btn
        }
    }

    // MARK: - Input

    private func inputNumber(_ value: String) {
        if shouldResetDisplay {
            activeOperator = nil
        }

        if shouldResetDisplay {
            currentInput = value
            shouldResetDisplay = false
        } else {
            let rawDigits = currentInput.replacingOccurrences(of: "[^0-9]", with: "", options: .regularExpression)
            if rawDigits.count >= 9 { return }

            if currentInput == "0" {
                currentInput = value
            } else {
                currentInput += value
            }
        }
        updateDisplay()
    }

    private func inputDecimal() {
        activeOperator = nil

        if shouldResetDisplay {
            currentInput = "0."
            shouldResetDisplay = false
        } else if !currentInput.contains(".") {
            currentInput += "."
        }
        updateDisplay()
    }

    private func inputOperator(_ op: CalcButton) {
        activeOperator = op

        if currentOperator != nil && !shouldResetDisplay {
            calculate()
        } else if lastResult != nil && shouldResetDisplay {
            currentInput = formatRawNumber(lastResult!)
        }

        previousInput = currentInput
        currentOperator = op
        expression = formatDisplayNumber(previousInput) + " " + op.rawValue
        shouldResetDisplay = true
        lastOperator = nil
        lastOperand = nil
        updateDisplay()
    }

    private func calculate() {
        var result: Double
        let a: Double
        let b: Double

        if let savedOp = lastOperator, currentOperator == nil, let savedOperand = lastOperand {
            a = Double(currentInput) ?? 0
            b = savedOperand
            result = compute(a, savedOp, b)
            expression = formatDisplayNumber(currentInput) + " " + savedOp.rawValue + " " + formatDisplayNumber(formatRawNumber(b)) + " ="
        } else if let op = currentOperator {
            a = Double(previousInput) ?? 0
            b = Double(currentInput) ?? 0
            lastOperator = op
            lastOperand = b
            result = compute(a, op, b)
            expression = formatDisplayNumber(previousInput) + " " + op.rawValue + " " + formatDisplayNumber(currentInput) + " ="
        } else {
            return
        }

        if result.isInfinite || result.isNaN {
            currentInput = "Error"
        } else {
            currentInput = formatRawNumber(result)
        }

        lastResult = Double(currentInput)
        currentOperator = nil
        previousInput = ""
        shouldResetDisplay = true
        activeOperator = nil
        updateDisplay()
    }

    private func compute(_ a: Double, _ op: CalcButton, _ b: Double) -> Double {
        switch op {
        case .add: return a + b
        case .subtract: return a - b
        case .multiply: return a * b
        case .divide: return b == 0 ? .infinity : a / b
        default: return b
        }
    }

    private func clearAll() {
        if currentInput == "0" && currentOperator == nil {
            previousInput = ""
            lastResult = nil
            lastOperator = nil
            lastOperand = nil
            expression = ""
        }
        currentInput = "0"
        currentOperator = nil
        shouldResetDisplay = false
        activeOperator = nil
        updateDisplay()
    }

    private func toggleNegate() {
        guard currentInput != "0" && currentInput != "Error" else { return }

        if currentInput.hasPrefix("-") {
            currentInput = String(currentInput.dropFirst())
        } else {
            currentInput = "-" + currentInput
        }
        updateDisplay()
    }

    private func inputPercent() {
        guard let num = Double(currentInput) else { return }
        let result = num / 100
        currentInput = formatRawNumber(result)
        updateDisplay()
    }

    // MARK: - Formatting

    private func updateDisplay() {
        displayValue = formatDisplayNumber(currentInput)
    }

    private func formatRawNumber(_ num: Double) -> String {
        if num == 0 { return "0" }
        if abs(num) >= 1e15 {
            return String(format: "%.5e", num)
        }

        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 10
        formatter.usesGroupingSeparator = false
        formatter.decimalSeparator = "."

        if let result = formatter.string(from: NSNumber(value: num)) {
            return result
        }
        return String(num)
    }

    private func formatDisplayNumber(_ numStr: String) -> String {
        if numStr == "Error" { return "Error" }

        if numStr.contains(".") {
            let parts = numStr.split(separator: ".", maxSplits: 1, omittingEmptySubsequences: false)
            let intPart = Double(String(parts[0])) ?? 0
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            formatter.maximumFractionDigits = 0
            let formattedInt = formatter.string(from: NSNumber(value: intPart)) ?? "0"
            if parts.count > 1 {
                return formattedInt + "." + parts[1]
            }
            return formattedInt + "."
        }

        guard let num = Double(numStr) else { return "0" }
        if !num.isFinite { return "Error" }

        if abs(num) >= 1e15 {
            return String(format: "%.5e", num)
        }

        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 10
        return formatter.string(from: NSNumber(value: num)) ?? "0"
    }
}
