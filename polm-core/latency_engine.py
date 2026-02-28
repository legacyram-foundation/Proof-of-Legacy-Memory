import hashlib
import time
import platform

start = time.time()

# Simulação de trabalho
time.sleep(0.5)

end = time.time()

execution_time = end - start

node_info = platform.node()
timestamp = time.time()

proof_data = f"{node_info}-{execution_time}-{timestamp}"

proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

print("\n=== PoLM Proof Generated ===")
print("Node:", node_info)
print("Latency:", execution_time)
print("Proof:", proof_hash)
