import json
import hashlib
import sys
import requests

NODE="http://127.0.0.1:8080"

with open("wallet.json") as f:
    wallet=json.load(f)

address=wallet["address"]

def balance():

    chain=requests.get(NODE+"/stats")

    print("Wallet:",address[:16])
    print("Balance: feature coming soon")

def send(to,amount):

    tx={
        "from":address,
        "to":to,
        "amount":amount
    }

    requests.post(NODE+"/tx",json=tx)

    print("Transaction sent")

if sys.argv[1]=="balance":
    balance()

if sys.argv[1]=="send":
    send(sys.argv[2],sys.argv[3])
