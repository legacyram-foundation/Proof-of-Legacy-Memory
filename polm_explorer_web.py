#!/usr/bin/env python3

import json
from flask import Flask, render_template_string

CHAIN_FILE="polm_chain.json"

app = Flask(__name__)

HTML="""
<html>
<head>
<title>PoLM Explorer</title>

<style>

body{
font-family:Arial;
background:#111;
color:white;
margin:40px;
}

h1{
color:#00ff9c;
}

.block{
background:#222;
padding:15px;
margin-bottom:10px;
border-radius:8px;
}

.hash{
color:#00ff9c;
}

</style>

</head>

<body>

<h1>PoLM Blockchain Explorer</h1>

<p>Height: {{height}}</p>

{% for b in blocks %}

<div class="block">

Height: {{b.height}} <br>
Hash: <span class="hash">{{b.hash}}</span><br>
Miner: {{b.miner}} <br>
Reward: {{b.reward}} <br>
TX count: {{b.transactions|length}}

</div>

{% endfor %}

</body>
</html>
"""

def load_chain():

    try:
        with open(CHAIN_FILE) as f:
            return json.load(f)
    except:
        return []

@app.route("/")

def index():

    chain=load_chain()

    blocks=list(reversed(chain[-20:]))

    return render_template_string(

        HTML,
        blocks=blocks,
        height=len(chain)-1
    )

app.run(host="0.0.0.0",port=8080)
