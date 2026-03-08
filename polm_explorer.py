#!/usr/bin/env python3

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080
DAG_FILE = "polm_dag.json"


def load_dag():

    if not os.path.exists(DAG_FILE):
        return []

    try:
        with open(DAG_FILE) as f:
            return json.load(f)
    except:
        return []


def miner_stats(dag):

    stats = {}

    for block in dag:

        if block.get("hash") == "genesis":
            continue

        miner = block.get("miner","unknown")

        if miner not in stats:
            stats[miner] = {"blocks":0,"score":0}

        stats[miner]["blocks"] += 1
        stats[miner]["score"] += block.get("score",0)

    ranking = []

    for miner,data in stats.items():

        avg = data["score"] / data["blocks"]

        ranking.append({
            "miner":miner,
            "blocks":data["blocks"],
            "avg_score":avg
        })

    ranking.sort(key=lambda x: x["blocks"], reverse=True)

    return ranking


def build_tree(dag):

    tree = {}

    for block in dag:

        h = block["hash"]

        if h not in tree:
            tree[h] = []

        for parent in block.get("parents",[]):

            if parent not in tree:
                tree[parent] = []

            tree[parent].append(h)

    return tree


def render_tree(node,tree,depth=0):

    html = "&nbsp;" * depth * 4 + node[:8] + "<br>"

    for child in tree.get(node,[]):

        html += render_tree(child,tree,depth+1)

    return html


class Explorer(BaseHTTPRequestHandler):

    def do_GET(self):

        dag = load_dag()

        ranking = miner_stats(dag)

        tree = build_tree(dag)

        html = """
        <html>
        <head>
        <title>PoLM Explorer</title>
        <meta http-equiv="refresh" content="5">
        <style>
        body{font-family:Arial;background:#111;color:#eee}
        table{border-collapse:collapse;width:100%}
        th,td{border:1px solid #444;padding:8px;text-align:center}
        th{background:#222}
        h1{color:#00ff99}
        .dag{font-family:monospace;background:#000;padding:20px}
        </style>
        </head>
        <body>
        """

        html += "<h1>PoLM Network Explorer</h1>"

        html += "<h2>Total Blocks: "+str(len(dag))+"</h2>"

        html += "<h2>Top Miners</h2>"

        html += "<table>"
        html += "<tr><th>Rank</th><th>Miner</th><th>Blocks</th><th>Avg Score</th></tr>"

        rank = 1

        for m in ranking:

            html += "<tr>"
            html += "<td>"+str(rank)+"</td>"
            html += "<td>"+m["miner"][:12]+"</td>"
            html += "<td>"+str(m["blocks"])+"</td>"
            html += "<td>"+str(round(m["avg_score"],2))+"</td>"
            html += "</tr>"

            rank += 1

        html += "</table>"

        html += "<h2>Recent Blocks</h2>"

        html += "<table>"
        html += "<tr><th>Hash</th><th>Miner</th><th>Score</th><th>Latency</th><th>RAM</th></tr>"

        for block in reversed(dag[-20:]):

            if block.get("hash") == "genesis":
                continue

            html += "<tr>"
            html += "<td>"+block["hash"][:12]+"</td>"
            html += "<td>"+block["miner"][:12]+"</td>"
            html += "<td>"+str(round(block["score"],2))+"</td>"
            html += "<td>"+str(round(block["latency"],3))+"</td>"
            html += "<td>"+block["ram"]+"</td>"
            html += "</tr>"

        html += "</table>"

        html += "<h2>DAG Structure</h2>"

        html += "<div class='dag'>"

        html += render_tree("genesis",tree)

        html += "</div>"

        html += "</body></html>"

        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.end_headers()

        self.wfile.write(html.encode())


print("PoLM Explorer DAG running on port",PORT)

server = HTTPServer(("0.0.0.0",PORT),Explorer)

server.serve_forever()
