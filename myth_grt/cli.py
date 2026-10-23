"""Terminal interface for Myth GRT."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from . import __version__
from .chronicle import to_markdown
from .engine import TurnResult, take_turn
from .mind import ClaudeMind, Mind, OfflineMind
from .world import ELEMENTS, GENRES, PHENOMENA, World, load_world, save_world

DEFAULT_WORLD = Path("worlds/primordia.json")

GENRE_COLORS = {
    "Comedy": "bright_yellow",
    "Drama": "magenta",
    "Action": "red",
    "Mystery": "medium_purple",
    "Horror": "#e05252",
    "Romance": "pink1",
    "Epic Fantasy": "gold1",
    "Sci-Fi": "cyan",
}
ALIGNMENT_COLORS = {
    "Harmonious": "green",
    "Neutral": "white",
    "Bittersweet": "plum2",
    "Turbulent": "orange1",
    "Chaotic": "red",
}

_LETTERS = {
    "M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
    "Y": ["██╗   ██╗", "╚██╗ ██╔╝", " ╚████╔╝ ", "  ╚██╔╝  ", "   ██║   ", "   ╚═╝   "],
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "G": [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    " ": ["   "] * 6,
}


def _block_text(word: str) -> list[str]:
    return ["".join(_LETTERS[ch][row] for ch in word) for row in range(6)]


_BANNER_LINES = _block_text("MYTH GRT") + ["", "speak, and the world becomes"]
# Pad every line to the same width so centering keeps the letters aligned.
_WIDTH = max(len(line) for line in _BANNER_LINES)
BANNER = "\n".join(line.center(_WIDTH) if line.islower() else line.ljust(_WIDTH) for line in _BANNER_LINES)


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def vitality_bar(vitality: int, width: int = 20) -> Text:
    filled = round(vitality / 100 * width)
    color = "green" if vitality > 60 else "yellow" if vitality > 25 else "red"
    bar = Text("█" * filled, style=color)
    bar.append("░" * (width - filled), style="grey35")
    bar.append(f"  {vitality}/100", style="bold")
    return bar


def status_panel(world: World) -> Panel:
    accent = GENRE_COLORS.get(world.genre, "white")
    table = Table.grid(padding=(0, 2))
    table.add_column(style="grey62", justify="right")
    table.add_column()
    table.add_row("Year", Text(str(world.age_in_years), style="bold"))
    table.add_row("Maturity", Text(world.maturity, style="bold"))
    table.add_row("Vitality", vitality_bar(world.vitality))
    table.add_row("Spirit", Text(world.alignment, style=ALIGNMENT_COLORS.get(world.alignment, "white")))
    table.add_row("Mood", Text(world.mood, style="italic"))
    nature = " · ".join(world.elements + world.phenomena)
    table.add_row("Nature", Text(nature, style=accent))
    if world.lineages:
        table.add_row("Peoples", ", ".join(l.name for l in world.lineages))
    if world.landmarks:
        table.add_row("Landmarks", ", ".join(world.landmarks[-4:]))
    return Panel(
        table,
        title=f"[bold {accent}]{world.name}[/]  [grey62]{world.genre}[/]",
        border_style=accent,
        padding=(1, 2),
    )


def turn_panel(world: World, result: TurnResult) -> Panel:
    accent = GENRE_COLORS.get(world.genre, "white")
    body: list = [Text(result.narration.narration, style="bright_white")]
    if result.report.events:
        events = Text()
        for event in result.report.events:
            events.append("✦ ", style=accent)
            events.append(event + "\n", style="grey70")
        body += [Text(""), events]
    if result.narration.omen:
        body.append(Text(f"Omen: {result.narration.omen}", style=f"italic {accent}"))
    if result.note:
        body += [Text(""), Text(result.note, style="yellow")]
    change = result.report.vitality_change
    sign = "+" if change > 0 else ""
    subtitle = f"[grey62]vitality {sign}{change} · {result.report.alignment} · narrated by {result.narration.source}[/]"
    return Panel(
        Group(*body),
        title=f"[bold {accent}]Year {result.report.year}[/]",
        subtitle=subtitle,
        border_style=accent,
        padding=(1, 2),
    )


# ---------------------------------------------------------------------------
# Genesis
# ---------------------------------------------------------------------------

def _choose(console: Console, label: str, options: list[str], exclude: set[str] = frozenset()) -> str:
    choices = [o for o in options if o not in exclude]
    for i, option in enumerate(choices, start=1):
        console.print(f"  [bold]{i}[/]. {option}")
    index = IntPrompt.ask(label, choices=[str(i) for i in range(1, len(choices) + 1)], show_choices=False)
    return choices[index - 1]


def genesis(console: Console) -> World:
    console.print(Panel("Before it breathes, shape its Sacred Genesis.", title="The world stirs in the void"))
    console.print("\n[bold]Choose a genre[/]")
    genre = _choose(console, "Genre", GENRES)
    console.print("\n[bold]Choose two Sacred Elements[/]")
    first = _choose(console, "First element", ELEMENTS)
    second = _choose(console, "Second element", ELEMENTS, exclude={first})
    console.print("\n[bold]Seed up to two Phenomena[/] (0 to finish)")
    phenomena: list[str] = []
    while len(phenomena) < 2:
        remaining = [p for p in PHENOMENA if p not in phenomena]
        for i, option in enumerate(remaining, start=1):
            console.print(f"  [bold]{i}[/]. {option}")
        pick = IntPrompt.ask("Phenomenon", choices=[str(i) for i in range(0, len(remaining) + 1)], show_choices=False)
        if pick == 0:
            break
        phenomena.append(remaining[pick - 1])
    name = Prompt.ask("\nName your world", default="Primordia").strip() or "Primordia"
    world = World(genre=genre, elements=[first, second], phenomena=phenomena, name=name)
    console.print(f"\n[bold]{name}[/] begins to breathe.\n")
    return world


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def make_mind(offline: bool, console: Console) -> Mind:
    if offline:
        return OfflineMind()
    try:
        return ClaudeMind()
    except Exception as err:  # missing SDK credentials, bad config, etc.
        console.print(f"[yellow]Claude isn't available ({err}). Playing with offline narration.[/]")
        return OfflineMind()


def play(args: argparse.Namespace, console: Console) -> int:
    path = Path(args.world)
    world = load_world(path)
    if world is None or args.new:
        if world is not None and not Confirm.ask(f"Overwrite the world saved at {path}?", default=False):
            return 1
        world = genesis(console)
        save_world(world, path)

    mind = make_mind(args.offline, console)
    console.print(Align.center(Text(BANNER, style=GENRE_COLORS.get(world.genre, "white"))))
    console.print(status_panel(world))
    console.print("[grey62]Speak a breath to shape the world. Commands: /status  /chronicle  /help  /exit[/]\n")

    while True:
        try:
            breath = Prompt.ask(f"[bold {GENRE_COLORS.get(world.genre, 'white')}]breath[/]").strip()
        except (EOFError, KeyboardInterrupt):
            breath = "/exit"
        if not breath:
            continue
        if breath in {"/exit", "/quit"}:
            console.print(f"\n{world.name} sleeps, awaiting your return.\n")
            return 0
        if breath == "/status":
            console.print(status_panel(world))
            continue
        if breath == "/chronicle":
            out = path.with_suffix(".md")
            out.write_text(to_markdown(world), encoding="utf-8")
            console.print(f"Chronicle written to [bold]{out}[/]")
            continue
        if breath == "/help":
            console.print("Type any sentence of intent: [italic]plant a garden of light by the river[/].")
            continue

        with console.status("The world is listening..."):
            result = take_turn(world, breath, mind)
        save_world(world, path)
        console.print(turn_panel(world, result))


def status(args: argparse.Namespace, console: Console) -> int:
    world = load_world(Path(args.world))
    if world is None:
        console.print("No world yet. Run [bold]myth-grt play[/] to create one.")
        return 1
    console.print(status_panel(world))
    return 0


def chronicle(args: argparse.Namespace, console: Console) -> int:
    world = load_world(Path(args.world))
    if world is None:
        console.print("No world yet. Run [bold]myth-grt play[/] to create one.")
        return 1
    markdown = to_markdown(world)
    if args.out:
        Path(args.out).write_text(markdown, encoding="utf-8")
        console.print(f"Chronicle written to [bold]{args.out}[/]")
    else:
        console.print(markdown)
    return 0


def demo(args: argparse.Namespace, console: Console) -> int:
    """Play a scripted session non-interactively (used for docs and screenshots)."""
    world = World(genre=args.genre, elements=args.elements, phenomena=args.phenomena or [], name=args.name)
    mind = make_mind(args.offline, console)
    console.print(Align.center(Text(BANNER, style=GENRE_COLORS.get(world.genre, "white"))))
    for breath in args.breaths:
        console.print(Rule(style="grey35"))
        console.print(Text(f"breath › {breath}", style=f"bold {GENRE_COLORS.get(world.genre, 'white')}"))
        result = take_turn(world, breath, mind)
        console.print(turn_panel(world, result))
    console.print(status_panel(world))
    if args.save:
        save_world(world, Path(args.save))
    if args.svg:
        console.save_svg(args.svg, title=f"Myth GRT · {world.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="myth-grt", description="Speak, and the world becomes.")
    parser.add_argument("--version", action="version", version=f"myth-grt {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_play = sub.add_parser("play", help="play (creates a world on first run)")
    p_play.add_argument("--world", default=str(DEFAULT_WORLD), help="path to the world save file")
    p_play.add_argument("--new", action="store_true", help="start a new world")
    p_play.add_argument("--offline", action="store_true", help="narrate without calling Claude")

    p_status = sub.add_parser("status", help="show a world's current state")
    p_status.add_argument("--world", default=str(DEFAULT_WORLD))

    p_chron = sub.add_parser("chronicle", help="export a world's history as Markdown")
    p_chron.add_argument("--world", default=str(DEFAULT_WORLD))
    p_chron.add_argument("--out", help="write to a file instead of the terminal")

    p_demo = sub.add_parser("demo", help="play a scripted session")
    p_demo.add_argument("--genre", default="Epic Fantasy", choices=GENRES)
    p_demo.add_argument("--elements", nargs=2, default=["Light", "Water"], choices=ELEMENTS)
    p_demo.add_argument("--phenomena", nargs="*", choices=PHENOMENA)
    p_demo.add_argument("--name", default="Primordia")
    p_demo.add_argument("--offline", action="store_true")
    p_demo.add_argument("--svg", help="save the session as an SVG screenshot")
    p_demo.add_argument("--save", help="save the resulting world to this path")
    p_demo.add_argument("breaths", nargs="+", help="breaths to speak, in order")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    args = build_parser().parse_args(argv)
    console = Console(record=getattr(args, "svg", None) is not None)
    if args.command is None:
        args = build_parser().parse_args(["play", *(argv or [])])
    handlers = {"play": play, "status": status, "chronicle": chronicle, "demo": demo}
    return handlers[args.command](args, console)


if __name__ == "__main__":
    sys.exit(main())
