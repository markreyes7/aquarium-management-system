from flask import Blueprint, jsonify, request
from db import get_db

bp = Blueprint("maintenance", __name__)

# Optional: keep welcome route if you want
@bp.route("/", methods=["GET"])
def welcome():
    return "Welcome to the best aquarium API"


@bp.route("/data", methods=["GET"])
def get_data():
    db = get_db()
    row = db.execute("SELECT * FROM tank_status WHERE id = 1").fetchone()
    return jsonify(dict(row) if row else {})


# ----------------------------
# New: log endpoints (what you want)
# ----------------------------
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
        SELECT id, action, occurred_at, note
        FROM maintenance_log
        ORDER BY occurred_at DESC
        LIMIT ?
        """,
        (limit_i,)
    ).fetchall()

    return jsonify([dict(r) for r in rows])


@bp.route("/maintenance", methods=["POST"])
def add_maintenance():
    """
    JSON:
      - action (required) e.g. fertilize, trimmed, topoff, water_change
      - note (optional)
    """
    payload = request.get_json(force=True)
    action = payload.get("action")
    note = payload.get("note")

    if not action:
        return jsonify({"ok": False, "error": "Missing action"}), 400

    action = action.strip().lower()

    db = get_db()
    db.execute(
        "INSERT INTO maintenance_log (action, note) VALUES (?, ?)",
        (action, note)
    )
    db.commit()

    return jsonify({"ok": True, "action": action})


# ----------------------------
# Legacy endpoints (keep working) + add log writes
# ----------------------------
def _log_action(action: str, note: str | None = None) -> None:
    db = get_db()
    db.execute("INSERT INTO maintenance_log (action, note) VALUES (?, ?)", (action, note))


@bp.route("/update/fertilize", methods=["POST"])
def update_fertilized():
    db = get_db()

    db.execute(
        """
        UPDATE tank_status
        SET last_fertilized = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("fertilize")
    db.commit()

    return jsonify({"ok": True})


@bp.route("/update/trimmed", methods=["POST"])
def update_trimmed():
    db = get_db()

    db.execute(
        """
        UPDATE tank_status
        SET last_trimmed = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("trimmed")
    db.commit()

    return jsonify({"ok": True})


@bp.route("/update/topoff", methods=["POST"])
def update_topoff():
    db = get_db()

    db.execute(
        """
        UPDATE tank_status
        SET last_water_topoff = CURRENT_TIMESTAMP
        WHERE id = 1
        """
    )

    _log_action("topoff")
    db.commit()

    return jsonify({"ok": True})
