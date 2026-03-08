import json

CHAIN_FILE = "polm_chain.json"


def load_chain():
    with open(CHAIN_FILE) as f:
        return json.load(f)


def calculate_balances(chain):

    balances = {}

    for block in chain:

        txs = block.get("transactions", [])

        for tx in txs:

            sender = tx["from"]
            receiver = tx["to"]
            amount = tx["amount"]

            if sender != "network":
                balances[sender] = balances.get(sender,0) - amount

            balances[receiver] = balances.get(receiver,0) + amount

    return balances


def get_balance(address):

    chain = load_chain()

    balances = calculate_balances(chain)

    return balances.get(address,0)


if __name__ == "__main__":

    address = input("Address: ")

    balance = get_balance(address)

    print("Balance:", balance, "POLM")
