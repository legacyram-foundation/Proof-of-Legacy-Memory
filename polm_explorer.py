import json
from flask import Flask, jsonify

app=Flask(__name__)

with open("blockchain.json") as f:
    chain=json.load(f)

@app.route("/blocks")
def blocks():
    return jsonify(chain)

@app.route("/height")
def height():
    return jsonify({"height":len(chain)})

app.run(port=8081)
