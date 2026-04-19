from rich.console import Console
from rich.pretty import Pretty
from rich.panel import Panel
from rich.traceback import install as install_rich_tracebacks

install_rich_tracebacks()
console = Console()

DEBUG = True

def debug(title, obj=None):
    if not DEBUG:
        return

    if obj is None:
        console.print(f"[bold cyan]{title}[/bold cyan]")
    else:
        console.print(
            Panel(
                Pretty(obj, expand_all=True),
                title=title,
                expand=False
            )
        )
