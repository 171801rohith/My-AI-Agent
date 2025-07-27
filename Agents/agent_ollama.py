from llama_index.llms.ollama import Ollama
from llama_index.core.agent.workflow import ReActAgent, AgentStream
from llama_index.core.workflow import Context
from dotenv import load_dotenv
import os

from tools import Tools

load_dotenv()

llm = Ollama(
    model="deepseek-r1",
    request_timeout=120.0,
    context_window=8000,
)

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
    handler = agent.run(message, ctx=ctx, chat_history=chatMessages)
    print("+" * 45)
    for ev in handler.stream_events():
        if isinstance(ev, AgentStream):
            print(f"{ev.delta}", end=" ", flush=True)
    print("+" * 45)
    response = await handler

    return str(response)
