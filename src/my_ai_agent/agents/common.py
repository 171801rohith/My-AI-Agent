from llama_index.core.agent.react.formatter import ReActChatFormatter
from typing import Callable

from llama_index.core.agent.workflow import AgentStream, FunctionAgent, ReActAgent
from llama_index.core.memory import ChatMemoryBuffer

from my_ai_agent import memory_store
from my_ai_agent.persona import persona_prompt
from my_ai_agent.tools.basic_tools import BasicTools
from my_ai_agent.tools.app_file_tools import AppAndFileTools
from my_ai_agent.tools.google_tools import GoogleTools
from my_ai_agent.tools.history_tools import HistoryTools
from my_ai_agent.tools.memory_tools import MemoryTools


def build_tools() -> list:
    return (
        BasicTools().tools
        + AppAndFileTools().tools
        + GoogleTools().tools
        + HistoryTools().tools
        + MemoryTools().tools
    )


def build_agent(llm, tools: list, native_tool_calling: bool):
    """FunctionAgent for models with native tool calling (Gemini);
    ReActAgent for local models that can only follow a text format.
    Remembered facts are added to the system prompt when the agent is built."""
    system_prompt = persona_prompt + memory_store.facts_prompt()
    if native_tool_calling:
        return FunctionAgent(tools=tools, llm=llm, system_prompt=system_prompt, verbose=False)
    # system_prompt= alone is dropped by the default ReAct header, which has no
    # {context} slot; from_defaults(context=...) selects the header that has one.
    formatter = ReActChatFormatter.from_defaults(context=system_prompt)
    return ReActAgent(tools=tools, llm=llm, formatter=formatter, verbose=False)


class Responder:
    """Callable as `await respond(message)`. Holds the single, token-limited memory
    (including tool calls) and saves recent user/assistant messages after each turn."""

    def __init__(self, agent, token_limit: int = 30000):
        self.agent = agent
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)

    def resume_history(self) -> int:
        """Load the previous run's recent messages; returns how many were loaded."""
        messages = memory_store.load_history()
        self.memory.set(messages)
        return len(messages)

    async def __call__(self, message: str, on_text: Callable[[str], None] | None = None) -> str:
        """Run one turn. If on_text is given, it receives the reply text as it streams in."""
        handler = self.agent.run(user_msg=message, memory=self.memory)
        # ReAct streams its raw "Thought:/Action:" scratch text, which must not be shown or spoken.
        if on_text is not None and isinstance(self.agent, FunctionAgent):
            async for event in handler.stream_events():
                if isinstance(event, AgentStream) and event.delta:
                    on_text(event.delta)
        response = await handler
        memory_store.save_history(self.memory.get_all())
        return str(response)


def make_responder(agent, token_limit: int = 30000) -> Responder:
    return Responder(agent, token_limit)
