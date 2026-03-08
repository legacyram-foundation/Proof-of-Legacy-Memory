#!/usr/bin/env python3

import time
import random
import hashlib
import threading
import json
import os

DAG_FILE = "polm_dag.json"

MEMORY_SIZE = 64 * 1024 * 1024
BUFFER = bytearray(MEMORY_SIZE)

GRAPH_SIZE = 100000

dag_lock = threading.Lock()

# ---------------- HARDWARE PROFILES ----------------

nodes = [

{"name":"node_ddr2_A","ram":"DDR2","mult":2.5},
{"name":"node_ddr2_B","ram":"DDR2","mult":2.5},

{"name":"node_ddr3_A","ram":"DDR3","mult":1.8},

{"name":"node_ddr4_A","ram":"DDR4","mult":1.0},
{"name":"node_ddr4_B","ram":"DDR4","mult":1.0},

]


# ---------------- DAG ----------------

def load_dag():

    with dag_lock:

        if not os.path.exists(DAG_FILE):

            genesis = {
                "hash":"genesis",
                "parents":[]
            }

            with open(DAG_FILE,"w") as f:
                json.dump([genesis],f)

        try:
            with open(DAG_FILE) as f:
                return json.load(f)
        except:
            return []


def save_dag(dag):

    with dag_lock:

        with open(DAG_FILE,"w") as f:
            json.dump(dag,f)


def select_parents(dag):

    if len(dag) <= 2:
        return ["genesis"]

    parents = random.sample(dag[-5:],2)

    return [p["hash"] for p in parents]


# ---------------- MEMORY STORM ----------------

def memory_storm(seed):

    pointer = seed % MEMORY_SIZE

    total = 0

    start = time.perf_counter()

    for _ in range(GRAPH_SIZE):

        pointer = (pointer * 1103515245 + 12345) % MEMORY_SIZE

        value = BUFFER[pointer]

        total ^= value

    latency = time.perf_counter() - start

    return total,latency


# ---------------- MINER ----------------

def miner(node):

    name = node["name"]
    ram = node["ram"]
    mult = node["mult"]

    while True:

        dag = load_dag()

        parents = select_parents(dag)

        seed = random.randint(0,2**32)

        work,lat = memory_storm(seed)

        score = lat * 100 * mult

        if score < 1:
            score = 1

        if score > 120:
            score = 120

        data = str(seed + work).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < 2**248:

            with dag_lock:

                dag = load_dag()

                block = {

                    "hash":h,
                    "parents":parents,
                    "miner":name,
                    "ram":ram,
                    "latency":lat,
                    "score":score,
                    "timestamp":time.time()

                }

                dag.append(block)

                save_dag(dag)

                print(
                    "BLOCK",
                    h[:8],
                    "|",
                    name,
                    "| RAM:",
                    ram,
                    "| score:",
                    round(score,2)
                )


# ---------------- START ----------------

print("===== PoLM Network Simulator =====")

load_dag()

for node in nodes:

    t = threading.Thread(target=miner,args=(node,))
    t.daemon = True
    t.start()

while True:
    time.sleep(5)

    dag = load_dag()

    print("TOTAL BLOCKS:",len(dag))
