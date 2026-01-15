from flask import Blueprint, jsonify
from db import get_db

bp = Blueprint("maintenance", __name__)

@bp.route("/", methods=["GET"])
def welcome():
    return "Welcome to the best aquarium API"

@bp.route("/data", methods=["GET"])
def get_data():
    db = get_db()
    row = db.execute(
        "SELECT * FROM tank_status WHERE id = 1"
    ).fetchone()

    return jsonify(dict(row))

@bp.route("/update/fertilize", methods=["POST"])
def update_fertilized():
    db = get_db()
    db.execute("""
        UPDATE tank_status
        SET last_fertilized = CURRENT_TIMESTAMP
        WHERE id = 1
    """)
    db.commit()

    return jsonify({"ok": True})

@bp.route("/update/trimmed", methods=["POST"])
def update_trimmed():
    db = get_db()
    db.execute("""
        UPDATE tank_status
        SET last_trimmed = CURRENT_TIMESTAMP
        WHERE id = 1
    """)
    db.commit()

    return jsonify({"ok": True})

@bp.route("/update/topoff", methods=["POST"])
def update_topoff():
    db = get_db()
    db.execute("""
            UPDATE tank_status
            SET last_water_topoff = CURRENT_TIMESTAMP
            where id = 1       
    """)
    db.commit()

    return jsonify({"ok": True})    