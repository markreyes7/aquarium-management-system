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

def post_fertilize() -> Dict[str, Any]:
    return _post("/update/fertilize")

def post_trimmed() -> Dict[str, Any]:
    return _post("/update/trimmed")

def post_topoff() -> Dict[str, Any]:
    return _post("/update/topoff")

# ---- new logging endpoints ----
def log_maintenance(action: str, note: Optional[str] = None, occurred_at: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"action": action}
    if note is not None:
        payload["note"] = note
    if occurred_at is not None:
        payload["occurred_at"] = occurred_at
    return _post("/maintenance", json=payload)

def list_maintenance(limit: int = 20) -> List[Dict[str, Any]]:
    return _get("/maintenance", params={"limit": limit})
