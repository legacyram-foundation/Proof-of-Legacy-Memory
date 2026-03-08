#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import socket
import threading

PORT = 5001

CHAIN_FILE="polm_chain.json"
PEER_FILE="peers.json"
MEMPOOL_FILE="mempool.json"

NETWORK_ID="POLM_TESTNET_1"

MAX_SUPPLY=32000000
INITIAL_REWARD=10
HALVING_INTERVAL=100000

BLOCK_TIME_TARGET=10
DIFFICULTY_START=5

TX_FEE=0.01

RAM_BUFFER_MB=64

lock=threading.Lock()

# ---------------- RAM ----------------

print("Allocating RAM buffer")

ram_buffer = bytearray(os.urandom(RAM_BUFFER_MB*1024*1024))

print("RAM ready")

# ---------------- MEMORY HASH ----------------

def memory_hash(seed):

    h = hashlib.sha256(str(seed).encode()).digest()

    for _ in range(64):

        idx = int.from_bytes(h[:4],"big") % len(ram_buffer)

        val = ram_buffer[idx]

        h = hashlib.sha256(h + bytes([val])).digest()

    return h.hex()

# ---------------- FILE ----------------

def load_json(file,default):

    if not os.path.exists(file):

        with open(file,"w") as f:
            json.dump(default,f)

    with open(file) as f:

        return json.load(f)

def save_json(file,data):

    with open(file,"w") as f:

        json.dump(data,f)

# ---------------- CHAIN ----------------

def load_chain():

    chain=load_json(CHAIN_FILE,[])

    if not chain:

        genesis={

            "height":0,
            "parent":"genesis",
            "hash":"genesis",
            "difficulty":DIFFICULTY_START,
            "timestamp":time.time(),
            "transactions":[],
            "merkle_root":"0"

        }

        save_json(CHAIN_FILE,[genesis])

        return [genesis]

    return chain

def save_chain(chain):

    save_json(CHAIN_FILE,chain)

# ---------------- MERKLE ----------------

def merkle_root(txs):

    if not txs:

        return hashlib.sha256(b"empty").hexdigest()

    hashes=[hashlib.sha256(json.dumps(tx).encode()).hexdigest() for tx in txs]

    while len(hashes)>1:

        new=[]

        for i in range(0,len(hashes),2):

            left=hashes[i]

            right=hashes[i+1] if i+1<len(hashes) else left

            new_hash=hashlib.sha256((left+right).encode()).hexdigest()

            new.append(new_hash)

        hashes=new

    return hashes[0]

# ---------------- PEERS ----------------

def load_peers():

    return load_json(PEER_FILE,[])

def save_peers(p):

    save_json(PEER_FILE,p)

def add_peer(ip):

    peers=load_peers()

    if ip not in peers:

        peers.append(ip)

        save_peers(peers)

# ---------------- MEMPOOL ----------------

def load_mempool():

    return load_json(MEMPOOL_FILE,[])

def save_mempool(m):

    save_json(MEMPOOL_FILE,m)

def add_tx(tx):

    m=load_mempool()

    m.append(tx)

    save_mempool(m)

# ---------------- BALANCE ----------------

def balance(addr):

    chain=load_chain()

    bal=0

    for b in chain:

        if b.get("miner")==addr:

            bal+=b.get("reward",0)

        for tx in b.get("transactions",[]):

            if tx["to"]==addr:

                bal+=tx["amount"]

            if tx["from"]==addr:

                bal-=tx["amount"]+tx["fee"]

    return bal

# ---------------- DIFFICULTY ----------------

def get_difficulty(chain):

    if len(chain)<20:

        return DIFFICULTY_START

    last=chain[-1]

    prev=chain[-20]

    span=last["timestamp"]-prev["timestamp"]

    avg=span/20

    diff=last["difficulty"]

    if avg < BLOCK_TIME_TARGET:

        diff+=1

    if avg > BLOCK_TIME_TARGET*2 and diff>1:

        diff-=1

    return diff

# ---------------- HEADER HASH ----------------

def block_hash(header):

    data=json.dumps(header,sort_keys=True).encode()

    return hashlib.sha256(data).hexdigest()

# ---------------- NETWORK ----------------

def send(peer,msg):

    try:

        s=socket.socket()

        s.settimeout(2)

        s.connect((peer,PORT))

        s.send(json.dumps(msg).encode())

        s.close()

    except:

        pass

def broadcast(msg):

    peers=load_peers()

    for p in peers:

        send(p,msg)

# ---------------- SERVER ----------------

def server():

    s=socket.socket()

    s.bind(("0.0.0.0",PORT))

    s.listen()

    while True:

        conn,addr=s.accept()

        ip=addr[0]

        add_peer(ip)

        try:

            msg=json.loads(conn.recv(65536).decode())

            if msg["type"]=="block":

                block=msg["data"]

                chain=load_chain()

                if block["parent"]==chain[-1]["hash"]:

                    chain.append(block)

                    save_chain(chain)

                    print("BLOCK RECEIVED",block["hash"][:10])

            if msg["type"]=="tx":

                add_tx(msg["data"])

                print("TX RECEIVED")

            if msg["type"]=="peers":

                for p in msg["data"]:

                    add_peer(p)

        except:

            pass

        conn.close()

# ---------------- MINING ----------------

def mine(addr):

    while True:

        chain=load_chain()

        parent=chain[-1]["hash"]

        height=len(chain)

        diff=get_difficulty(chain)

        seed=random.randint(0,2**64)

        mempool=load_mempool()

        root=merkle_root(mempool)

        header={

            "height":height,
            "parent":parent,
            "merkle_root":root,
            "timestamp":time.time(),
            "difficulty":diff,
            "nonce":seed

        }

        h=block_hash(header)

        if h.startswith("0"*diff):

            reward=INITIAL_REWARD+sum(tx["fee"] for tx in mempool)

            block={

                **header,
                "hash":h,
                "miner":addr,
                "reward":reward,
                "transactions":mempool

            }

            save_mempool([])

            chain.append(block)

            save_chain(chain)

            print("BLOCK MINED",h[:10],"reward",reward)

            broadcast({"type":"block","data":block})

# ---------------- WALLET ----------------

def send_coins():

    frm=input("from: ")

    to=input("to: ")

    amount=float(input("amount: "))

    if balance(frm)<amount+TX_FEE:

        print("not enough balance")

        return

    tx={

        "from":frm,
        "to":to,
        "amount":amount,
        "fee":TX_FEE,
        "timestamp":time.time()

    }

    tx["txid"]=hashlib.sha256(json.dumps(tx).encode()).hexdigest()

    add_tx(tx)

    broadcast({"type":"tx","data":tx})

    print("TX SENT")

# ---------------- CLI ----------------

def menu():

    print()
    print("1 start mining")
    print("2 balance")
    print("3 send coins")
    print("4 peers")
    print()

    c=input("> ")

    if c=="1":

        addr=input("miner address: ")

        mine(addr)

    if c=="2":

        addr=input("address: ")

        print(balance(addr))

    if c=="3":

        send_coins()

    if c=="4":

        print(load_peers())

# ---------------- START ----------------

threading.Thread(target=server,daemon=True).start()

while True:

    menu()
