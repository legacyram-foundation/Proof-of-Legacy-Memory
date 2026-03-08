#!/usr/bin/env python3

import os
import json
import hashlib
from ecdsa import SigningKey, SECP256k1

WALLET_FILE = "wallet.json"

# ---------------- HASH160 ----------------
def hash160(data_bytes):
    sha = hashlib.sha256(data_bytes).digest()
    rip = hashlib.new("ripemd160", sha).digest()
    return rip.hex()

# ---------------- CREATE WALLET ----------------
def create_wallet():

    sk = SigningKey.generate(curve=SECP256k1)
    pk = sk.get_verifying_key()

    private_key = sk.to_string().hex()
    public_key = pk.to_string().hex()

    address = hash160(bytes.fromhex(public_key))

    wallet = {
        "private_key": private_key,
        "public_key": public_key,
        "address": address
    }

    with open(WALLET_FILE,"w") as f:
        json.dump(wallet,f)

    print("Wallet created")
    print("Address:", address)

# ---------------- LOAD ----------------
def load_wallet():

    if not os.path.exists(WALLET_FILE):
        print("wallet.json not found")
        return None

    with open(WALLET_FILE) as f:
        return json.load(f)

# ---------------- SIGN TX ----------------
def sign_tx(tx):

    wallet = load_wallet()

    sk = SigningKey.from_string(bytes.fromhex(wallet["private_key"]), curve=SECP256k1)

    message = json.dumps(tx, sort_keys=True).encode()

    sig = sk.sign(message)

    return sig.hex()

# ---------------- CLI ----------------
def menu():

    print()
    print("1 create wallet")
    print("2 show address")
    print()

    c = input("> ")

    if c == "1":
        create_wallet()

    if c == "2":
        w = load_wallet()
        if w:
            print("Address:", w["address"])

if __name__ == "__main__":
    menu()
