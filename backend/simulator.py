import json, time, random, requests
from datetime import datetime
import os

def log_temperature(value):
    file_path = "tempHistory.json"
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

    new_item = {
        "timestamp": datetime.now().isoformat(),
        "temperature": value
    }
    data.append(new_item)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

# ---- simulator loop ----
while True:
    temp = 78 + random.random() * 2
    log_temperature(temp)
    requests.post("http://127.0.0.1:3001/update/temp", json={"temperature": temp})
    print(f"Sent temp: {temp}")
    time.sleep(15)
