# ams_cli/main.py
import argparse
from datetime import datetime, timedelta
import json

from .api import (
    base_url,
    get_data,
    get_light_status,
    post_light_auto,
    post_fertilize,
    post_light_off,
    post_light_on,
    post_trimmed,
    post_topoff,
    post_runtopoff,
    log_maintenance,
    list_maintenance,
    get_temperature_last_24_hours,
    get_latest_water_parameters,
    get_tank_profile,
    use_dev_base_url,
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


def _format_water_value(value, suffix: str = "") -> str:
    if value is None:
        return "N/A"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    formatted = f"{number:g}"
    return f"{formatted}{suffix}"


def _format_water_tested_at(row) -> str:
    if not row:
        return "N/A"
    return _format_timestamp(row.get("tested_at"))


def _print_water_parameters(row) -> None:
    values = row or {}

    print("Water Parameters")
    print(f"Tested At: {_format_water_tested_at(values)}")
    print(f"pH: {_format_water_value(values.get('ph'))}")
    print(f"Ammonia: {_format_water_value(values.get('ammonia'), ' ppm')}")
    print(f"Nitrite: {_format_water_value(values.get('nitrite'), ' ppm')}")
    print(f"Nitrate: {_format_water_value(values.get('nitrate'), ' ppm')}")
    print(f"GH: {_format_water_value(values.get('gh'), ' dGH')}")
    print(f"KH: {_format_water_value(values.get('kh'), ' dKH')}")
    print(f"TDS: {_format_water_value(values.get('tds'), ' ppm')}")
    if values.get("notes"):
        print(f"Notes: {values.get('notes')}")


def _format_water_summary(row) -> str:
    values = row or {}
    tested_at = _format_water_tested_at(values)
    ph = _format_water_value(values.get("ph"))
    ammonia = _format_water_value(values.get("ammonia"), " ppm")
    nitrite = _format_water_value(values.get("nitrite"), " ppm")
    nitrate = _format_water_value(values.get("nitrate"), " ppm")
    return (
        f"{tested_at} | pH {ph} | NH3 {ammonia} | "
        f"NO2 {nitrite} | NO3 {nitrate}"
    )


def _format_profile_temperature_range(profile) -> str:
    if not profile:
        return "N/A"

    min_temp = profile.get("target_temperature_min")
    max_temp = profile.get("target_temperature_max")
    if min_temp is None and max_temp is None:
        return "N/A"
    if min_temp is None:
        return f"up to {_format_water_value(max_temp)}F"
    if max_temp is None:
        return f"at least {_format_water_value(min_temp)}F"
    return f"{_format_water_value(min_temp)}F - {_format_water_value(max_temp)}F"


def _print_tank_profile(profile) -> None:
    values = profile or {}

    print("Tank Profile")
    print(f"Size: {_format_water_value(values.get('size_gallons'), ' gal')}")
    print(f"Water Type: {values.get('water_type') or 'N/A'}")
    print(f"Target Temp: {_format_profile_temperature_range(values)}")
    print(f"Lighting Schedule: {values.get('lighting_schedule') or 'N/A'}")
    print(f"Setup Date: {values.get('setup_date') or 'N/A'}")
    if values.get("notes"):
        print(f"Notes: {values.get('notes')}")


def _print_plain_status_demo(data) -> None:
    latest_water = data.get("latest_water_parameters") or {}
    tank_profile = data.get("tank_profile") or {}
    recent_water = data.get("recent_water_parameters") or []

    print("AMS Status Demo")
    print(f"Backend: {base_url()}")
    print("")
    _print_tank_profile(tank_profile)
    print("")
    print(f"Current Temperature: {_format_temperature(data.get('temperature')).strip()}")
    print(f"Light Status: {_format_light_status((data.get('latest_light') or {}).get('status', data.get('light_state')))}")
    print(f"Last Fertilized: {_format_timestamp(data.get('last_fertilized'))}")
    print(f"Last Trimmed: {_format_timestamp(data.get('last_trimmed'))}")
    print(f"Last Topoff: {_format_timestamp(data.get('last_water_topoff'))}")
    print("")
    _print_water_parameters(latest_water)
    print("")
    print("Recent Water Parameter Log")
    if not recent_water:
        print("No water parameter logs recorded yet.")
    else:
        for row in recent_water:
            print(f"- {_format_water_summary(row)}")


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
    status_table.add_column(style=ACCENT, no_wrap=False, width=20)
    status_table.add_column(width=3)
    status_table.add_column(style=SOFT_TEXT, no_wrap=False, min_width=18)

    latest_temperature = data.get("latest_temperature") or {}
    latest_light = data.get("latest_light") or {}
    latest_water = data.get("latest_water_parameters") or {}
    tank_profile = data.get("tank_profile") or {}

    status_table.add_row("Backend", "", base_url())
    status_table.add_row("Tank Size", "", _format_water_value(tank_profile.get("size_gallons"), " gal"))
    status_table.add_row("Water Type", "", tank_profile.get("water_type") or "N/A")
    status_table.add_row("Target Temp", "", _format_profile_temperature_range(tank_profile))
    status_table.add_row("Lighting", "", tank_profile.get("lighting_schedule") or "N/A")
    status_table.add_row("Setup Date", "", tank_profile.get("setup_date") or "N/A")
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row(
        "Current Temperature",
        "",
        _format_temperature(data.get("temperature")),
    )
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
    status_table.add_row(Text(""), Text(""), Text(""))
    status_table.add_row("Water Tested", "", _format_water_tested_at(latest_water))
    status_table.add_row("pH", "", _format_water_value(latest_water.get("ph")))
    status_table.add_row(
        "Ammonia",
        "",
        _format_water_value(latest_water.get("ammonia"), " ppm"),
    )
    status_table.add_row(
        "Nitrite",
        "",
        _format_water_value(latest_water.get("nitrite"), " ppm"),
    )
    status_table.add_row(
        "Nitrate",
        "",
        _format_water_value(latest_water.get("nitrate"), " ppm"),
    )
    gh_kh = (
        f"{_format_water_value(latest_water.get('gh'), ' dGH')} / "
        f"{_format_water_value(latest_water.get('kh'), ' dKH')}"
    )
    status_table.add_row("GH / KH", "", gh_kh)
    status_table.add_row("TDS", "", _format_water_value(latest_water.get("tds"), " ppm"))
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
    latest_water = data.get("latest_water_parameters") or {}
    tank_profile = data.get("tank_profile") or {}

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
        "Profile",
        tank_profile.get("water_type") or "N/A",
    )
    summary.add_row(
        "Latest Water",
        _format_water_tested_at(latest_water),
    )
    summary.add_row(
        "Tank Row",
        "Available" if data else "Missing",
    )
    return summary


def _build_profile_panel(data):
    from rich.panel import Panel
    from rich.table import Table

    tank_profile = data.get("tank_profile") or {}

    profile = Table.grid(expand=True)
    profile.add_column(style=ACCENT, no_wrap=True, width=18)
    profile.add_column(style=SOFT_TEXT, no_wrap=False)
    profile.add_row("Size", _format_water_value(tank_profile.get("size_gallons"), " gal"))
    profile.add_row("Water Type", tank_profile.get("water_type") or "N/A")
    profile.add_row("Target Temp", _format_profile_temperature_range(tank_profile))
    profile.add_row("Lighting", tank_profile.get("lighting_schedule") or "N/A")
    profile.add_row("Setup Date", tank_profile.get("setup_date") or "N/A")
    if tank_profile.get("notes"):
        profile.add_row("Notes", tank_profile.get("notes"))

    return Panel(
        profile,
        title="tank profile",
        title_align="left",
        border_style=BORDER,
        padding=(1, 3),
        expand=True,
    )


def _build_live_vitals_panel(data):
    from rich.panel import Panel
    from rich.table import Table

    latest_temperature = data.get("latest_temperature") or {}
    latest_light = data.get("latest_light") or {}

    vitals = Table.grid(expand=True)
    vitals.add_column(style=ACCENT, no_wrap=True, width=18)
    vitals.add_column(style=SOFT_TEXT, no_wrap=False)
    vitals.add_row("Backend", base_url())
    vitals.add_row("Current Temp", _format_temperature(data.get("temperature")).strip())
    vitals.add_row("Latest Temp Log", _format_temperature(latest_temperature.get("temperature")).strip())
    vitals.add_row("Temp Logged At", _format_timestamp(latest_temperature.get("recorded_at")))
    vitals.add_row(
        "Light",
        _format_light_status(latest_light.get("status", data.get("light_state"))),
    )
    vitals.add_row("Last Fertilized", _format_timestamp(data.get("last_fertilized")))
    vitals.add_row("Last Trimmed", _format_timestamp(data.get("last_trimmed")))
    vitals.add_row("Last Topoff", _format_timestamp(data.get("last_water_topoff")))
    vitals.add_row("Latest Note", data.get("latest_maintenance_note") or "No recent note")

    return Panel(
        vitals,
        title="current vitals",
        title_align="left",
        border_style=BORDER,
        padding=(1, 3),
        expand=True,
    )


def _build_latest_water_panel(data):
    from rich.panel import Panel
    from rich.table import Table

    latest_water = data.get("latest_water_parameters") or {}

    water = Table.grid(expand=True)
    water.add_column(style=ACCENT, no_wrap=True, width=18)
    water.add_column(style=SOFT_TEXT, no_wrap=False)
    water.add_row("Tested", _format_water_tested_at(latest_water))
    water.add_row("pH", _format_water_value(latest_water.get("ph")))
    water.add_row("Ammonia", _format_water_value(latest_water.get("ammonia"), " ppm"))
    water.add_row("Nitrite", _format_water_value(latest_water.get("nitrite"), " ppm"))
    water.add_row("Nitrate", _format_water_value(latest_water.get("nitrate"), " ppm"))
    water.add_row(
        "GH / KH",
        (
            f"{_format_water_value(latest_water.get('gh'), ' dGH')} / "
            f"{_format_water_value(latest_water.get('kh'), ' dKH')}"
        ),
    )
    water.add_row("TDS", _format_water_value(latest_water.get("tds"), " ppm"))
    if latest_water.get("notes"):
        water.add_row("Notes", latest_water.get("notes"))

    return Panel(
        water,
        title="latest water parameters",
        title_align="left",
        border_style=BORDER,
        padding=(1, 3),
        expand=True,
    )


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


def _build_recent_water_panel(data):
    from rich.table import Table

    water = Table(
        show_header=True,
        header_style=DETAIL,
        box=None,
        pad_edge=False,
        expand=False,
        padding=(0, 2),
    )
    water.add_column("tested", style=SOFT_TEXT, no_wrap=False, ratio=2)
    water.add_column("readings", style=ACCENT, no_wrap=False, ratio=4)
    water.add_column("notes", style=MUTED_TEXT, no_wrap=False, ratio=2)

    rows = data.get("recent_water_parameters") or []
    if not rows:
        water.add_row("N/A", "No water parameter logs recorded yet", "-")
    else:
        for row in rows:
            readings = (
                f"pH {_format_water_value(row.get('ph'))}; "
                f"NH3 {_format_water_value(row.get('ammonia'), ' ppm')}; "
                f"NO2 {_format_water_value(row.get('nitrite'), ' ppm')}; "
                f"NO3 {_format_water_value(row.get('nitrate'), ' ppm')}; "
                f"GH/KH {_format_water_value(row.get('gh'))}/"
                f"{_format_water_value(row.get('kh'))}; "
                f"TDS {_format_water_value(row.get('tds'), ' ppm')}"
            )
            water.add_row(
                _format_water_tested_at(row),
                readings,
                row.get("notes") or "-",
            )
    return water


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
    from rich.text import Text

    dashboard_width = min(112, max(76, console_width - 2))

    top_content = Group(
        Text("~ tank profile ~", style=ACCENT, justify="center"),
        _build_profile_panel(data),
        Text(""),
        Text("~ live vitals ~", style=ACCENT, justify="center"),
        _build_live_vitals_panel(data),
        Text(""),
        Text("~ water snapshot ~", style=ACCENT, justify="center"),
        _build_latest_water_panel(data),
    )

    recent_activity = Group(
        Text("~ recent activity ~", style=ACCENT, justify="center"),
        Text(
            "pulling from tank_status, tank_profile, water_parameter_log, temperature_log, light_log, plants, maintenance_log",
            style=MUTED_TEXT,
            justify="center",
        ),
        Text(""),
        Panel(
            _build_recent_maintenance_panel(data),
            border_style=BORDER,
            padding=(1, 2),
            expand=True,
        ),
        Text(""),
        Text("~ water parameter log ~", style=ACCENT, justify="center"),
        Text(""),
        Panel(
            _build_recent_water_panel(data),
            border_style=BORDER,
            padding=(1, 2),
            expand=True,
        ),
    )

    centered_group = Group(
        _build_nav_bar(),
        Text(""),
        Text("AMS STATUS DEMO", style=WARM_TEXT, justify="center"),
        Text("calm dev dashboard", style=MUTED_TEXT, justify="center"),
        Text(""),
        top_content,
        Text(""),
        recent_activity,
        Text(""),
        Text("live aquarium command center", style=MUTED_TEXT, justify="center"),
        Text("~" * max(24, dashboard_width - 18), style=DETAIL, justify="center"),
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
        data = get_data()
    except Exception as exc:
        print(f"Unable to load dashboard data: {exc}")
        return

    data = _with_live_light_status(data)

    try:
        from rich.console import Console
    except ImportError:
        _print_plain_status_demo(data)
        return

    console = Console()

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
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Use the local development backend at http://127.0.0.1:3002",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current tank status")
    sub.add_parser("status-demo", help="Show live status UI with Rich")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Manually mark last water topoff date (timestamp now)")
    sub.add_parser("runtopoff", help="Run topoff using the Arduino sensor/pump")
    sub.add_parser("lighton", help="Turn the aquarium light on")
    sub.add_parser("lightoff", help="Turn the aquarium light off")
    sub.add_parser("lightstatus", help="Get the current aquarium light status")
    sub.add_parser("lightauto", help="Return the aquarium light to auto mode")
    sub.add_parser(
        "waterparams",
        aliases=["water-parameters"],
        help="Show the latest logged water parameters",
    )
    sub.add_parser(
        "tankprofile",
        aliases=["tank-profile"],
        help="Show the configured tank profile",
    )

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

    if args.dev:
        use_dev_base_url()

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

    if args.cmd in ("waterparams", "water-parameters"):
        resp = get_latest_water_parameters()
        _print_water_parameters(resp.get("latest"))
        return

    if args.cmd in ("tankprofile", "tank-profile"):
        resp = get_tank_profile()
        _print_tank_profile(resp.get("tank_profile"))
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
        resp = post_topoff()
        print("✅ Manual Topoff:", resp)
        action_name = "topoff"

    elif args.cmd == "runtopoff":
        seconds = prompt_topoff_seconds()
        if seconds is None:
            return
        resp = post_runtopoff(seconds)
        print("✅ Water Restored:", resp)
        action_name = "runtopoff"

    else:
        parser.print_help()
        return

    # Prompt for an optional note, then always log the action
    notes = prompt_note(action_name)
    log_resp = log_maintenance(action_name, notes=notes)
    print("📝 Logged:", json.dumps(log_resp, indent=2))


if __name__ == "__main__":
    main()
