#!/usr/bin/env python3

import json
import os
import time

CHAIN_FILE="polm_chain.json"

def load_chain():

    if not os.path.exists(CHAIN_FILE):
        return []

    try:
        with open(CHAIN_FILE) as f:
            return json.load(f)
    except:
        return []

def analyze(chain):

    miners={}
    hardware={}

    for block in chain:

        miner=block.get("miner","unknown")
        ram=block.get("ram","unknown")
        score=block.get("score",0)

        if miner not in miners:
            miners[miner]={"blocks":0,"score":0}

        miners[miner]["blocks"]+=1
        miners[miner]["score"]+=score

        if ram not in hardware:
            hardware[ram]={"blocks":0,"score":0}

        hardware[ram]["blocks"]+=1
        hardware[ram]["score"]+=score

    return miners,hardware

def show():

    while True:

        os.system("clear")

        chain=load_chain()

        miners,hardware=analyze(chain)

        print("===== PoLM NETWORK MONITOR =====")
        print()

        print("TOTAL BLOCKS:",len(chain))
        print()

        print("----- MINERS -----")

        for m,data in miners.items():

            avg=0

            if data["blocks"]>0:
                avg=data["score"]/data["blocks"]

            print(
                m,
                "| blocks:",data["blocks"],
                "| avg score:",round(avg,2)
            )

        print()
        print("----- HARDWARE -----")

        for h,data in hardware.items():

            avg=0

            if data["blocks"]>0:
                avg=data["score"]/data["blocks"]

            print(
                h,
                "| blocks:",data["blocks"],
                "| avg score:",round(avg,2)
            )

        print()

        time.sleep(3)

show()
