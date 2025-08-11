"""
Simple Calculator Example
"""

class Calculator:
    """A basic calculator class"""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers"""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a"""
        result = a - b
        self.history.append(f"{a} - {b} = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers"""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"{a} / {b} = {result}")
        return result
    
    def get_history(self) -> list:
        """Get calculation history"""
        return self.history.copy()
    
    def clear_history(self):
        """Clear calculation history"""
        self.history.clear()

def calculate_area(length: float, width: float) -> float:
    """Calculate area of rectangle"""
    return length * width

def calculate_interest(principal: float, rate: float, time: float) -> float:
    """Calculate simple interest"""
    return (principal * rate * time) / 100

if __name__ == "__main__":
    calc = Calculator()
    print(calc.add(10, 5))
    print(calc.multiply(3, 4))
    print(calc.get_history())
