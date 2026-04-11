import os

import requests
from flask import Blueprint, jsonify, request
from db import get_db
from light_state import normalize_light_state, record_light_state

bp = Blueprint("environment", __name__)


def get_arduino_base_url():
    return "http://192.168.1.100"

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
    state = record_light_state(raw_state)

    if state is None:
        return jsonify({"ok": False, "error": "state must be 0 or 1"}), 400

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


@bp.route("/environment/light/status", methods=["GET"])
def current_light_status():
    db = get_db()
    row = db.execute(
        "SELECT light_state FROM tank_status WHERE id = 1"
    ).fetchone()

    if row is None or row["light_state"] is None:
        return jsonify({"ok": True, "status": None, "state": None})

    state = row["light_state"]
    return jsonify({
        "ok": True,
        "status": "on" if state == 1 else "off",
        "state": state
    })


@bp.route("/environment/light/currentStatus", methods=["GET"])
def light_current_status():
    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return jsonify({
            "ok": False,
            "error": "ARDUINO_BASE_URL is not configured"
        }), 500

    try:
        light_request = requests.get(f"{arduino_base_url}/light/currentStatus", timeout=5)

        if light_request.status_code == 200:
            payload = light_request.json()
            return jsonify({"status": payload.get("status")})

        return jsonify({
            "ok": False,
            "error": "Arduino returned a non-200 response",
            "arduino_status_code": light_request.status_code,
            "arduino_response": light_request.text,
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Could not reach Arduino",
            "details": str(exc),
        }), 502


@bp.route("/environment/light/on", methods=["POST"])
def turn_light_on():
    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return jsonify({
            "ok": False,
            "error": "ARDUINO_BASE_URL is not configured"
        }), 500

    try:
        light_request = requests.get(f"{arduino_base_url}/light/on", timeout=5)

        if light_request.status_code == 200:
            state = record_light_state(1)
            return jsonify({"ok": True, "status": "light on", "state": state})

        return jsonify({
            "ok": False,
            "error": "Arduino returned a non-200 response",
            "arduino_status_code": light_request.status_code,
            "arduino_response": light_request.text,
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Could not reach Arduino",
            "details": str(exc),
        }), 502

@bp.route("/environment/light/off", methods=["POST"])
def turn_light_off():
    arduino_base_url = get_arduino_base_url()
    if not arduino_base_url:
        return jsonify({
            "ok": False,
            "error": "ARDUINO_BASE_URL is not configured"
        }), 500

    try:
        light_request = requests.get(f"{arduino_base_url}/light/off", timeout=5)

        if light_request.status_code == 200:
            state = record_light_state(0)
            return jsonify({"ok": True, "status": "light off", "state": state})

        return jsonify({
            "ok": False,
            "error": "Arduino returned a non-200 response",
            "arduino_status_code": light_request.status_code,
            "arduino_response": light_request.text,
        }), 502
    except requests.exceptions.RequestException as exc:
        return jsonify({
            "ok": False,
            "error": "Could not reach Arduino",
            "details": str(exc),
        }), 502
