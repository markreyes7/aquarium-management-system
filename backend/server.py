from flask import Flask, jsonify, request, json
import filework

app = Flask(__name__)

# Sample data (e.g., a list of items)
items = [
    {"value": 1, "name": "Stuff", "unit": "ppm"},
    {"value": 2, "name": "Item B"}
]

welcomemessage = "Welcome to the best aquarium api"

# Define API routes
@app.route('/', methods=['GET'])
def welcome():
    print("Welcom to the best aquarium api")
    return welcomemessage

# GET all items
@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(items)

@app.route('/data',methods=['GET'])
def get_data():
    return filework.open_file('backend/aquariumdata.json')

@app.route('/temp',methods=['GET'])
def get_temp():
    data = filework.open_file('backend/aquariumdata.json')
    print(data["temperature"])
    return jsonify({"temperature": data["temperature"]})

@app.route('/update/temp', methods=['POST'])
def update_temp():
    payload = request.get_json(force=True)
    new_temp = payload.get("temperature")

    if new_temp is None:
        return jsonify({"ok": False, "error": "Missing temperature"}), 400
    
   
    # Read existing data
    data = filework.open_file('backend/aquariumdata.json')
    data["temperature"] = new_temp

    # Save back
    filework.write_file('backend/aquariumdata.json', data)

    return jsonify({"ok": True, "temperature": new_temp})



# app.route('updateTemp', methods=['POST'])
# def update_temp():


if __name__ == "__main__":
    # run with: python3 server.py
    app.run(host="0.0.0.0", port=3001, debug=True)