# ams_cli/api.py
import os
import requests

DEFAULT_BASE_URL = "http://127.0.0.1:3001" # local dev

def base_url() -> str:
    return os.getenv("AMS_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

def get_data() -> dict:
    r = requests.get(f"{base_url()}/data", timeout=5)
    r.raise_for_status()
    return r.json()

def post_fertilize() -> dict:
    r = requests.post(f"{base_url()}/update/fertilize", timeout=5)
    r.raise_for_status()
    return r.json()

def post_trimmed() -> dict:
    r = requests.post(f"{base_url()}/update/trimmed", timeout=5)
    r.raise_for_status()
    return r.json()

def post_topoff() -> dict:
    r = requests.post(f"{base_url()}/update/topoff", timeout=5)
    r.raise_for_status()
    return r.json()
