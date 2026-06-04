from flask import Flask, jsonify, request

app = Flask(__name__)

light_state = "off"
topoff_state = {
    "active": False,
    "last_requested_seconds": None,
    "last_completed_seconds": None,
}


@app.route("/temp", methods=["GET"])
def temp():
    return jsonify({"temperature": 72.4})


@app.route("/ph", methods=["GET"])
def ph():
    return jsonify({"ph": 7.2})


@app.route("/light/currentStatus", methods=["GET"])
def light_current_status():
    return jsonify({"status": light_state})


@app.route("/light/on", methods=["GET"])
def light_on():
    global light_state
    light_state = "on"
    return jsonify({"status": light_state})


@app.route("/light/off", methods=["GET"])
def light_off():
    global light_state
    light_state = "off"
    return jsonify({"status": light_state})


@app.route("/light/auto", methods=["GET"])
def light_auto():
    return jsonify({"status": light_state, "mode": "auto"})


@app.route("/topoff/status", methods=["GET"])
def topoff_status():
    return jsonify({
        "ok": True,
        "active": topoff_state["active"],
        "last_requested_seconds": topoff_state["last_requested_seconds"],
        "last_completed_seconds": topoff_state["last_completed_seconds"],
    })


@app.route("/topoff/run", methods=["GET"])
@app.route("/topoff", methods=["GET"])
def topoff_run():
    seconds = request.args.get("seconds", "0")
    try:
        parsed = float(seconds)
    except ValueError:
        return jsonify({"ok": False, "error": "invalid seconds"}), 400

    if parsed <= 0 or parsed > 5:
        return jsonify({"ok": False, "error": "seconds must be between 1 and 5"}), 400

    topoff_state["active"] = False
    topoff_state["last_requested_seconds"] = parsed
    topoff_state["last_completed_seconds"] = parsed
    return jsonify({
        "ok": True,
        "active": False,
        "requested_seconds": parsed,
        "completed_seconds": parsed,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3999, debug=True)
