import json
from datetime import datetime
import os

def log_temperature(value):
    file_path = "tempHistory.json"

    # Try to load existing data
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
        except (json.JSONDecodeError, FileNotFoundError):
            data = []
    else:
        data = []

    # Append the new record
    new_item = {
        "timestamp": datetime.now().isoformat(),
        "temperature": value
    }
    data.append(new_item)

    # Write updated data back
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
