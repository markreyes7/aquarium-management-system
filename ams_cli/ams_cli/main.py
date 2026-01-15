# ams_cli/main.py
import argparse
import json
from .api import get_data, post_fertilize, post_trimmed, post_topoff

def main():
    parser = argparse.ArgumentParser(prog="ams", description="Aquarium Management CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show current tank status")

    sub.add_parser("fertilize", help="Mark tank as fertilized (timestamp now)")
    sub.add_parser("trimmed", help="Mark tank as trimmed (timestamp now)")
    sub.add_parser("topoff", help="Mark last water topoff date (timestamp now)")

    args = parser.parse_args()

    if args.cmd == "status":
        data = get_data()
        print(json.dumps(data, indent=2))
    elif args.cmd == "fertilize":
        resp = post_fertilize()
        print("✅ Fertilized:", resp)
    elif args.cmd == "trimmed":
        resp = post_trimmed()
        print("✅ Trimmed:", resp)
    elif args.cmd == "topoff":
        resp = post_topoff()
        print("✅ Water Restored:", resp)

if __name__ == "__main__":
    main()
