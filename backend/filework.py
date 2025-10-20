from flask import Flask, jsonify, request, json

#TODO: read from files. write from files


def open_file(path):
    with open(path, 'r') as f:
        return json.load(f)

def write_file(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_data(opened_file):
    print(opened_file)
    
