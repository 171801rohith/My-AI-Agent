import os
from llama_index.llms.google_genai import GoogleGenAI 
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.workflow import Context
from llama_index.core import PromptTemplate
from dotenv import load_dotenv

from tools import Tools

load_dotenv()

llm = GoogleGenAI(model="models/gemini-2.5-flash")

tools = Tools()
base_dir = os.path.dirname(__file__)
system_prompt_file = os.path.join(base_dir, "..", "config", "system_prompt.txt")
with open(system_prompt_file, "r") as f:
    system_prompt = f.read()


agent = ReActAgent(
    tools=tools.tools,
    llm=llm,
    verbose=False,
    system_prompt=system_prompt,
)

react_system_prompt = PromptTemplate(system_prompt)
agent.update_prompts({"react_header": react_system_prompt})
ctx = Context(agent)
ctx = Context(agent)


async def generateResponse(message: str, chatMessages: list) -> str:
    response = await agent.run(message, ctx=ctx, chat_history=chatMessages)
    return str(response)
