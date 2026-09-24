from llama_index.llms.google_genai import GoogleGenAI

from my_ai_agent.agents.common import build_agent, build_tools, make_responder
from my_ai_agent.settings import settings

llm = GoogleGenAI(model=settings.gemini_model, api_key=settings.require("google_api_key"))
tools = build_tools()

# Gemini supports native tool calling, so no text format has to be parsed.
agent = build_agent(llm, tools, native_tool_calling=True)
generateResponse = make_responder(agent)
