from proof_logger import save_proof
import hashlib
import time
import platform
import json

# carregar identidade do node
with open("node_id.json", "r") as f:
    identity = json.load(f)

NODE_ID = identity["node_id"]

start = time.time()

# Simulação de trabalho PoLM
time.sleep(0.5)

end = time.time()
execution_time = end - start

node_info = platform.node()
timestamp = time.time()

# gerar prova
proof_data = f"{NODE_ID}-{execution_time}-{timestamp}"
proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

# salvar prova
save_proof(
    node_info,
    execution_time,
    proof_hash,
    NODE_ID
)

print("\n=== PoLM Proof Generated ===")
print("Node:", node_info)
print("Latency:", execution_time)
print("Proof:", proof_hash)
