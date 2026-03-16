# ams_cli/ams_cli/api.py
import os
from typing import Any, Dict, List, Optional
import requests

DEFAULT_BASE_URL = "http://127.0.0.1:3001"

def base_url() -> str:
    return os.getenv("AMS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

def _get(path: str, *, params: Optional[dict] = None) -> Any:
    url = f"{base_url()}{path}"
    r = requests.get(url, params=params, timeout=8)
    r.raise_for_status()
    return r.json()

def _post(path: str, *, json: Optional[dict] = None) -> Any:
    url = f"{base_url()}{path}"
    r = requests.post(url, json=json, timeout=8)
    r.raise_for_status()
    try:
        return r.json()
    except ValueError:
        return {"ok": True, "raw": r.text}

# ---- names main.py imports ----
def get_data() -> Dict[str, Any]:
    return _get("/data")

def post_fertilize(notes: Optional[str] = None) -> Dict[str, Any]:
    payload = {"notes": notes} if notes else None
    return _post("/update/fertilize", json=payload)

def post_trimmed() -> Dict[str, Any]:
    return _post("/update/trimmed")

def post_topoff() -> Dict[str, Any]:
    return _post("/update/topoff")

# ---- new logging endpoints ----
def log_maintenance(action: str, notes: Optional[str] = None, occurred_at: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"action": action}
    if notes is not None:
        payload["notes"] = notes
    if occurred_at is not None:
        payload["occurred_at"] = occurred_at
    return _post("/maintenance", json=payload)

def list_maintenance(limit: int = 20) -> List[Dict[str, Any]]:
    return _get("/maintenance", params={"limit": limit})

def get_temperature_logs(limit: int = 100) -> List[Dict[str, Any]]:
    return _get("/environment/temperature/logs", params={"limit": limit})

def get_temperature_last_24_hours() -> List[Dict[str, Any]]:
    return _get("/environment/temperature/last-24-hours")

def update_temperature_status() -> Dict[str, Any]:
    return _post("/update/temperature")


def post_light_on() -> Dict[str, Any]:
    return _post("/environment/light/on")


def post_light_off() -> Dict[str, Any]:
    return _post("/environment/light/off")
