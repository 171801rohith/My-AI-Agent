from llama_index.llms.google_genai import GoogleGenAI

from Agents.common import build_agent, build_tools, make_responder
from config.settings import settings

llm = GoogleGenAI(model=settings.gemini_model, api_key=settings.require("google_api_key"))
tools = build_tools()

# Gemini supports native tool calling, so no text format has to be parsed.
agent = build_agent(llm, tools, native_tool_calling=True)
generateResponse = make_responder(agent)
