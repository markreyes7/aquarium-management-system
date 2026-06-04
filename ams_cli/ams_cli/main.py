# ams_cli/main.py
import argparse
from datetime import datetime, timedelta
import json

from .api import (
    get_data,
    get_light_status,
    get_topoff_status,
    post_light_auto,
    post_fertilize,
    post_light_off,
    post_light_on,
    post_trimmed,
    post_topoff,
    post_runtopoff,
    list_maintenance,
    add_livestock,
    list_livestock,
    remove_livestock,
    get_temperature_last_24_hours,
    get_latest_water_parameters,
    get_tank_profile,
    update_tank_profile,
    use_dev_base_url,
)
from .status_dashboard import show_status


def _format_timestamp(value: str | None) -> str:
    if not value:
        return "N/A"

    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %I:%M %p")
    except ValueError:
        return value

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


def _format_livestock(row) -> str:
    common_name = row.get("common_name") or "N/A"
    quantity = row.get("quantity")
    if quantity is None:
        return common_name
    return f"{common_name} x{quantity}"


def _print_livestock(rows) -> None:
    livestock = [row for row in (rows or []) if row]

    print("Livestock")
    if not livestock:
        print("No livestock currently marked in tank.")
        return

    for row in livestock:
        row_id = row.get("id")
        prefix = f"{row_id}: " if row_id is not None else "- "
        print(f"{prefix}{_format_livestock(row)}")


def _build_tank_profile_update_payload(args) -> dict:
    fields = {
        "size_gallons": args.size_gallons,
        "water_type": args.water_type,
        "target_temperature_min": args.target_temperature_min,
        "target_temperature_max": args.target_temperature_max,
        "lighting_schedule": args.lighting_schedule,
        "setup_date": args.setup_date,
        "notes": args.notes,
    }
    return {field: value for field, value in fields.items() if value is not None}


def _prompt_optional_text(question: str) -> str | None:
    value = input(f"{question} (enter to skip): ").strip()
    return value or None


def _prompt_optional_float(question: str) -> float | None:
    while True:
        value = _prompt_optional_text(question)
        if value is None:
            return None

        try:
            return float(value)
        except ValueError:
            print("Please enter a number, or press enter to skip.")


def _prompt_water_type() -> str | None:
    choices = {"freshwater", "saltwater", "brackish"}

    while True:
        value = _prompt_optional_text(
            "What is the water type? freshwater, saltwater, or brackish"
        )
        if value is None:
            return None

        normalized = value.lower()
        if normalized in choices:
            return normalized

        print("Water type must be freshwater, saltwater, or brackish.")


def _prompt_livestock_type() -> str | None:
    choices = {"fish", "shrimp", "snail", "crab", "coral", "other"}

    while True:
        value = _prompt_optional_text(
            "What type is it? fish, shrimp, snail, crab, coral, or other"
        )
        if value is None:
            return None

        normalized = value.lower()
        if normalized in choices:
            return normalized

        print("Livestock type must be fish, shrimp, snail, crab, coral, or other.")


def _prompt_optional_int(question: str) -> int | None:
    while True:
        value = _prompt_optional_text(question)
        if value is None:
            return None

        try:
            parsed = int(value)
        except ValueError:
            print("Please enter a whole number, or press enter to skip.")
            continue

        if parsed <= 0:
            print("Please enter a positive number, or press enter to skip.")
            continue

        return parsed


def _prompt_add_livestock_payload() -> dict | None:
    try:
        common_name = None
        while not common_name:
            common_name = _prompt_optional_text("What is the common name?")
            if not common_name:
                print("Common name is required.")

        species_name = _prompt_optional_text("What is the species name?")
        livestock_type = _prompt_livestock_type()
        quantity = _prompt_optional_int("How many are being added?") or 1
        notes = _prompt_optional_text("Any livestock notes?")
    except (EOFError, KeyboardInterrupt):
        print("\n(livestock add cancelled)")
        return None

    payload = {
        "common_name": common_name,
        "quantity": quantity,
    }
    if species_name is not None:
        payload["species_name"] = species_name
    if livestock_type is not None:
        payload["livestock_type"] = livestock_type
    if notes is not None:
        payload["notes"] = notes
    return payload


def _prompt_remove_livestock_payload() -> dict | None:
    try:
        rows = list_livestock().get("livestock") or []
        _print_livestock(rows)
        print("")

        raw_id = _prompt_optional_text("Which livestock id should be removed?")
        payload = {}
        if raw_id is not None:
            try:
                payload["id"] = int(raw_id)
            except ValueError:
                print("Livestock id must be a whole number.")
                return None
        else:
            common_name = _prompt_optional_text("What common name should be removed?")
            if not common_name:
                print("Livestock id or common name is required.")
                return None
            payload["common_name"] = common_name

        quantity = _prompt_optional_int("How many should be removed?")
        if quantity is not None:
            payload["quantity"] = quantity

        notes = _prompt_optional_text("Any removal notes?")
        if notes is not None:
            payload["notes"] = notes
    except (EOFError, KeyboardInterrupt):
        print("\n(livestock remove cancelled)")
        return None

    return payload


def _prompt_tank_profile_update_payload(args) -> dict | None:
    payload = _build_tank_profile_update_payload(args)

    try:
        if args.size_gallons is None:
            value = _prompt_optional_float("What is the tank size in gallons?")
            if value is not None:
                payload["size_gallons"] = value

        if args.water_type is None:
            value = _prompt_water_type()
            if value is not None:
                payload["water_type"] = value

        if args.target_temperature_min is None:
            value = _prompt_optional_float("What is the minimum target temperature?")
            if value is not None:
                payload["target_temperature_min"] = value

        if args.target_temperature_max is None:
            value = _prompt_optional_float("What is the maximum target temperature?")
            if value is not None:
                payload["target_temperature_max"] = value

        if args.lighting_schedule is None:
            value = _prompt_optional_text("What is the lighting schedule?")
            if value is not None:
                payload["lighting_schedule"] = value

        if args.setup_date is None:
            value = _prompt_optional_text("What is the setup date?")
            if value is not None:
                payload["setup_date"] = value

        if args.notes is None:
            value = _prompt_optional_text("Any tank profile notes?")
            if value is not None:
                payload["notes"] = value
    except (EOFError, KeyboardInterrupt):
        print("\n(tank profile update cancelled)")
        return None

    return payload


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
        payload = get_topoff_status()
        topoff = payload.get("topoff") or {}
        last_topoff = topoff.get("last_water_topoff_display")
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

    sub.add_parser("status", help="Show current tank dashboard")
    sub.add_parser("status-json", help="Show raw current tank status JSON")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Manually mark last water topoff date (timestamp now)")
    sub.add_parser("runtopoff", help="Run topoff using the Arduino sensor/pump")
    sub.add_parser("addlivestock", help="Add livestock to the tank")
    sub.add_parser("removelivestock", help="Remove livestock from the tank")
    sub.add_parser("livestock", help="List livestock currently in the tank")
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
    p_update_profile = sub.add_parser(
        "updatetankprofile",
        aliases=["update-tank-profile", "updatetank-profile"],
        help="Update the configured tank profile",
    )
    p_update_profile.add_argument("--size-gallons", type=float)
    p_update_profile.add_argument(
        "--water-type",
        choices=["freshwater", "saltwater", "brackish"],
    )
    p_update_profile.add_argument("--target-temperature-min", type=float)
    p_update_profile.add_argument("--target-temperature-max", type=float)
    p_update_profile.add_argument("--lighting-schedule")
    p_update_profile.add_argument("--setup-date")
    p_update_profile.add_argument("--notes")

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
        show_status()
        return

    if args.cmd == "status-json":
        data = get_data()
        print(json.dumps(data, indent=2))
        return

    if args.cmd in ("logs", "maintenance"):
        rows = list_maintenance(limit=args.limit)
        print(json.dumps(rows, indent=2))
        return

    if args.cmd in ("waterparams", "water-parameters"):
        resp = get_latest_water_parameters()
        _print_water_parameters(resp.get("latest"))
        return

    if args.cmd == "livestock":
        resp = list_livestock()
        _print_livestock(resp.get("livestock"))
        return

    if args.cmd == "addlivestock":
        payload = _prompt_add_livestock_payload()
        if payload is None:
            return
        resp = add_livestock(payload)
        print("Added livestock:")
        _print_livestock([resp.get("livestock")])
        return

    if args.cmd == "removelivestock":
        payload = _prompt_remove_livestock_payload()
        if payload is None:
            return
        resp = remove_livestock(payload)
        removed = resp.get("removed") or {}
        print(f"Removed livestock: {_format_livestock(removed)}")
        print("")
        _print_livestock(resp.get("livestock"))
        return

    if args.cmd in ("tankprofile", "tank-profile"):
        resp = get_tank_profile()
        _print_tank_profile(resp.get("tank_profile"))
        return

    if args.cmd in ("updatetankprofile", "update-tank-profile", "updatetank-profile"):
        payload = _prompt_tank_profile_update_payload(args)
        if payload is None:
            return
        if not payload:
            print("No tank profile changes entered.")
            return
        resp = update_tank_profile(payload)
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
        notes = prompt_note("fertilize")
        resp = post_fertilize(notes)
        print("✅ Fertilized:", resp)
        return

    elif args.cmd == "trimmed":
        notes = prompt_note("trimmed")
        resp = post_trimmed(notes)
        print("✅ Trimmed:", resp)
        return

    elif args.cmd == "topoff":
        notes = prompt_note("topoff")
        resp = post_topoff(notes)
        print("✅ Manual Topoff:", resp)
        return

    elif args.cmd == "runtopoff":
        seconds = prompt_topoff_seconds()
        if seconds is None:
            return
        notes = prompt_note("runtopoff")
        resp = post_runtopoff(seconds, notes)
        print("✅ Water Restored:", resp)
        return

    else:
        parser.print_help()
        return


if __name__ == "__main__":
    main()
