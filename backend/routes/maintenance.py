from datetime import datetime
import requests
from flask import Blueprint, jsonify, request
from db import get_db
from typing import Any, Dict, List, Optional

bp = Blueprint("maintenance", __name__)


def _format_topoff_timestamp(timestamp: Optional[str]) -> Optional[str]:
    if not timestamp:
        return None

    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime(
            "%Y-%m-%d %I:%M:%S %p"
        )
    except ValueError:
        return timestamp


def get_arduino_base_url() -> str:
    return "http://192.168.1.100"

# Optional: keep welcome route if you want
@bp.route("/", methods=["GET"])
def welcome():
    return "Welcome to the best aquarium API"


@bp.route("/data", methods=["GET"])
def get_data():
    db = get_db()
    row = db.execute("SELECT * FROM tank_status WHERE id = 1").fetchone()
    data = dict(row) if row else {}

    latest_note_row = db.execute(
        """
        SELECT notes
        FROM maintenance_log
        WHERE notes IS NOT NULL AND TRIM(notes) <> ''
        ORDER BY occurred_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()

    data["latest_maintenance_note"] = (
        latest_note_row["notes"] if latest_note_row else None
    )

    return jsonify(data)

@bp.route("/maintenance", methods=["GET"])
def list_maintenance():
    limit = request.args.get("limit", "50")
    try:
        limit_i = max(1, min(200, int(limit)))
    except ValueError:
        return jsonify({"ok": False, "error": "limit must be an integer"}), 400

    db = get_db()
    rows = db.execute(
        """
        SELECT id, action, occurred_at, notes
        FROM maintenance_log
        ORDER BY occurred_at DESC
        LIMIT ?
        """,
        (limit_i,)
    ).fetchall()

    return jsonify([dict(r) for r in rows])


@bp.route("/maintenance", methods=["POST"])
def add_maintenance():
    payload = request.get_json(force=True)
    action = payload.get("action")
    notes = payload.get("notes")
    if notes is None:
        # backward-compatible fallback for older clients
        notes = payload.get("note")

    if not action:
        return jsonify({"ok": False, "error": "Missing action"}), 400

    action = action.strip().lower()

    db = get_db()
    db.execute(
        "INSERT INTO maintenance_log (action, notes) VALUES (?, ?)",
        (action, notes)
    )
    db.commit()

    return jsonify({"ok": True, "action": action, "notes": notes})



def _log_action(action: str, notes: str | None = None) -> None:
    db = get_db()
    db.execute("INSERT INTO maintenance_log (action, notes) VALUES (?, ?)", (action, notes))

@bp.route("/update/fertilize", methods=["POST"])
def update_fertilized():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes")  # optional

    db = get_db()

    # update current status of tank
    db.execute(
        """
        UPDATE tank_status
        SET last_fertilized = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("fertilize", notes)

    db.commit()
    return jsonify({"ok": True, "action": "fertilize", "notes": notes})

@bp.route("/update/trimmed", methods=["POST"])
def update_trimmed():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes") 

    db = get_db()

    db.execute(
        """
        UPDATE tank_status
        SET last_trimmed = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("trimmed", notes)
    db.commit()

    return jsonify({"ok": True, "action": "trimmed", "notes": notes})


@bp.route("/update/topoff", methods=["POST"])
def update_topoff():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes")
    duration = topoff_time_duration(payload.get("seconds"))

    db = get_db()
    last_topoff_row = db.execute(
        "SELECT last_water_topoff FROM tank_status WHERE id = 1"
    ).fetchone()
    last_topoff = last_topoff_row["last_water_topoff"] if last_topoff_row else None
    formatted_last_topoff = _format_topoff_timestamp(last_topoff)

    if duration is None:
        return jsonify({
            "ok": False,
            "error": "seconds must be a number between 1 and 5",
            "last_topoff": formatted_last_topoff,
        }), 400

    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return jsonify({
            "ok": False,
            "error": "ARDUINO_BASE_URL is not configured",
            "last_topoff": formatted_last_topoff,
        }), 500

    try:
        topoff_request = requests.get(
            f"{arduino_base_url}/topoff",
            params={"seconds": duration},
            timeout=max(5, int(duration) + 3),
        )
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Could not reach Arduino for topoff",
            "details": str(exc),
            "last_topoff": formatted_last_topoff,
        }), 502

    if topoff_request.status_code != 200:
        return jsonify({
            "ok": False,
            "error": "Arduino returned a non-200 response",
            "arduino_status_code": topoff_request.status_code,
            "arduino_response": topoff_request.text,
            "last_topoff": formatted_last_topoff,
        }), 502

    db.execute(
        """
        UPDATE tank_status
        SET last_water_topoff = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("topoff", notes)
    db.commit()

    return jsonify({
        "ok": True,
        "action": "topoff",
        "notes": notes,
        "seconds": duration,
        "arduino_response": topoff_request.text.strip(),
        "last_topoff_before_update": formatted_last_topoff,
    })

def topoff_time_duration(user_input: Any) -> Optional[float]:
    """
    Validate the requested pump runtime for a topoff.
    The client should display the previous topoff time before sending this value.
    """
    try:
        seconds = float(user_input)
    except (TypeError, ValueError):
        return None

    if seconds <= 0 or seconds > 5:
        return None

    return seconds
