from flask import Flask, jsonify, request, json

app = Flask(__name__)

# Sample data (e.g., a list of items)
items = [
    {"value": 1, "name": "Fuck", "unit": "ppm"},
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

@app.route('/getData',methods=['GET'])
def get_data():
    open_file = open('backend/aquariumdata.json')
    data = json.load(open_file)
    return data

if __name__ == "__main__":
    # run with: python3 server.py
    app.run(host="0.0.0.0", port=3000, debug=True)