from llama_index.core.agent.react.formatter import ReActChatFormatter
from llama_index.core.agent.workflow import FunctionAgent, ReActAgent
from llama_index.core.memory import ChatMemoryBuffer

from config.system_prompt import persona_prompt
from Tools.basic_tools import BasicTools
from Tools.app_file_tools import AppAndFileTools
from Tools.google_tools import GoogleTools


def build_tools() -> list:
    return BasicTools().tools + AppAndFileTools().tools + GoogleTools().tools


def build_agent(llm, tools: list, native_tool_calling: bool):
    """FunctionAgent for models with native tool calling (Gemini);
    ReActAgent for local models that can only follow a text format."""
    if native_tool_calling:
        return FunctionAgent(tools=tools, llm=llm, system_prompt=persona_prompt, verbose=False)
    # system_prompt= alone is dropped by the default ReAct header, which has no
    # {context} slot; from_defaults(context=...) selects the header that has one.
    formatter = ReActChatFormatter.from_defaults(context=persona_prompt)
    return ReActAgent(tools=tools, llm=llm, formatter=formatter, verbose=False)


def make_responder(agent, token_limit: int = 30000):
    """Return generateResponse(message) backed by a single, token-limited memory."""
    # The single source of conversation history, including tool calls.
    memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)

    async def generateResponse(message: str) -> str:
        response = await agent.run(user_msg=message, memory=memory)
        return str(response)

    return generateResponse
