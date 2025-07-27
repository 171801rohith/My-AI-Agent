from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.workflow import Context
from dotenv import load_dotenv
import os

from tools import Tools

load_dotenv()

llm = GoogleGenAI(model="models/gemini-2.0-flash")

tools = Tools()

agent = ReActAgent(
    tools=tools.tools,
    llm=llm,
    verbose=False,
    system_prompt=os.getenv("SYSTEM_PROMPT"),
)

ctx = Context(agent)


async def generateResponse(message: str, chatMessages: list) -> str:
    response = await agent.run(message, ctx=ctx, chat_history=chatMessages)
    return str(response)
