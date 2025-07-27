from llama_index.core.tools import FunctionTool


class Tools:
    def __init__(self):
        self.tools = []
        for attr_name in dir(self):
            if attr_name.startswith("__"):
                continue
            attr = getattr(self, attr_name)
            if callable(attr):
                self.tools.append(FunctionTool.from_defaults(fn=attr))

    def add(self, a: float, b: float) -> float:
        """Add two numbers and returns the result as float."""
        return a + b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers and returns the result as float."""
        return a * b

    def substract(self, a: float, b: float) -> float:
        """Substract two numbers and returns the result as float."""
        return a - b

    def quotient(self, a: float, b: float) -> float:
        """Returns the Quotient of two numbers result as float."""
        return a / b

    def remainder(self, a: float, b: float) -> float:
        """Returns the Remainder or Modulus of two numbers result as float."""
        return a % b
