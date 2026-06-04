from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Optional

import requests

from config import get_arduino_base_url
from db import get_db
from models import TopoffRunResult

MIN_TOP_OFF_SECONDS = 1.0
MAX_TOP_OFF_SECONDS = 5.0
DEFAULT_REQUEST_TIMEOUT_SECONDS = 5
DEFAULT_POLL_INTERVAL_SECONDS = 0.25
TOP_OFF_STATUS_PATH = "/topoff/status"
TOP_OFF_RUN_PATH = "/topoff/run"

def format_topoff_timestamp(timestamp: Optional[str]) -> Optional[str]:
    if not timestamp:
        return None

    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )
    except ValueError:
        return timestamp


def parse_topoff_duration(user_input: Any) -> Optional[float]:
    try:
        seconds = float(user_input)
    except (TypeError, ValueError):
        return None

    if seconds < MIN_TOP_OFF_SECONDS or seconds > MAX_TOP_OFF_SECONDS:
        return None

    return round(seconds, 2)


def get_last_topoff_timestamp() -> Optional[str]:
    db = get_db()
    row = db.execute(
        "SELECT last_water_topoff FROM tank_status WHERE id = 1"
    ).fetchone()
    if row is None:
        return None
    return row["last_water_topoff"]


def get_topoff_status_snapshot() -> dict[str, Any]:
    db = get_db()
    last_topoff = get_last_topoff_timestamp()
    latest_event = db.execute(
        """
        SELECT id, source, requested_seconds, status, notes,
               arduino_response, created_at, completed_at
        FROM topoff_log
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    return {
        "last_water_topoff": last_topoff,
        "last_water_topoff_display": format_topoff_timestamp(last_topoff),
        "limits": {
            "min_seconds": MIN_TOP_OFF_SECONDS,
            "max_seconds": MAX_TOP_OFF_SECONDS,
        },
        "latest_event": dict(latest_event) if latest_event else None,
    }


def record_topoff_event(
    *,
    source: str,
    requested_seconds: Optional[float],
    status: str,
    notes: Optional[str],
    arduino_response: Optional[str] = None,
    completed: bool = False,
) -> int:
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO topoff_log (
            source,
            requested_seconds,
            status,
            notes,
            arduino_response,
            created_at,
            completed_at
        )
        VALUES (
            ?, ?, ?, ?, ?,
            datetime('now', 'localtime'),
            CASE WHEN ? THEN datetime('now', 'localtime') ELSE NULL END
        )
        """,
        (
            source,
            requested_seconds,
            status,
            notes,
            arduino_response,
            1 if completed else 0,
        ),
    )
    return cursor.lastrowid


def finalize_topoff_event(
    event_id: int,
    *,
    status: str,
    arduino_response: Optional[str] = None,
) -> None:
    db = get_db()
    db.execute(
        """
        UPDATE topoff_log
        SET status = ?,
            arduino_response = COALESCE(?, arduino_response),
            completed_at = datetime('now', 'localtime')
        WHERE id = ?
        """,
        (status, arduino_response, event_id),
    )


def mark_topoff_complete(*, action: str, notes: Optional[str]) -> None:
    db = get_db()
    db.execute(
        """
        UPDATE tank_status
        SET last_water_topoff = datetime('now', 'localtime')
        WHERE id = 1
        """
    )
    db.execute(
        """
        INSERT INTO maintenance_log (action, occurred_at, notes)
        VALUES (?, datetime('now', 'localtime'), ?)
        """,
        (action, notes),
    )


def fetch_arduino_topoff_status() -> tuple[Optional[dict[str, Any]], Optional[str]]:
    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return None, "ARDUINO_BASE_URL is not configured"

    try:
        response = requests.get(
            f"{arduino_base_url}{TOP_OFF_STATUS_PATH}",
            timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        return None, str(exc)

    try:
        return response.json(), None
    except ValueError:
        return {"raw": response.text}, None


def run_topoff_hardware(duration: float) -> TopoffRunResult:
    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return TopoffRunResult(
            ok=False,
            status_code=500,
            error="ARDUINO_BASE_URL is not configured",
        )

    try:
        response = requests.get(
            f"{arduino_base_url}{TOP_OFF_RUN_PATH}",
            params={"seconds": duration},
            timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        return TopoffRunResult(
            ok=False,
            status_code=502,
            error="Could not reach Arduino for topoff",
            details=str(exc),
        )

    response_payload = _response_payload(response)

    if response.status_code >= 400:
        return TopoffRunResult(
            ok=False,
            status_code=502,
            error="Arduino returned a non-200 response",
            arduino_status_code=response.status_code,
            arduino_response=response_payload,
        )

    if response.status_code == 202 or _payload_active(response_payload):
        deadline = time.monotonic() + max(5.0, duration + 3.0)
        final_status = _wait_for_topoff_completion(
            f"{arduino_base_url}{TOP_OFF_STATUS_PATH}",
            deadline,
        )
        if isinstance(final_status, str):
            return TopoffRunResult(
                ok=False,
                status_code=502,
                error="Timed out waiting for Arduino topoff completion",
                details=final_status,
                arduino_response=response_payload,
            )

        if final_status.get("active"):
            return TopoffRunResult(
                ok=False,
                status_code=502,
                error="Arduino topoff did not finish before timeout",
                arduino_response=final_status,
            )

        return TopoffRunResult(
            ok=True,
            status_code=200,
            seconds=duration,
            arduino_response=response_payload,
            final_status=final_status,
        )

    return TopoffRunResult(
        ok=True,
        status_code=200,
        seconds=duration,
        arduino_response=response_payload,
        final_status=response_payload if isinstance(response_payload, dict) else None,
    )


def _payload_active(payload: Any) -> bool:
    return isinstance(payload, dict) and bool(payload.get("active"))


def _response_payload(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text.strip()


def _wait_for_topoff_completion(
    status_url: str,
    deadline: float,
) -> dict[str, Any] | str:
    last_error = "No status response received"

    while time.monotonic() < deadline:
        try:
            response = requests.get(status_url, timeout=DEFAULT_REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
            continue
        except ValueError:
            last_error = "Arduino topoff status returned invalid JSON"
            time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
            continue

        if not payload.get("active"):
            return payload

        time.sleep(DEFAULT_POLL_INTERVAL_SECONDS)

    return last_error
