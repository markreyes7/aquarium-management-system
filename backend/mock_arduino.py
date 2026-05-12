from flask import Flask, jsonify, request

app = Flask(__name__)

light_state = "off"


@app.route("/temp", methods=["GET"])
def temp():
    return jsonify({"temperature": 72.4})


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


@app.route("/topoff", methods=["GET"])
def topoff():
    seconds = request.args.get("seconds", "0")
    return jsonify({"ok": True, "seconds": seconds})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3999, debug=True)
