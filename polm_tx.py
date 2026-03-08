#!/usr/bin/env python3

import json
import time
import hashlib

WALLET_FILE = "polm_wallet.json"

def send_tx(to_address,amount):

    with open(WALLET_FILE) as f:
        wallet = json.load(f)

    tx = {
        "from":wallet["address"],
        "to":to_address,
        "amount":amount,
        "timestamp":time.time()
    }

    tx["hash"] = hashlib.sha256(str(tx).encode()).hexdigest()

    with open("mempool.json","w") as f:
        json.dump(tx,f,indent=2)

    print("Transaction created")
    print(tx)

addr = input("Send to address: ")
amt = float(input("Amount: "))

send_tx(addr,amt)
