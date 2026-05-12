from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("water_parameters", __name__)

PARAMETER_FIELDS = ("ph", "ammonia", "nitrite", "nitrate", "gh", "kh", "tds")


def _parse_parameter(name, value):
    if value in (None, ""):
        return None

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None

    if name == "ph" and (parsed < 0 or parsed > 14):
        return None
    if name != "ph" and parsed < 0:
        return None

    return parsed


def _row_to_dict(row):
    return dict(row) if row else None


@bp.route("/water-parameters", methods=["GET"])
def list_water_parameters():
    limit = request.args.get("limit", "50")
    try:
        limit_i = max(1, min(200, int(limit)))
    except ValueError:
        return jsonify({"ok": False, "error": "limit must be an integer"}), 400

    db = get_db()
    rows = db.execute(
        """
        SELECT id, ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes
        FROM water_parameter_log
        ORDER BY tested_at DESC, id DESC
        LIMIT ?
        """,
        (limit_i,),
    ).fetchall()

    return jsonify([dict(row) for row in rows])


@bp.route("/water-parameters/latest", methods=["GET"])
def latest_water_parameters():
    db = get_db()
    row = db.execute(
        """
        SELECT id, ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes
        FROM water_parameter_log
        ORDER BY tested_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()

    return jsonify({"ok": True, "latest": _row_to_dict(row)})


@bp.route("/water-parameters", methods=["POST"])
def add_water_parameters():
    payload = request.get_json(force=True)
    values = {}

    for field in PARAMETER_FIELDS:
        raw_value = payload.get(field)
        parsed_value = _parse_parameter(field, raw_value)
        if raw_value not in (None, "") and parsed_value is None:
            if field == "ph":
                return jsonify({"ok": False, "error": "ph must be a number between 0 and 14"}), 400
            return jsonify({"ok": False, "error": f"{field} must be a non-negative number"}), 400
        values[field] = parsed_value

    if all(values[field] is None for field in PARAMETER_FIELDS):
        return jsonify({
            "ok": False,
            "error": "At least one water parameter is required",
        }), 400

    tested_at = payload.get("tested_at")
    notes = payload.get("notes")

    db = get_db()
    if tested_at:
        cursor = db.execute(
            """
            INSERT INTO water_parameter_log
                (ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["ph"],
                values["ammonia"],
                values["nitrite"],
                values["nitrate"],
                values["gh"],
                values["kh"],
                values["tds"],
                tested_at,
                notes,
            ),
        )
    else:
        cursor = db.execute(
            """
            INSERT INTO water_parameter_log
                (ph, ammonia, nitrite, nitrate, gh, kh, tds, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["ph"],
                values["ammonia"],
                values["nitrite"],
                values["nitrate"],
                values["gh"],
                values["kh"],
                values["tds"],
                notes,
            ),
        )
    db.commit()

    row = db.execute(
        """
        SELECT id, ph, ammonia, nitrite, nitrate, gh, kh, tds, tested_at, notes
        FROM water_parameter_log
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify({"ok": True, "water_parameters": dict(row)}), 201
