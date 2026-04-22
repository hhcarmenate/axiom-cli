from rich.console import Console
from rich.theme import Theme

_theme = Theme({
    "ok": "bold green",
    "fail": "bold red",
    "warn": "bold yellow",
    "info": "bold cyan",
    "muted": "dim white",
    "cmd": "bold magenta",
})

console = Console(theme=_theme)


def ok(msg: str) -> None:
    console.print(f"[ok]✅ {msg}[/ok]")


def fail(msg: str) -> None:
    console.print(f"[fail]❌ {msg}[/fail]")


def warn(msg: str) -> None:
    console.print(f"[warn]⚠️  {msg}[/warn]")


def info(msg: str) -> None:
    console.print(f"[info]→  {msg}[/info]")


def header(title: str) -> None:
    console.rule(f"[bold]{title}[/bold]")
