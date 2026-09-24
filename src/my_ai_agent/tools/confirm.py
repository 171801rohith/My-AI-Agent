import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()
logger = logging.getLogger(__name__)


def ask_user(title: str, details: str) -> bool:
    """Show the exact action the agent wants to take and wait for a y/n answer."""
    console.print(Panel(details, title=f"[bold yellow]Confirm: {title}", border_style="yellow"))
    approved = Confirm.ask("[bold yellow]Allow this action?", default=False)
    logger.info("User %s: %s", "approved" if approved else "declined", title)
    return approved


# Side-effecting tools call confirm(); tests replace it to approve or decline.
confirm = ask_user

CANCELLED = "Cancelled: the user declined this action. Do not retry it unless asked."
