import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DEFAULT_DATABASE = BASE_DIR / "aquarium.db"
DEFAULT_ARDUINO_BASE_URL = "http://192.168.1.100"
DEFAULT_SERVER_HOST = "0.0.0.0"
DEFAULT_SERVER_PORT = 3001

DEV_DATABASE = BASE_DIR / "aquarium-dev.db"
DEV_ARDUINO_BASE_URL = "http://127.0.0.1:3999"
DEV_SERVER_HOST = "127.0.0.1"
DEV_SERVER_PORT = 3002


def get_database_path() -> Path:
    return Path(os.getenv("AMS_DATABASE", DEFAULT_DATABASE))


def get_arduino_base_url() -> str:
    return os.getenv("AMS_ARDUINO_BASE_URL", DEFAULT_ARDUINO_BASE_URL).rstrip("/")


def get_server_host() -> str:
    return os.getenv("AMS_SERVER_HOST", DEFAULT_SERVER_HOST)


def get_server_port() -> int:
    raw_port = os.getenv("AMS_SERVER_PORT", str(DEFAULT_SERVER_PORT))
    try:
        return int(raw_port)
    except ValueError:
        return DEFAULT_SERVER_PORT


def apply_dev_defaults() -> None:
    os.environ.setdefault("AMS_DATABASE", str(DEV_DATABASE))
    os.environ.setdefault("AMS_ARDUINO_BASE_URL", DEV_ARDUINO_BASE_URL)
    os.environ.setdefault("AMS_SERVER_HOST", DEV_SERVER_HOST)
    os.environ.setdefault("AMS_SERVER_PORT", str(DEV_SERVER_PORT))
