from llama_index.core.tools import FunctionTool

from my_ai_agent import memory_store


class MemoryTools:
    def __init__(self):
        self.tools = [
            FunctionTool.from_defaults(
                fn=self.remember_fact,
                description="""Save a lasting fact about the user so it is remembered in future sessions,
                    e.g. 'My brother's email is ravi@example.com' or 'I prefer short answers'.
                    Use it when the user asks you to remember something or shares a stable preference.
                    Input: fact (string, a complete self-contained sentence).""",
            ),
            FunctionTool.from_defaults(
                fn=self.forget_fact,
                description="""Forget remembered facts that contain the given text.
                    Input: text (string).""",
            ),
            FunctionTool.from_defaults(
                fn=self.list_facts,
                description="""List everything remembered about the user.""",
            ),
        ]

    def remember_fact(self, fact: str) -> str:
        if memory_store.add_fact(fact):
            return f"Remembered: {fact.strip()}"
        return "Already remembered (or empty); nothing changed."

    def forget_fact(self, text: str) -> str:
        removed = memory_store.remove_facts(text)
        if not removed:
            return f"No remembered fact contains '{text}'."
        return "Forgot: " + "; ".join(removed)

    def list_facts(self) -> str:
        facts = memory_store.load_facts()
        if not facts:
            return "Nothing has been remembered yet."
        return "\n".join(f"- {f}" for f in facts)
