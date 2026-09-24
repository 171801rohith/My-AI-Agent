from llama_index.llms.google_genai import GoogleGenAI
from dotenv import load_dotenv

from Agents.common import build_agent, build_tools, make_responder

load_dotenv()

llm = GoogleGenAI(model="gemini-2.5-flash")
tools = build_tools()

# Gemini supports native tool calling, so no text format has to be parsed.
agent = build_agent(llm, tools, native_tool_calling=True)
generateResponse = make_responder(agent)
