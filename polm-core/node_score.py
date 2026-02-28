import json

def calculate_score():
    with open("proofs.json", "r") as f:
        proofs = json.load(f)

    total_proofs = len(proofs)

    avg_latency = sum(p["latency"] for p in proofs) / total_proofs

    score = total_proofs / avg_latency

    print("\n=== NODE SCORE ===")
    print("Total Proofs:", total_proofs)
    print("Average Latency:", avg_latency)
    print("Node Score:", score)

if __name__ == "__main__":
    calculate_score()
