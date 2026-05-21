from flask import Blueprint, jsonify, request

from db import get_db

bp = Blueprint("livestock", __name__)

LIVESTOCK_TYPES = {"fish", "shrimp", "snail", "other"}


def _row_to_dict(row):
    return dict(row) if row else None


def _parse_quantity(value, *, default=1):
    if value in (None, ""):
        return default

    try:
        quantity = int(value)
    except (TypeError, ValueError):
        return None

    if quantity <= 0:
        return None

    return quantity


def _normalize_livestock_type(value):
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        return None

    normalized = value.strip().lower()
    if normalized not in LIVESTOCK_TYPES:
        return None
    return normalized


@bp.route("/livestock", methods=["GET"])
def list_livestock():
    in_tank = request.args.get("in_tank", "true").strip().lower()
    current_only = in_tank not in ("false", "0", "all")

    db = get_db()
    if current_only:
        rows = db.execute(
            """
            SELECT id, common_name, species_name, livestock_type, quantity,
                   in_tank, added_at, removed_at, notes
            FROM livestock
            WHERE in_tank = 1
            ORDER BY common_name COLLATE NOCASE, id
            """
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT id, common_name, species_name, livestock_type, quantity,
                   in_tank, added_at, removed_at, notes
            FROM livestock
            ORDER BY in_tank DESC, common_name COLLATE NOCASE, id
            """
        ).fetchall()

    return jsonify({"ok": True, "livestock": [dict(row) for row in rows]})


@bp.route("/livestock", methods=["POST"])
def add_livestock():
    payload = request.get_json(force=True)
    common_name = (payload.get("common_name") or "").strip()
    if not common_name:
        return jsonify({"ok": False, "error": "common_name is required"}), 400

    quantity = _parse_quantity(payload.get("quantity"))
    if quantity is None:
        return jsonify({"ok": False, "error": "quantity must be a positive integer"}), 400

    livestock_type = _normalize_livestock_type(payload.get("livestock_type"))
    if payload.get("livestock_type") not in (None, "") and livestock_type is None:
        return jsonify({
            "ok": False,
            "error": "livestock_type must be fish, shrimp, snail, crab, coral, or other",
        }), 400

    species_name = payload.get("species_name")
    notes = payload.get("notes")

    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO livestock
            (common_name, species_name, livestock_type, quantity, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (common_name, species_name, livestock_type, quantity, notes),
    )
    db.commit()

    row = db.execute(
        """
        SELECT id, common_name, species_name, livestock_type, quantity,
               in_tank, added_at, removed_at, notes
        FROM livestock
        WHERE id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()

    return jsonify({"ok": True, "livestock": _row_to_dict(row)}), 201


@bp.route("/livestock/remove", methods=["POST"])
def remove_livestock():
    payload = request.get_json(force=True)
    livestock_id = payload.get("id")
    common_name = (payload.get("common_name") or "").strip()
    quantity = _parse_quantity(payload.get("quantity"), default=None)

    if quantity is None and payload.get("quantity") not in (None, ""):
        return jsonify({"ok": False, "error": "quantity must be a positive integer"}), 400

    db = get_db()
    if livestock_id not in (None, ""):
        row = db.execute(
            """
            SELECT id, common_name, species_name, livestock_type, quantity,
                   in_tank, added_at, removed_at, notes
            FROM livestock
            WHERE id = ? AND in_tank = 1
            """,
            (livestock_id,),
        ).fetchone()
    else:
        if not common_name:
            return jsonify({"ok": False, "error": "id or common_name is required"}), 400

        row = db.execute(
            """
            SELECT id, common_name, species_name, livestock_type, quantity,
                   in_tank, added_at, removed_at, notes
            FROM livestock
            WHERE lower(common_name) = lower(?) AND in_tank = 1
            ORDER BY id
            LIMIT 1
            """,
            (common_name,),
        ).fetchone()

    if row is None:
        return jsonify({"ok": False, "error": "No matching livestock found in tank"}), 404

    current = dict(row)
    remove_quantity = quantity or current["quantity"]

    if remove_quantity >= current["quantity"]:
        db.execute(
            """
            UPDATE livestock
            SET in_tank = 0, removed_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (current["id"],),
        )
    else:
        db.execute(
            """
            UPDATE livestock
            SET quantity = quantity - ?
            WHERE id = ?
            """,
            (remove_quantity, current["id"]),
        )
        db.execute(
            """
            INSERT INTO livestock
                (common_name, species_name, livestock_type, quantity, in_tank,
                 added_at, removed_at, notes)
            VALUES (?, ?, ?, ?, 0, ?, datetime('now', 'localtime'), ?)
            """,
            (
                current["common_name"],
                current["species_name"],
                current["livestock_type"],
                remove_quantity,
                current["added_at"],
                payload.get("notes") or current["notes"],
            ),
        )

    db.commit()

    active_rows = db.execute(
        """
        SELECT id, common_name, species_name, livestock_type, quantity,
               in_tank, added_at, removed_at, notes
        FROM livestock
        WHERE in_tank = 1
        ORDER BY common_name COLLATE NOCASE, id
        """
    ).fetchall()

    return jsonify({
        "ok": True,
        "removed": {
            "id": current["id"],
            "common_name": current["common_name"],
            "quantity": remove_quantity,
        },
        "livestock": [dict(row) for row in active_rows],
    })
