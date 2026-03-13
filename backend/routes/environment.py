from flask import Blueprint, jsonify, request
from db import get_db

bp = Blueprint("environment", __name__)

@bp.route("/temp", methods=["GET"])
def get_temp():
    """Return the current temperature (and optionally other status).

    This endpoint is intended as a simple "check the temperature" command
    used by clients.  It no longer touches the log table; the log remains
    intact for historical records.  The most recent reading is stored in
    the singleton ``tank_status`` row, which is updated whenever a new
    temperature is logged.
    """
    db = get_db()
    row = db.execute(
        "SELECT temperature FROM tank_status WHERE id = 1"
    ).fetchone()
    return jsonify({"temperature": row["temperature"] if row else None})

@bp.route("/environment/temperature", methods=["POST"])
def log_temperature():
    """Store a new reading in the log and update the status table."""
    payload = request.get_json(force=True)
    temp = payload.get("temperature")

    if temp is None:
        return jsonify({"ok": False, "error": "Missing temperature"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO temperature_log (temperature) VALUES (?)",
        (temp,)
    )
    # # also keep the singleton status row current so /temp is fast
    # db.execute(
    #     "UPDATE tank_status SET temperature = ? WHERE id = 1",
    #     (temp,)
    # )
    db.commit()

    return jsonify({"ok": True, "temperature": temp})

@bp.route("/environment/temperature/latest", methods=["GET"])
def latest_temperature():
    db = get_db()
    row = db.execute(
        "SELECT temperature, recorded_at FROM temperature_log "
        "ORDER BY recorded_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return jsonify({"ok": True, "latest": None})
    return jsonify({"ok": True, "latest": dict(row)})


@bp.route("/update/temperature", methods=["POST"])
def update_temperature_status():
    """Update the tank_status with the latest temperature from the log."""
    db = get_db()
    row = db.execute(
        "SELECT temperature FROM temperature_log "
        "ORDER BY recorded_at DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return jsonify({"ok": False, "error": "No temperature data available"}), 404

    db.execute(
        "UPDATE tank_status SET temperature = ? WHERE id = 1",
        (row["temperature"],)
    )
    db.commit()
    return jsonify({"ok": True, "temperature": row["temperature"]})
