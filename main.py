import asyncio
import os
from llama_index.core.llms import ChatMessage
from Agents.agent_ollama import generateResponse
# from Agents.agent_gemini import generateResponse
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from Functions.wake_word import wake_sanctuary

console = Console()

output_dir = "output_audios"
input_dir = "input_audios"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(input_dir, exist_ok=True)

messages = []


async def main_loop():
    console.print(
        Panel(
            Text(
                "⚔️  Say wake up SANCTUARY!",
                justify="center",
                style="italic bright_magenta",
            ),
            title="[bold white] My AI Agent",
            border_style="cyan",
            expand=True,
        )
    )
    if wake_sanctuary():
        while True:

            prompt = Prompt.ask("[bold cyan]You")

            if prompt.strip() == "":
                continue

            messages.append({"role": "user", "content": prompt})
            chatMessages = [
                ChatMessage(role=m["role"], content=m["content"]) for m in messages
            ]

            try:
                response = await generateResponse(prompt, chatMessages)
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue

            response_text = str(response)
            messages.append({"role": "assistant", "content": response_text})

            console.print(
                Panel(
                    prompt,
                    title="[cyan]You",
                    border_style="cyan",
                    expand=True,
                    title_align="right",
                )
            )
            console.print(
                Panel(
                    response_text,
                    title="[magenta]Assistant",
                    border_style="magenta",
                    expand=True,
                    title_align="left",
                )
            )


if __name__ == "__main__":
    asyncio.run(main_loop())
