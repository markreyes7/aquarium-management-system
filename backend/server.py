from flask import Flask, jsonify, request
import filework

app = Flask(__name__)

# --- Global Variables ---
light_on = False  # ✅ initialize this so /light/status works

welcomemessage = "Welcome to the best aquarium API"

# --- Sample data ---
items = [
    {"value": 1, "name": "Stuff", "unit": "ppm"},
    {"value": 2, "name": "Item B"}
]

# --- Routes ---
@app.route('/', methods=['GET'])
def welcome():
    print("Welcome to the best aquarium API")
    return welcomemessage


@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(items)


@app.route('/data', methods=['GET'])
def get_data():
    """Return full aquarium dataset (pH, TDS, temperature, etc.)"""
    data = filework.open_file('aquariumdata.json')
    return jsonify(data)


@app.route('/temp', methods=['GET'])
def get_temp():
    """Return only the current temperature"""
    data = filework.open_file('aquariumdata.json')
    return jsonify({"temperature": data.get("temperature", None)})


@app.route('/update/temp', methods=['POST'])
def update_temp():
    """Update temperature value in the JSON file"""
    payload = request.get_json(force=True)
    new_temp = payload.get("temperature")

    if new_temp is None:
        return jsonify({"ok": False, "error": "Missing temperature"}), 400

    # Read, update, and save back
    data = filework.open_file('aquariumdata.json')
    data["temperature"] = new_temp
    filework.write_file('aquariumdata.json', data)

    return jsonify({"ok": True, "temperature": new_temp})


@app.route("/light/status", methods=["GET"])
def light_status():
    """Return light ON/OFF state"""
    return jsonify({"on": light_on})


@app.route("/light/toggle", methods=["POST"])
def toggle_light():
    """Toggle light ON/OFF state"""
    global light_on
    data = request.get_json(force=True)

    desired = data.get("desired")
    if desired is None:
        return jsonify({"ok": False, "error": "Missing 'desired' field"}), 400

    # Here’s where hardware control would go (GPIO, relay, etc.)
    light_on = bool(desired)
    print(f"Light state updated to: {light_on}")

    return jsonify({"ok": True, "on": light_on})


if __name__ == "__main__":
    # Run with: python3 server.py
    app.run(host="0.0.0.0", port=3001, debug=True)
