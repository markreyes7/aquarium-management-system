from flask import Blueprint, jsonify, request
from db import get_db

bp = Blueprint("environment", __name__)

@bp.route("/temp", methods=["GET"])
def get_temp():
    db = get_db()
    row = db.execute("""
        SELECT temperature
        FROM temperature_log
        ORDER BY recorded_at DESC
        LIMIT 1
    """).fetchone()

    return jsonify({"temperature": row["temperature"] if row else None})

@bp.route("/update/temp", methods=["POST"])
def update_temp():
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

    return jsonify({"ok": True, "temperature": temp})