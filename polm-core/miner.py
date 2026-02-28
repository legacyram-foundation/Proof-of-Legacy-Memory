import time
import subprocess

print("=== PoLM Miner Started ===")

while True:
    print("\nRunning latency proof...")
    
    subprocess.run(["python3", "polm-core/latency_engine.py"])
    
    print("Sleeping 10 seconds...\n")
    time.sleep(10)
