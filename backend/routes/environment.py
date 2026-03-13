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

@bp.route("/environment/temperature/logs", methods=["GET"])
def get_temperature_logs():
    """Return recent temperature log entries for analysis."""
    limit = request.args.get("limit", "100") # will be changed in the future
    try:
        limit_i = max(1, min(1000, int(limit)))
    except ValueError:
        return jsonify({"ok": False, "error": "limit must be an integer"}), 400

    db = get_db()
    rows = db.execute(
        """
        SELECT temperature, recorded_at
        FROM temperature_log
        ORDER BY recorded_at DESC
        LIMIT ?
        """,
        (limit_i,)
    ).fetchall()

    return jsonify([dict(r) for r in rows])


@bp.route("/environment/temperature/last-24-hours", methods=["GET"])
def get_temperature_last_24_hours():
    db = get_db()
    rows = db.execute(
        """
        SELECT temperature, recorded_at
        FROM temperature_log
        WHERE recorded_at >= datetime('now', '-24 hours')
        ORDER BY recorded_at ASC
        """
    ).fetchall()

    return jsonify([dict(r) for r in rows])


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
