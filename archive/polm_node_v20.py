import json
import time
import hashlib
import threading
import socket
import os
import random

PORT=5555
CHAIN_FILE="polm_chain.json"

lock=threading.Lock()

# coloque os IPs dos 3 computadores aqui
PEERS=[
"192.168.0.102",
"192.168.0.103",
"192.168.0.104"
]

difficulty=2
target_block_time=2
adjust_interval=20


def sha(data):
    return hashlib.sha256(data.encode()).hexdigest()


def atomic_write(chain):
    tmp="polm_chain.tmp"
    with open(tmp,"w") as f:
        json.dump(chain,f)
    os.replace(tmp,CHAIN_FILE)


def load_chain():

    if not os.path.exists(CHAIN_FILE):

        genesis={
            "index":0,
            "timestamp":time.time(),
            "prev":"genesis",
            "miner":"genesis",
            "nonce":0,
            "difficulty":difficulty,
            "hash":"genesis"
        }

        atomic_write([genesis])
        return [genesis]

    with open(CHAIN_FILE) as f:
        return json.load(f)


def save_chain(chain):
    atomic_write(chain)


def adjust_difficulty(chain):

    global difficulty

    if len(chain)<adjust_interval+1:
        return

    last=chain[-1]
    prev=chain[-adjust_interval]

    span=last["timestamp"]-prev["timestamp"]
    avg=span/adjust_interval

    if avg<target_block_time:
        difficulty+=1
    elif difficulty>1:
        difficulty-=1

    print("DIFFICULTY",difficulty,"avg",round(avg,2),"s")


def sync_chain():

    global difficulty

    best_chain=load_chain()

    for peer in PEERS:

        try:

            s=socket.socket()
            s.connect((peer,PORT))
            s.send(b"GET_CHAIN")

            data=b""

            while True:
                part=s.recv(4096)
                if not part:
                    break
                data+=part

            s.close()

            peer_chain=json.loads(data.decode())

            if len(peer_chain)>len(best_chain):
                best_chain=peer_chain

        except:
            pass

    save_chain(best_chain)

    if len(best_chain)>1:
        difficulty=best_chain[-1]["difficulty"]


def mine(miner):

    global difficulty

    while True:

        with lock:
            chain=load_chain()
            last=chain[-1]

        index=last["index"]+1
        prev=last["hash"]

        nonce=random.randint(0,1_000_000)

        h=sha(str(index)+prev+miner+str(nonce))

        if h.startswith("0"*difficulty):

            block={
                "index":index,
                "timestamp":time.time(),
                "prev":prev,
                "miner":miner,
                "nonce":nonce,
                "difficulty":difficulty,
                "hash":h
            }

            with lock:

                chain=load_chain()

                if chain[-1]["hash"]!=prev:
                    continue

                chain.append(block)

                adjust_difficulty(chain)

                save_chain(chain)

            print("BLOCK MINED",h[:10],"diff",difficulty)

            broadcast_block(block)


def broadcast_block(block):

    msg=json.dumps({"type":"BLOCK","data":block}).encode()

    for peer in PEERS:

        try:
            s=socket.socket()
            s.connect((peer,PORT))
            s.send(msg)
            s.close()
        except:
            pass


def handle(conn):

    data=conn.recv(65536)

    if not data:
        conn.close()
        return

    try:

        if data==b"GET_CHAIN":

            chain=load_chain()

            conn.send(json.dumps(chain).encode())

        else:

            msg=json.loads(data.decode())

            if msg["type"]=="BLOCK":

                block=msg["data"]

                with lock:

                    chain=load_chain()

                    if block["prev"]==chain[-1]["hash"]:

                        chain.append(block)

                        save_chain(chain)

                        print("BLOCK RECEIVED",block["hash"][:10])

    except:
        pass

    conn.close()


def server():

    s=socket.socket()
    s.bind(("0.0.0.0",PORT))
    s.listen()

    while True:

        conn,_=s.accept()

        threading.Thread(target=handle,args=(conn,)).start()


def balance(addr):

    chain=load_chain()

    bal=0

    for b in chain:
        if b["miner"]==addr:
            bal+=1

    print("balance:",bal)


def menu():

    print()
    print("1 start mining")
    print("2 balance")
    print()

    cmd=input("> ")

    if cmd=="1":

        addr=input("miner address: ")

        threading.Thread(target=server).start()

        print("syncing network...")

        sync_chain()

        mine(addr)

    if cmd=="2":

        addr=input("address: ")

        balance(addr)


if __name__=="__main__":
    menu()
