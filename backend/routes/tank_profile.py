from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("tank_profile", __name__)

WATER_TYPES = {"freshwater", "saltwater", "brackish"}
PROFILE_FIELDS = (
    "size_gallons",
    "water_type",
    "target_temperature_min",
    "target_temperature_max",
    "lighting_schedule",
    "setup_date",
    "notes",
)


def _row_to_dict(row):
    return dict(row) if row else None


def _parse_positive_float(name, value):
    if value in (None, ""):
        return None

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None

    if parsed <= 0:
        return None

    return parsed


def _parse_float(name, value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_water_type(value):
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    if normalized not in WATER_TYPES:
        return None
    return normalized


def _validate_payload(payload):
    values = {}

    if "size_gallons" in payload:
        values["size_gallons"] = _parse_positive_float(
            "size_gallons",
            payload.get("size_gallons"),
        )
        if payload.get("size_gallons") not in (None, "") and values["size_gallons"] is None:
            return None, "size_gallons must be a positive number"

    if "water_type" in payload:
        values["water_type"] = _normalize_water_type(payload.get("water_type"))
        if payload.get("water_type") not in (None, "") and values["water_type"] is None:
            return None, "water_type must be freshwater, saltwater, or brackish"

    for field in ("target_temperature_min", "target_temperature_max"):
        if field in payload:
            values[field] = _parse_float(field, payload.get(field))
            if payload.get(field) not in (None, "") and values[field] is None:
                return None, f"{field} must be a number"

    for field in ("lighting_schedule", "setup_date", "notes"):
        if field in payload:
            values[field] = payload.get(field)

    min_temp = values.get("target_temperature_min")
    max_temp = values.get("target_temperature_max")
    if min_temp is not None and max_temp is not None and min_temp > max_temp:
        return None, "target_temperature_min cannot be greater than target_temperature_max"

    return values, None


@bp.route("/tank-profile", methods=["GET"])
def get_tank_profile():
    db = get_db()
    db.execute("INSERT OR IGNORE INTO tank_profile (id) VALUES (1)")
    db.commit()

    row = db.execute(
        """
        SELECT id, size_gallons, water_type, target_temperature_min,
               target_temperature_max, lighting_schedule, setup_date, notes,
               updated_at
        FROM tank_profile
        WHERE id = 1
        """
    ).fetchone()

    return jsonify({"ok": True, "tank_profile": _row_to_dict(row)})


@bp.route("/tank-profile", methods=["PUT", "PATCH"])
def update_tank_profile():
    payload = request.get_json(force=True)
    values, error = _validate_payload(payload)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    if not values:
        return jsonify({"ok": False, "error": "At least one profile field is required"}), 400

    assignments = [f"{field} = ?" for field in values]
    assignments.append("updated_at = datetime('now', 'localtime')")

    db = get_db()
    db.execute("INSERT OR IGNORE INTO tank_profile (id) VALUES (1)")
    db.execute(
        f"""
        UPDATE tank_profile
        SET {", ".join(assignments)}
        WHERE id = 1
        """,
        tuple(values.values()),
    )
    db.commit()

    row = db.execute(
        """
        SELECT id, size_gallons, water_type, target_temperature_min,
               target_temperature_max, lighting_schedule, setup_date, notes,
               updated_at
        FROM tank_profile
        WHERE id = 1
        """
    ).fetchone()

    return jsonify({"ok": True, "tank_profile": _row_to_dict(row)})
