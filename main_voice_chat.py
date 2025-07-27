import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

# from Agents.agent_ollama import generateResponse
from Agents.agent_gemini import generateResponse
from llama_index.core.llms import ChatMessage
from Functions.wake_word import wake_sanctuary
from Functions.play_audio import play_audio_and_print_response, play_intro
from Functions.speech_to_text import speech_to_text, record_audio

console = Console()

output_dir = "output_audios"
input_dir = "input_audios"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(input_dir, exist_ok=True)

messages = []


def check_for_termination(words: list) -> bool:
    if "chat" in words:
        i = words.index("chat")
        if i >= 1 and words[i - 1] in ["exit", "quit"]:
            return True
    return False


async def main_loop():
    console.print(
        Panel(
            Text(
                "⚔️  Say wake up SANCTUARY!",
                justify="center",
                style="italic bright_magenta",
            ),
            title="[bold white] My AI Agent",
            border_style="white",
            expand=True,
        )
    )
    if wake_sanctuary():
        await play_intro()
        console.print(
            f"[bold white]Press and hold 'SPACE' to start recording 🎙️[/bold white]"
        )
        console.print(
            f"[italic grey]Say 'quit chat' or 'exit chat' to Terminate Sanctuary [/italic grey]"
        )
        while True:
            prompt = ""
            if record_audio(console):
                prompt = speech_to_text()
            else:
                continue
            
            if check_for_termination(prompt.lower().split(" ")):
                break
                
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
                    title="[yellow]You",
                    border_style="yellow",
                    expand=True,
                    title_align="left",
                )
            )
            try:
                await play_audio_and_print_response(
                    response_text=response_text, console=console
                )
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e}")
                continue


if __name__ == "__main__":
    asyncio.run(main_loop())
