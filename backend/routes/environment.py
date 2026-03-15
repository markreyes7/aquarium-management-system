import os

import requests
from flask import Blueprint, jsonify, request
from db import get_db
from light_state import normalize_light_state

ARDUINO_BASE_URL = os.getenv("ARDUINO_BASE_URL")

bp = Blueprint("environment", __name__)

@bp.route("/temp", methods=["GET"])
def get_temp():
    db = get_db()
    row = db.execute(
        "SELECT temperature FROM tank_status WHERE id = 1"
    ).fetchone()
    return jsonify({"temperature": row["temperature"] if row else None})

@bp.route("/environment/temperature", methods=["POST"])
def log_temperature():
    payload = request.get_json(force=True)
    temp = payload.get("temperature")

    if temp is None:
        return jsonify({"ok": False, "error": "Missing temperature"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO temperature_log (temperature) VALUES (?)",
        (temp,)
    )
    
    db.commit()

@bp.route("/environment/temperature/logs", methods=["GET"])
def get_temperature_logs():
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


@bp.route("/environment/light", methods=["POST"])
def log_light_state():
    payload = request.get_json(force=True)
    raw_state = payload.get("state")
    state = normalize_light_state(raw_state)

    if state is None:
        return jsonify({"ok": False, "error": "state must be 0 or 1"}), 400

    db = get_db()
    db.execute(
        "INSERT INTO light_log (state) VALUES (?)",
        (state,)
    )
    db.execute(
        "UPDATE tank_status SET light_state = ? WHERE id = 1",
        (state,)
    )
    db.commit()

    return jsonify({"ok": True, "state": state})


@bp.route("/environment/light/latest", methods=["GET"])
def latest_light_state():
    db = get_db()
    row = db.execute(
        """
        SELECT state, recorded_at
        FROM light_log
        ORDER BY recorded_at DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return jsonify({"ok": True, "latest": None})
    return jsonify({"ok": True, "latest": dict(row)})


@bp.route("/environment/light/on", methods=["POST"])
def turn_light_on():
    if not ARDUINO_BASE_URL:
        return jsonify({"status": "arduino base url is not configured"}), 500

    try:
        light_request = requests.get(f"{ARDUINO_BASE_URL}/light/on")

        if (light_request.status_code == 200):
            return jsonify({"status": "light on"})
        else:
            return jsonify({"status": "response was found but failed. check arduino "}), 500
    except requests.exceptions.RequestException:
        return jsonify({"status": "light could not be detected"}), 500

@bp.route("/environment/light/off", methods=["POST"])
def turn_light_off():
    if not ARDUINO_BASE_URL:
        return jsonify({"status": "arduino base url is not configured"}), 500

    try:
        light_request = requests.get(f"{ARDUINO_BASE_URL}/light/off")

        if (light_request.status_code == 200):
            return jsonify({"status": "light off"})
        else:
            return jsonify({"status": "response was found but failed. check arduino "}), 500
    except requests.exceptions.RequestException:
        return jsonify({"status": "light could not be detected"}), 500


