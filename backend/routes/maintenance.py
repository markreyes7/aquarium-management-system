from flask import Blueprint, jsonify, request
from db import get_db

bp = Blueprint("maintenance", __name__)


# i just like this to check if server is up
@bp.route("/", methods=["GET"])
def welcome():
    return "Welcome to the best aquarium API"

# this is for checking everything related to the aquarium. not optimal or maybe not necessary but i will leave it
@bp.route("/data", methods=["GET"])
def get_data():
    db = get_db()
    row = db.execute("SELECT * FROM tank_status WHERE id = 1").fetchone()
    data = dict(row) if row else {}

    tank_profile_row = db.execute(
        """
        SELECT id, size_gallons, water_type, target_temperature_min,
               target_temperature_max, lighting_schedule, setup_date, notes,
               updated_at
        FROM tank_profile
        WHERE id = 1
        """
    ).fetchone()
    data["tank_profile"] = dict(tank_profile_row) if tank_profile_row else None

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

    latest_temperature_row = db.execute(
        """
        SELECT temperature, recorded_at
        FROM temperature_log
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()
    data["latest_temperature"] = (
        dict(latest_temperature_row) if latest_temperature_row else None
    )

    latest_light_row = db.execute(
        """
        SELECT state, recorded_at
        FROM light_log
        ORDER BY recorded_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if latest_light_row:
        latest_light = dict(latest_light_row)
        latest_light["status"] = "on" if latest_light["state"] == 1 else "off"
        data["latest_light"] = latest_light
    else:
        data["latest_light"] = None

    plant_summary_row = db.execute(
        """
        SELECT
            COUNT(*) AS total_plants,
            SUM(CASE WHEN in_tank = 1 THEN 1 ELSE 0 END) AS plants_in_tank
        FROM plants
        """
    ).fetchone()
    data["plant_summary"] = {
        "total_plants": plant_summary_row["total_plants"] if plant_summary_row else 0,
        "plants_in_tank": plant_summary_row["plants_in_tank"] if plant_summary_row and plant_summary_row["plants_in_tank"] is not None else 0,
    }

    livestock_rows = db.execute(
        """
        SELECT id, common_name, quantity
        FROM livestock
        WHERE in_tank = 1
        ORDER BY common_name COLLATE NOCASE, id
        """
    ).fetchall()
    data["livestock"] = [dict(row) for row in livestock_rows]

    maintenance_summary_row = db.execute(
        """
        SELECT COUNT(*) AS total_maintenance_events
        FROM maintenance_log
        """
    ).fetchone()
    data["maintenance_summary"] = {
        "total_events": maintenance_summary_row["total_maintenance_events"]
        if maintenance_summary_row
        else 0
    }

    recent_maintenance_rows = db.execute(
        """
        SELECT action, occurred_at, notes
        FROM maintenance_log
        ORDER BY occurred_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()
    data["recent_maintenance"] = [dict(row) for row in recent_maintenance_rows]

    latest_water_parameters_row = db.execute(
        """
        SELECT id, ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes
        FROM water_parameter_log
        ORDER BY tested_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    data["latest_water_parameters"] = (
        dict(latest_water_parameters_row) if latest_water_parameters_row else None
    )

    recent_water_parameter_rows = db.execute(
        """
        SELECT id, ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes
        FROM water_parameter_log
        ORDER BY tested_at DESC, id DESC
        LIMIT 5
        """
    ).fetchall()
    data["recent_water_parameters"] = [
        dict(row) for row in recent_water_parameter_rows
    ]

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
    db.execute(
        """
        INSERT INTO maintenance_log (action, occurred_at, notes)
        VALUES (?, datetime('now', 'localtime'), ?)
        """,
        (action, notes),
    )

@bp.route("/update/fertilize", methods=["POST"])
def update_fertilized():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes")  # optional

    db = get_db()

    # update current status of tank
    db.execute(
        """
        UPDATE tank_status
        SET last_fertilized = datetime('now', 'localtime')
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
        SET last_trimmed = datetime('now', 'localtime')
        WHERE id = 1
        """
    )

    _log_action("trimmed", notes)
    db.commit()

    return jsonify({"ok": True, "action": "trimmed", "notes": notes})
