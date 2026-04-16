# ams_cli/main.py
import argparse
from datetime import datetime, timedelta
import json

from .api import (
    get_data,
    get_light_status,
    post_light_auto,
    post_fertilize,
    post_light_off,
    post_light_on,
    post_trimmed,
    post_topoff,
    log_maintenance,
    list_maintenance,
    get_temperature_last_24_hours,
)

ACCENT = "bold #8be9c1"
SOFT_TEXT = "#b8f2e6"
MUTED_TEXT = "#9ccfd8"
WARM_TEXT = "#f6c6ea"
BORDER = "#7bdff2"
DETAIL = "#cdb4db"


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "N/A"

    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        return value

# this is running fine. status demo is still not showing the full value
def _format_temperature(value) -> str:
    if value is None:
        return "N/A"

    try:
        return " " + f"{float(value):.1f}F"
    except (TypeError, ValueError):
        return str(value)


def _format_light_status(value) -> str:
    if value is None:
        return "Unknown"
    if value in (1, "1", True, "on", "ON"):
        return "On"
    if value in (0, "0", False, "off", "OFF"):
        return "Off"
    return str(value)


def _with_live_light_status(data):
    enriched = dict(data)
    latest_light = dict(enriched.get("latest_light") or {})

    try:
        live_light = get_light_status()
    except Exception:
        live_light = None

    if isinstance(live_light, dict):
        live_status = live_light.get("status")
        if live_status in ("on", "off"):
            latest_light["status"] = live_status
            enriched["live_light_status"] = live_status

    if latest_light:
        enriched["latest_light"] = latest_light

    return enriched


def _build_status_table(data):
    from rich.table import Table
    from rich.text import Text

    status_table = Table.grid(expand=True)
    status_table.add_column(style=ACCENT, no_wrap=False, width=18)
    status_table.add_column(width=2)
    status_table.add_column(style=SOFT_TEXT, no_wrap=True, min_width=12)

    latest_temperature = data.get("latest_temperature") or {}
    latest_light = data.get("latest_light") or {}

    status_table.add_row("Current Temperature" ,"", _format_temperature(data.get("temperature")))
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row(
        "Latest Temp Log",
        "",
        _format_temperature(latest_temperature.get("temperature")),
    )
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row(
        "Temp Logged At",
        "",
        _format_timestamp(latest_temperature.get("recorded_at")),
    )
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row(
        "Light Status",
        "",
        _format_light_status(
            latest_light.get("status", data.get("light_state"))
        ),
    )

    status_table.add_row(Text(""), Text(""), Text(""))

    status_table.add_row(
        "Last Fertilized",
        "",
        _format_timestamp(data.get("last_fertilized")),
    )

    status_table.add_row(Text(""), Text(""), Text(""))

    status_table.add_row(
        "Last Trimmed",
        "",
        _format_timestamp(data.get("last_trimmed")),
    )
    status_table.add_row(Text(""), Text(""), Text(""))
    
    status_table.add_row(
        "Last Topoff",
        "",
        _format_timestamp(data.get("last_water_topoff")),
    )
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row(
        "Latest Note",
        "",
        data.get("latest_maintenance_note") or "No recent note",
    )
    return status_table


def _build_welcome_panel():
    from rich.align import Align
    from rich.text import Text

    welcome_text = Text(justify="center")
    welcome_text.append("\n", style=MUTED_TEXT)
    welcome_text.append("WELCOME TO AMS\n", style=WARM_TEXT)
    welcome_text.append("aquarium management system\n", style=ACCENT)
    welcome_text.append("live tank status dashboard", style=MUTED_TEXT)
    welcome_text.append("\n", style=MUTED_TEXT)

    return Align.center(welcome_text)


def _build_summary_table(data):
    from rich.table import Table

    summary = Table(
        show_header=False,
        box=None,
        pad_edge=False,
        expand=False,
        padding=(0, 3),
    )
    summary.add_column("Source", style=ACCENT, no_wrap=True, min_width=12)
    summary.add_column("Status", style=SOFT_TEXT, min_width=18)

    plant_summary = data.get("plant_summary") or {}
    maintenance_summary = data.get("maintenance_summary") or {}
    latest_light = data.get("latest_light") or {}

    summary.add_row(
        "Plants",
        f"{plant_summary.get('plants_in_tank', 0)} in tank / {plant_summary.get('total_plants', 0)} total",
    )
    summary.add_row(
        "Maintenance",
        f"{maintenance_summary.get('total_events', 0)} logged events",
    )
    summary.add_row(
        "Light Log",
        _format_timestamp(latest_light.get("recorded_at")),
    )
    summary.add_row(
        "Tank Row",
        "Available" if data else "Missing",
    )
    return summary


def _build_recent_maintenance_panel(data):
    from rich.table import Table

    recent = Table(
        show_header=True,
        header_style=DETAIL,
        box=None,
        pad_edge=False,
        expand=False,
        padding=(0, 3),
    )
    recent.add_column("action", style=ACCENT, no_wrap=True)
    recent.add_column("when", style=SOFT_TEXT, no_wrap=True)
    recent.add_column("notes", style=MUTED_TEXT, overflow="fold")

    rows = data.get("recent_maintenance") or []
    if not rows:
        recent.add_row("N/A", "N/A", "No maintenance logged yet")
    else:
        for row in rows:
            recent.add_row(
                str(row.get("action", "N/A")).title(),
                _format_timestamp(row.get("occurred_at")),
                row.get("notes") or "-",
            )
    return recent


def _build_nav_bar():
    from rich.table import Table

    nav = Table(
        show_header=False,
        box=None,
        expand=True,
        pad_edge=False,
        padding=(0, 2),
    )
    for _ in range(4):
        nav.add_column(style=DETAIL, justify="center", ratio=1)

    nav.add_row(
        "terminal",
        "tank status",
        "welcome",
        "ams dashboard",
    )
    return nav


def _build_footer():
    from rich.text import Text

    footer = Text(justify="center")
    footer.append("r refresh   ", style=DETAIL)
    footer.append("t temp24   ", style=MUTED_TEXT)
    footer.append("l light status   ", style=SOFT_TEXT)
    footer.append("q quit", style=WARM_TEXT)
    return footer


def _build_status_dashboard(data, console_width: int):
    from rich.align import Align
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    dashboard_width = max(90, console_width - 4)

    top_content = Table.grid(expand=True)
    top_content.add_column(ratio=5, min_width=34)
    top_content.add_column(ratio=3, min_width=20)
    top_content.add_column(ratio=4, min_width=28)

    top_content.add_row(
        Text("~ tank ~", style=ACCENT),
        _build_welcome_panel(),
        Text("~ summary ~", style=ACCENT),
    )
    top_content.add_row(
        _build_status_table(data),
        Text(""),
        Panel(
            _build_summary_table(data),
            title="summary",
            title_align="left",
            border_style=BORDER,
            padding=(1, 2),
            expand=False,
        ),
    )

    recent_activity = Group(
        Text("~ recent activity ~", style=ACCENT),
        Text(
            "pulling from tank_status, temperature_log, light_log, plants, maintenance_log",
            style=MUTED_TEXT,
        ),
        Text(""),
        Panel(
            _build_recent_maintenance_panel(data),
            border_style=BORDER,
            padding=(1, 2),
            expand=True,
        ),
    )

    centered_group = Group(
        _build_nav_bar(),
        Text(""),
        top_content,
        Text(""),
        recent_activity,
        Text(""),
        Text("live aquarium command center", style=WARM_TEXT, justify="center"),
        Text("~" * 76, style=DETAIL, justify="center"),
        _build_footer(),
    )

    return Align.center(
        Panel(
            centered_group,
            border_style=BORDER,
            padding=(2, 3),
            expand=False,
            width=dashboard_width,
        )
    )


def show_status_ui() -> None:
    try:
        from rich.console import Console
    except ImportError:
        print(".....")
        return

    console = Console()
    try:
        data = get_data()
    except Exception as exc:
        print(f"Unable to load dashboard data: {exc}")
        return

    data = _with_live_light_status(data)

    console.print(_build_status_dashboard(data, console.width))


def prompt_note(action_name: str) -> str | None:
    try:
        notes = input(f"Add a note for '{action_name}'? (enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n(skipped note)")
        return None

    if notes == "" or notes.lower() in ("n", "no"):
        return None

    return notes


def prompt_topoff_seconds() -> float | None:
    try:
        data = get_data()
        last_topoff = data.get("last_water_topoff")
    except Exception:
        last_topoff = None

    if last_topoff:
        print(f"Last water topoff: {last_topoff}")
    else:
        print("Last water topoff: No topoff recorded yet.")

    while True:
        try:
            user_input = input("Enter seconds to run pump (between 1-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n(topoff cancelled)")
            return None

        try:
            seconds = float(user_input)
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if seconds <= 0 or seconds > 5:
            print("Time must be between 1 and 5 seconds.")
            continue

        return seconds


def main():
    parser = argparse.ArgumentParser(prog="ams", description="Aquarium Management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current tank status")
    sub.add_parser("status-demo", help="Show live status UI with Rich")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Mark last water topoff date (timestamp now)")
    sub.add_parser("lighton", help="Turn the aquarium light on")
    sub.add_parser("lightoff", help="Turn the aquarium light off")
    sub.add_parser("lightstatus", help="Get the current aquarium light status")
    sub.add_parser("lightauto", help="Return the aquarium light to auto mode")

    p_logs = sub.add_parser(
        "logs",
        aliases=["maintenance"],
        help="List recent maintenance_log entries"
    )
    p_logs.add_argument("--limit", type=int, default=20)

    p_graph = sub.add_parser(
        "temp24",
        help="Show temperature history for the last 24 hours"
    )

    args = parser.parse_args()

    if args.cmd == "status":
        data = get_data()
        print(json.dumps(data, indent=2))
        return

    if args.cmd == "status-demo":
        show_status_ui()
        return

    if args.cmd in ("logs", "maintenance"):
        rows = list_maintenance(limit=args.limit)
        print(json.dumps(rows, indent=2))
        return

    if args.cmd == "temp24":
        try:
            import plotext as plt
        except ImportError:
            print("plotext not installed. Run: pip install plotext")
            return

        logs = get_temperature_last_24_hours()
        if not logs:
            print("No temperature data available in the last 24 hours.")
            return

        temps = [entry["temperature"] for entry in logs]
        now = datetime.now()
        window_start = now - timedelta(hours=24)

        x_hours = []
        for entry in logs:
            recorded_at = datetime.fromisoformat(entry["recorded_at"])
            hours_since_start = (recorded_at - window_start).total_seconds() / 3600
            x_hours.append(max(0, min(24, hours_since_start)))

        print(f"Fetched {len(logs)} temperature readings from the last 24 hours.")
        print(f"Temperature range: {min(temps):.1f}°F - {max(temps):.1f}°F")

        # plt.colorize("red on black, bold",        "red",        "bold",      "black",         True) #for text
        plt.theme('clear')
        
        plt.plot(x_hours, temps, marker='fhd', color='cyan+' )
        plt.plotsize(50, 15)  # Make the plot larger for better visibility
        plt.xlim(0, 24)
        plt.xticks(
            [0, 4, 8, 12, 16, 20, 24],
            ["00", "04", "08", "12", "16", "20", "24"],
        )
        plt.title("Temperature History (Last 24 Hours)")
        plt.xlabel("Time")
        plt.ylabel("Temperature (°F)")
        plt.show()
        return

    if args.cmd == "lighton":
        resp = post_light_on()
        print(json.dumps(resp, indent=2))
        return

    elif args.cmd == "lightoff":
        resp = post_light_off()
        print(json.dumps(resp, indent=2))
        return

    elif args.cmd == "lightstatus":
        resp = get_light_status()
        print(resp.get("status", "unknown"))
        return

    elif args.cmd == "lightauto":
        resp = post_light_auto()
        print(json.dumps(resp, indent=2))
        return

    elif args.cmd == "fertilize":
        resp = post_fertilize()
        print("✅ Fertilized:", resp)
        action_name = "fertilize"

    elif args.cmd == "trimmed":
        resp = post_trimmed()
        print("✅ Trimmed:", resp)
        action_name = "trimmed"

    elif args.cmd == "topoff":
        seconds = prompt_topoff_seconds()
        if seconds is None:
            return
        resp = post_topoff(seconds)
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
