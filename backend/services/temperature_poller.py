import os
import sqlite3
import sys
import time
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parents[1]
DATABASE = BASE_DIR / "aquarium.db"

DEFAULT_SENSOR_URL = "http://192.168.1.100/temp"
DEFAULT_POLL_INTERVAL_SECONDS = 240
DEFAULT_REQUEST_TIMEOUT_SECONDS = 5


"""this needs to be reworked. needs better optimization"""
def sensor_url() -> str:
    return os.getenv("AMS_TEMPERATURE_SENSOR_URL", DEFAULT_SENSOR_URL)


def poll_interval_seconds() -> int:
    raw_value = os.getenv("AMS_TEMPERATURE_POLL_INTERVAL_SECONDS", "")
    try:
        return max(1, int(raw_value))
    except ValueError:
        return DEFAULT_POLL_INTERVAL_SECONDS


def request_timeout_seconds() -> int:
    raw_value = os.getenv("AMS_TEMPERATURE_REQUEST_TIMEOUT_SECONDS", "")
    try:
        return max(1, int(raw_value))
    except ValueError:
        return DEFAULT_REQUEST_TIMEOUT_SECONDS


def fetch_current_temperature() -> float:
    response = requests.get(sensor_url(), timeout=request_timeout_seconds())
    response.raise_for_status()

    payload = response.json()
    value = payload.get("temperature")
    if value is None:
        value = payload.get("temp")
    if value is None:
        value = payload.get("temperature_f")
    if value is None:
        raise ValueError(
            "Temperature payload missing 'temperature', 'temp', or 'temperature_f' field"
        )

    return float(value)


def save_temperature_reading(temperature: float) -> None:
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute("INSERT OR IGNORE INTO tank_status (id) VALUES (1)")
        conn.execute(
            "INSERT INTO temperature_log (temperature) VALUES (?)",
            (temperature,)
        )
        conn.execute(
            "UPDATE tank_status SET temperature = ? WHERE id = 1",
            (temperature,)
        )
        conn.commit()
    finally:
        conn.close()


def run_temperature_poller() -> None:
    interval = poll_interval_seconds()
    print(f"Temperature poller running every {interval}s")
    print(f"Sensor URL: {sensor_url()}")
    print(f"Database: {DATABASE}")

    while True:
        try:
            temperature = fetch_current_temperature()
            save_temperature_reading(temperature)
            print(f"Saved temperature: {temperature}")
        except requests.RequestException as exc:
            print(f"Temperature poller shutting down: sensor/Arduino is not online: {exc}")
            sys.exit(1)
        except ValueError as exc:
            print(f"Temperature poll failed: {exc}")

        time.sleep(interval)


if __name__ == "__main__":
    run_temperature_poller()
