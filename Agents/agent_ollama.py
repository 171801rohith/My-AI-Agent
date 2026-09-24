from llama_index.llms.ollama import Ollama

from Agents.common import build_agent, build_tools, make_responder

llm = Ollama(
    model="hermes3:8b",
    request_timeout=120.0,
    context_window=8000,
)
tools = build_tools()

# Hermes 3 supports native tool calling in Ollama, so no text format has to be parsed.
agent = build_agent(llm, tools, native_tool_calling=True)
generateResponse = make_responder(agent, token_limit=6000)
