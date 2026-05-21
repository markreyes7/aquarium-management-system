from datetime import datetime

from .api import base_url, get_data, get_light_status

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


def _format_livestock(row) -> str:
    common_name = row.get("common_name") or "N/A"
    quantity = row.get("quantity")
    if quantity is None:
        return common_name
    return f"{common_name} x{quantity}"


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


def _print_livestock(rows) -> None:
    livestock = [row for row in (rows or []) if row]

    print("Livestock")
    if not livestock:
        print("No livestock currently marked in tank.")
        return

    for row in livestock:
        print(f"- {_format_livestock(row)}")


def _print_plain_status(data) -> None:
    latest_water = data.get("latest_water_parameters") or {}
    tank_profile = data.get("tank_profile") or {}
    livestock = data.get("livestock") or []
    recent_water = data.get("recent_water_parameters") or []

    print("AMS Status")
    print(f"Backend: {base_url()}")
    print("")
    _print_tank_profile(tank_profile)
    print("")
    _print_livestock(livestock)
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


def _build_profile_panel(data):
    from rich.panel import Panel
    from rich.table import Table

    tank_profile = data.get("tank_profile") or {}
    livestock = data.get("livestock") or []

    profile = Table.grid(expand=True)
    profile.add_column(style=ACCENT, no_wrap=True, width=18)
    profile.add_column(style=SOFT_TEXT, no_wrap=False)
    profile.add_row("Size", _format_water_value(tank_profile.get("size_gallons"), " gal"))
    profile.add_row("Water Type", tank_profile.get("water_type") or "N/A")
    profile.add_row("Target Temp", _format_profile_temperature_range(tank_profile))
    profile.add_row("Lighting", tank_profile.get("lighting_schedule") or "N/A")
    profile.add_row("Setup Date", tank_profile.get("setup_date") or "N/A")
    if livestock:
        for row in livestock:
            profile.add_row("Livestock", _format_livestock(row))
    else:
        profile.add_row("Livestock", "N/A")
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
        Text("AMS STATUS", style=WARM_TEXT, justify="center"),
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


def show_status() -> None:
    try:
        data = get_data()
    except Exception as exc:
        print(f"Unable to load dashboard data: {exc}")
        return

    data = _with_live_light_status(data)

    try:
        from rich.console import Console
    except ImportError:
        _print_plain_status(data)
        return

    console = Console()
    console.print(_build_status_dashboard(data, console.width))
