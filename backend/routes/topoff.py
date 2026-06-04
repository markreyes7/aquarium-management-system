from __future__ import annotations

from flask import Blueprint, jsonify, request

from db import get_db
from topoff import (
    fetch_arduino_topoff_status,
    finalize_topoff_event,
    format_topoff_timestamp,
    get_last_topoff_timestamp,
    get_topoff_status_snapshot,
    mark_topoff_complete,
    parse_topoff_duration,
    record_topoff_event,
    run_topoff_hardware,
)

bp = Blueprint("topoff", __name__)


@bp.route("/topoff", methods=["GET"])
def topoff_status():
    snapshot = get_topoff_status_snapshot()
    arduino_status, arduino_error = fetch_arduino_topoff_status()

    return jsonify({
        "ok": True,
        "topoff": snapshot,
        "arduino": {
            "ok": arduino_error is None,
            "status": arduino_status,
            "error": arduino_error,
        },
    })


@bp.route("/topoff/manual", methods=["POST"])
@bp.route("/update/topoff", methods=["POST"])
def update_manual_topoff():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes")

    record_topoff_event(
        source="manual",
        requested_seconds=None,
        status="completed",
        notes=notes,
        arduino_response="manual topoff recorded",
        completed=True,
    )
    mark_topoff_complete(action="topoff", notes=notes)
    get_db().commit()

    return jsonify({
        "ok": True,
        "action": "topoff",
        "notes": notes,
        "last_topoff": format_topoff_timestamp(get_last_topoff_timestamp()),
    })


@bp.route("/topoff/run", methods=["POST"])
@bp.route("/update/runtopoff", methods=["POST"])
def run_topoff():
    payload = request.get_json(silent=True) or {}
    notes = payload.get("notes")
    duration = parse_topoff_duration(payload.get("seconds"))
    last_topoff = get_last_topoff_timestamp()
    formatted_last_topoff = format_topoff_timestamp(last_topoff)

    if duration is None:
        return jsonify({
            "ok": False,
            "error": "seconds must be a number between 1 and 5",
            "last_topoff": formatted_last_topoff,
        }), 400

    event_id = record_topoff_event(
        source="pump",
        requested_seconds=duration,
        status="requested",
        notes=notes,
    )
    run_result = run_topoff_hardware(duration)

    if not run_result.ok:
        finalize_topoff_event(
            event_id,
            status="failed",
            arduino_response=_stringify_payload(
                run_result.arduino_response,
                run_result.details,
            ),
        )
        get_db().commit()
        return jsonify({
            "ok": False,
            "error": run_result.error,
            "details": run_result.details,
            "arduino_status_code": run_result.arduino_status_code,
            "arduino_response": run_result.arduino_response,
            "last_topoff": formatted_last_topoff,
        }), run_result.status_code

    mark_topoff_complete(action="runtopoff", notes=notes)
    finalize_topoff_event(
        event_id,
        status="completed",
        arduino_response=_stringify_payload(
            run_result.final_status or run_result.arduino_response
        ),
    )
    get_db().commit()

    return jsonify({
        "ok": True,
        "action": "runtopoff",
        "notes": notes,
        "seconds": duration,
        "arduino_response": run_result.arduino_response,
        "arduino_status": run_result.final_status,
        "last_topoff_before_update": formatted_last_topoff,
        "last_topoff": format_topoff_timestamp(get_last_topoff_timestamp()),
    })


def _stringify_payload(payload, details=None) -> str | None:
    if payload is None and details is None:
        return None
    if details and payload is None:
        return details
    if isinstance(payload, str):
        return payload
    return str(payload)
