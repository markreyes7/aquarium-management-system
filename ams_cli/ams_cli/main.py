# ams_cli/main.py
import argparse
import json
import time

from .api import (
    get_data,
    post_fertilize,
    post_trimmed,
    post_topoff,
    log_maintenance,
    list_maintenance,
)


def _build_status_table():

    # filling with dummy data for now
    from rich.table import Table

    status_table = Table(show_header=True, header_style="bold cyan")
    status_table.add_column("Metric", style="bold")
    status_table.add_column("Value")
    status_table.add_row("Water Temp", "77.4 F")
    status_table.add_row("pH", "6.8")
    status_table.add_row("Last Fertilized", "2026-03-02 08:15 PM")
    status_table.add_row("Last Trimmed", "2026-02-28 07:40 PM")
    status_table.add_row("Last Topoff", "2026-03-04 09:12 PM")
    status_table.add_row("Latest Note", "Trimmed stem plants near filter intake.")
    return status_table


def _build_reminders():
    from rich.table import Table

    reminders = Table.grid(padding=(0, 1))
    reminders.add_row("[bold yellow]Reminders[/bold yellow]")
    reminders.add_row("- Fertilize in 2 days")
    reminders.add_row("- Top off by tomorrow")
    reminders.add_row("- Check CO2 diffuser bubble rate")
    return reminders


def _aquarium_frame(frame: int):
    from rich.text import Text
    # animation is choppy needs work
    width = 53
    fish = ["><(((('>", "><(((*>", "><>"]
    positions = [
        frame % (width - len(fish[0])),
        (frame * 2 + 9) % (width - len(fish[1])),
        (frame * 3 + 3) % (width - len(fish[2])),
    ]

    water_top = "~ " * 32
    water_bottom = "~" * width
    rows = [
        " " * positions[0] + fish[0],
        " " * positions[1] + fish[1],
        " " * positions[2] + fish[2],
    ]

    aquarium_art = Text()
    aquarium_art.append(water_top[:width], style="bold cyan")
    aquarium_art.append("\n")
    aquarium_art.append(rows[0], style="blue")
    aquarium_art.append("\n")
    aquarium_art.append(rows[1], style="bright_blue")
    aquarium_art.append("\n")
    aquarium_art.append(rows[2], style="cyan")
    aquarium_art.append("\n")
    aquarium_art.append(water_bottom, style="cyan")

    return aquarium_art


def _build_demo_panel(frame: int):
    from rich.panel import Panel
    from rich.table import Table

    body = Table.grid(padding=(1, 0))
    body.add_row(_aquarium_frame(frame))
    body.add_row(_build_status_table())
    body.add_row(_build_reminders())
    return Panel.fit(
        body,
        title="[bold blue]Aquarium Dashboard (Demo)[/bold blue]",
        border_style="blue",
    )


def show_dummy_status_ui(animated: bool = True, seconds: int = 12, fps: int = 8) -> None:

    # Render a fake status screen with Rich.
    try:
        from rich.console import Console
        from rich.live import Live
    except ImportError:
        print(".....")
        return

    console = Console()

    if not animated:
        console.print(_build_demo_panel(0))
        return

    sleep_time = 1 / max(1, fps)
    max_frames = max(1, seconds * max(1, fps))

    try:
        with Live(console=console, refresh_per_second=max(1, fps), screen=False) as live:
            for frame in range(max_frames):
                live.update(_build_demo_panel(frame))
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        pass


def prompt_note(action_name: str) -> str | None:
    """
    Ask the user for an optional note.
    - Enter (blank) = no note
    - "n" / "no" = no note
    Returns: note string or None
    """
    try:
        notes = input(f"Add a note for '{action_name}'? (enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n(skipped note)")
        return None

    if notes == "" or notes.lower() in ("n", "no"):
        return None

    return notes


def main():
    parser = argparse.ArgumentParser(prog="ams", description="Aquarium Management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current tank status")
    sub.add_parser("status-demo", help="Show fake status UI with Rich (no API calls)")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Mark last water topoff date (timestamp now)")

    p_logs = sub.add_parser(
        "logs",
        aliases=["maintenance"],
        help="List recent maintenance_log entries"
    )
    p_logs.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "status":
        data = get_data()
        print(json.dumps(data, indent=2))
        return

    if args.cmd == "status-demo":
        show_dummy_status_ui()
        return

    if args.cmd in ("logs", "maintenance"):
        rows = list_maintenance(limit=args.limit)
        print(json.dumps(rows, indent=2))
        return

    # Action commands
    if args.cmd == "fertilize":
        resp = post_fertilize()
        print("✅ Fertilized:", resp)
        action_name = "fertilize"

    elif args.cmd == "trimmed":
        resp = post_trimmed()
        print("✅ Trimmed:", resp)
        action_name = "trimmed"

    elif args.cmd == "topoff":
        resp = post_topoff()
        print("✅ Water Restored:", resp)
        action_name = "topoff"

    else:
        parser.print_help()
        return

    # Prompt for an optional note, then always log the action
    notes = prompt_note(action_name)
    log_resp = log_maintenance(action_name, notes=notes)
    print("📝 Logged:", json.dumps(log_resp, indent=2))


if __name__ == "__main__":
    main()
