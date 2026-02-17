# ams_cli/main.py
import argparse
import json

from .api import (
    get_data,
    post_fertilize,
    post_trimmed,
    post_topoff,
    log_maintenance,
    list_maintenance,
)

def prompt_note(action_name: str) -> str | None:
    """
    Ask the user for an optional note.
    - Enter (blank) = no note
    - "n" / "no" = no note
    Returns: note string or None
    """
    try:
        note = input(f"Add a note for '{action_name}'? (enter to skip): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n(skipped note)")
        return None

    if note == "" or note.lower() in ("n", "no"):
        return None

    return note


def main():
    parser = argparse.ArgumentParser(prog="ams", description="Aquarium Management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current tank status")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Mark last water topoff date (timestamp now)")

    p_logs = sub.add_parser("logs", help="List recent maintenance_log entries")
    p_logs.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "status":
        data = get_data()
        print(json.dumps(data, indent=2))
        return

    if args.cmd == "logs":
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
    note = prompt_note(action_name)
    log_resp = log_maintenance(action_name, note=note)
    print("📝 Logged:", json.dumps(log_resp, indent=2))


if __name__ == "__main__":
    main()
