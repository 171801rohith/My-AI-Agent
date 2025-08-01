import os
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.agent.workflow import ReActAgent, AgentStream
from llama_index.core.workflow import Context
from llama_index.core import PromptTemplate
from dotenv import load_dotenv

from config.system_prompt import react_system_prompt
from Tools.basic_tools import BasicTools
from Tools.app_file_tools import AppAndFileTools

load_dotenv()

llm = GoogleGenAI(model="gemini-2.5-flash")
tools = []

basicTools = BasicTools()
tools += basicTools.tools

appFileTools = AppAndFileTools()
tools += appFileTools.tools


agent = ReActAgent(
    tools=tools,
    llm=llm,
    verbose=False,
)


agent.update_prompts({"react_header": react_system_prompt})
ctx = Context(agent)


async def generateResponse(message: str, chatMessages: list) -> str:
    stream = []
    handler = agent.run(message, ctx=ctx, chat_history=chatMessages)
    async for ev in handler.stream_events():
        if isinstance(ev, AgentStream):
            stream.append(ev.delta)
            # print(f"{ev.delta}", end=" ", flush=True)

    response = await handler
    return str(response)
