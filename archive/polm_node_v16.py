#!/usr/bin/env python3

import time
import random
import hashlib
import json
import os
import threading

DAG_FILE="polm_chain.json"
MEMPOOL_FILE="polm_mempool.json"

BLOCK_REWARD=10

dag_lock=threading.Lock()

# ---------------- DAG ----------------

def load_chain():

    if not os.path.exists(DAG_FILE):

        genesis={
            "hash":"genesis",
            "parents":[],
            "transactions":[]
        }

        with open(DAG_FILE,"w") as f:
            json.dump([genesis],f)

    with open(DAG_FILE) as f:
        return json.load(f)


def save_chain(chain):

    with open(DAG_FILE,"w") as f:
        json.dump(chain,f)

# ---------------- MEMPOOL ----------------

def load_mempool():

    if not os.path.exists(MEMPOOL_FILE):
        return []

    with open(MEMPOOL_FILE) as f:
        return json.load(f)


def save_mempool(pool):

    with open(MEMPOOL_FILE,"w") as f:
        json.dump(pool,f)

# ---------------- BALANCE ----------------

def compute_balance(address):

    chain=load_chain()

    balance=0

    for block in chain:

        for tx in block.get("transactions",[]):

            if tx["to"]==address:
                balance+=tx["amount"]

            if tx["from"]==address:
                balance-=tx["amount"]

        if block.get("miner")==address:
            balance+=block.get("reward",0)

    return balance

# ---------------- TX ----------------

def create_tx():

    sender=input("from: ")
    receiver=input("to: ")
    amount=float(input("amount: "))

    if compute_balance(sender)<amount:

        print("insufficient balance")
        return

    tx={
        "from":sender,
        "to":receiver,
        "amount":amount
    }

    pool=load_mempool()

    pool.append(tx)

    save_mempool(pool)

    print("transaction added")

# ---------------- MINING ----------------

def mine(address):

    while True:

        chain=load_chain()

        mempool=load_mempool()

        txs=mempool[:5]

        seed=random.randint(0,2**32)

        h=hashlib.sha256(str(seed).encode()).hexdigest()

        if int(h,16)<2**250:

            with dag_lock:

                chain=load_chain()

                block={

                    "hash":h,
                    "parents":[chain[-1]["hash"]],
                    "miner":address,
                    "reward":BLOCK_REWARD,
                    "transactions":txs,
                    "timestamp":time.time()

                }

                chain.append(block)

                save_chain(chain)

                pool=load_mempool()

                pool=pool[5:]

                save_mempool(pool)

                print("BLOCK MINED",h[:10])

# ---------------- CLI ----------------

def menu():

    print()
    print("1 mine")
    print("2 send")
    print("3 balance")
    print()

    choice=input("> ")

    if choice=="1":

        addr=input("miner address: ")

        mine(addr)

    if choice=="2":

        create_tx()

    if choice=="3":

        addr=input("address: ")

        print("balance:",compute_balance(addr))

while True:
    menu()
