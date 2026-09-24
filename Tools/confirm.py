from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


def ask_user(title: str, details: str) -> bool:
    """Show the exact action the agent wants to take and wait for a y/n answer."""
    console.print(Panel(details, title=f"[bold yellow]Confirm: {title}", border_style="yellow"))
    return Confirm.ask("[bold yellow]Allow this action?", default=False)


# Side-effecting tools call confirm(); tests replace it to approve or decline.
confirm = ask_user

CANCELLED = "Cancelled: the user declined this action. Do not retry it unless asked."
