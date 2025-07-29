from llama_index.core.tools import FunctionTool
from Functions.open_url import open_web_url


class BasicTools:
    def __init__(self):
        self.tools = []

        add_tool = FunctionTool.from_defaults(
            fn=self.add,
            description="""Add two numbers and returns the result as float.""",
        )
        multiply_tool = FunctionTool.from_defaults(
            fn=self.multiply,
            description="""Multiply two numbers and returns the result as float.""",
        )
        quotient_tool = FunctionTool.from_defaults(
            fn=self.quotient,
            description="""Divides two numbers and returns the quotient as result(float).""",
        )
        remainder_tool = FunctionTool.from_defaults(
            fn=self.remainder,
            description="""Divides two numbers and returns the remainder or modulus as result(float).""",
        )
        power_tool = FunctionTool.from_defaults(
            fn=self.power,
            description="""a raised to the power of b or a^b and returns the result as float""",
        )
        open_url_tool = FunctionTool.from_defaults(
            fn=self.open_url,
            description="""Opens a known website (e.g., 'youtube', 'leetcode') in the user's browser using the site_name string.""",
        )

        self.tools += [
            add_tool,
            multiply_tool,
            quotient_tool,
            remainder_tool,
            power_tool,
            open_url_tool,
        ]

    def add(self, a: float, b: float) -> float:
        return a + b

    def multiply(self, a: float, b: float) -> float:

        return a * b

    def substract(self, a: float, b: float) -> float:
        return a - b

    def quotient(self, a: float, b: float) -> float:
        return a / b

    def remainder(self, a: float, b: float) -> float:
        return a % b

    def power(self, a: float, b: int) -> float:
        return pow(a, b)

    def open_url(self, site_name: str) -> str:
        try:
            url = open_web_url(site_name)
            return f"✅ Successfully opened {site_name} at {url}"
        except Exception as e:
            return f"❌ Failed to open {site_name}. Error: {str(e)}"
