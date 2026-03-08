#!/usr/bin/env python3

import hashlib
import secrets
import json

WALLET_FILE = "polm_wallet.json"

def create_wallet():

    private_key = secrets.token_hex(32)

    public_key = hashlib.sha256(private_key.encode()).hexdigest()

    address = hashlib.sha256(public_key.encode()).hexdigest()

    wallet = {
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    }

    with open(WALLET_FILE,"w") as f:
        json.dump(wallet,f,indent=2)

    print("Wallet created")
    print("Address:",address)

create_wallet()
