#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading
import platform
import subprocess

PORT = 5001

PEERS = [
"192.168.0.100",
"192.168.0.103",
"192.168.0.102"
]

DAG_FILE = "polm_dag.json"

MEMORY_SIZE = 512 * 1024 * 1024
BUFFER = bytearray(MEMORY_SIZE)

GRAPH_SIZE = 200000

BLOCK_REWARD = 50
MAX_THREADS = 2

dag_lock = threading.Lock()
mine_lock = threading.Lock()


# ---------------- RAM DETECTION ----------------

def detect_ram():

    try:

        out = subprocess.check_output(
            "sudo dmidecode -t memory | grep 'Type:'",
            shell=True
        ).decode()

        if "DDR2" in out:
            return "DDR2",2.5

        if "DDR3" in out:
            return "DDR3",1.8

        if "DDR4" in out:
            return "DDR4",1.0

        if "DDR5" in out:
            return "DDR5",0.7

    except:
        pass

    return "UNKNOWN",1.0


RAM_TYPE,RAM_MULT = detect_ram()

print("===== PoLM Node v13 (DAG Mining) =====")
print("CPU:", platform.processor())
print("Cores:", os.cpu_count())
print("RAM:", RAM_TYPE)


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


def latency_score(latency):

    score = latency * 100 * RAM_MULT

    if score < 1:
        score = 1

    if score > 120:
        score = 120

    return score


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


# ---------------- NETWORK ----------------

def broadcast(block):

    for peer in PEERS:

        try:

            s = socket.socket()
            s.connect((peer,PORT))
            s.send(json.dumps(block).encode())
            s.close()

        except:
            pass


def server():

    s = socket.socket()

    s.bind(("0.0.0.0",PORT))

    s.listen()

    while True:

        conn,addr = s.accept()

        try:

            data = conn.recv(4096)

            block = json.loads(data.decode())

            dag = load_dag()

            dag.append(block)

            save_dag(dag)

            print("BLOCK RECEIVED",block["hash"][:8])

        except:
            pass

        conn.close()


# ---------------- MINER ----------------

def miner_thread(address):

    while True:

        dag = load_dag()

        parents = select_parents(dag)

        seed = random.randint(0,2**32)

        work,latency = memory_storm(seed)

        score = latency_score(latency)

        data = str(seed + work).encode()

        h = hashlib.sha256(data).hexdigest()

        if int(h,16) < 2**244:

            with mine_lock:

                dag = load_dag()

                block = {

                    "hash":h,
                    "parents":parents,
                    "timestamp":time.time(),
                    "seed":seed,
                    "latency":latency,
                    "score":score,
                    "miner":address,
                    "ram":RAM_TYPE
                }

                dag.append(block)

                save_dag(dag)

                print(
                    "BLOCK",
                    h[:8],
                    "| score:",
                    round(score,2),
                    "| RAM:",
                    RAM_TYPE
                )

                broadcast(block)


def start_mining(address):

    for _ in range(MAX_THREADS):

        t = threading.Thread(
            target=miner_thread,
            args=(address,)
        )

        t.daemon = True
        t.start()

    while True:
        time.sleep(1)


threading.Thread(target=server,daemon=True).start()

miner = input("Miner address: ")

start_mining(miner)
