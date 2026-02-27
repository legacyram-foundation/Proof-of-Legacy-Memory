import time
import subprocess

TEST_RUNS = 5

print("PoLM Benchmark Starting...\n")

results = []

for i in range(TEST_RUNS):
    start = time.time()

    subprocess.run(
        ["python3", "../polm-core/latency_engine.py"],
        stdout=subprocess.DEVNULL
    )

    end = time.time()
    duration = end - start
    results.append(duration)

    print(f"Run {i+1}: {duration:.4f} sec")

avg = sum(results) / len(results)

print("\n--- Benchmark Result ---")
print(f"Average Execution Time: {avg:.4f} sec")
