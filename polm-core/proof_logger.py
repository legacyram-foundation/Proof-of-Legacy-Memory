import json
import os

PROOF_FILE = "proofs.json"


def save_proof(node, latency, proof, node_id):

    new_proof = {
        "node": node,
        "node_id": node_id,
        "latency": latency,
        "proof": proof
    }

    # cria arquivo se não existir
    if not os.path.exists(PROOF_FILE):
        with open(PROOF_FILE, "w") as f:
            json.dump([], f)

    # carregar provas existentes
    with open(PROOF_FILE, "r") as f:
        data = json.load(f)

    data.append(new_proof)

    # salvar novamente
    with open(PROOF_FILE, "w") as f:
        json.dump(data, f, indent=4)
