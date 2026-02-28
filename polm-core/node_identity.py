import uuid
import json
import platform
import os

IDENTITY_FILE = "node_id.json"

def generate_identity():
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, "r") as f:
            return json.load(f)

    node_id = str(uuid.uuid4())

    identity = {
        "node_name": platform.node(),
        "node_id": node_id
    }

    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=4)

    return identity


if __name__ == "__main__":
    identity = generate_identity()
    print("\n=== NODE IDENTITY ===")
    print(identity)
