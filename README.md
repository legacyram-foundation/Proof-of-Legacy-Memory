# PoLM — Proof of Legacy Memory

> **The first RAM-latency-bound Proof-of-Work consensus algorithm.**  
> Giving computational relevance back to legacy hardware.

[![Version](https://img.shields.io/badge/version-3.1.0-00e5ff?style=flat-square&labelColor=0d1520)](.)
[![Status](https://img.shields.io/badge/status-testnet-ffb300?style=flat-square&labelColor=0d1520)](.)
[![Python](https://img.shields.io/badge/python-3.9%2B-00ff88?style=flat-square&labelColor=0d1520)](.)
[![License](https://img.shields.io/badge/license-MIT-white?style=flat-square&labelColor=0d1520)](LICENSE)

---

## What is PoLM?

Most cryptocurrencies reward whoever has the most powerful hardware. PoLM flips this: the bottleneck is **real DRAM latency** — a physical property that cannot be miniaturized, parallelized, or easily optimized with ASICs.

A **Core 2 Duo from 2006 with DDR2** is genuinely competitive against a modern i5 with DDR4.

---

## Proven in the real world

On March 15, 2026, a 3-node testnet ran for several hours on real hardware:

| Miner | CPU | RAM | Latency | Boost | Blocks | Share |
|-------|-----|-----|---------|-------|--------|-------|
| POLM_Aluisio | i5 12th gen, 16t | DDR4 | ~1200 ns | 1.00× (×0.65 pen.) | 330 | 67% |
| POLM6837… | i5 7th gen, 4t | DDR4 | ~1620 ns | 1.00× | 120 | 24% |
| **POLMBE9E…** | **Core 2 Duo, 2t** | **DDR2** | **~6700 ns** | **6.00×** | **43** | **9%** |

**Key result**: a 2006 Core 2 Duo with DDR2 mined 43 blocks including 3 consecutive blocks (#488, #489, #490), competing directly against modern hardware.

---

## How it works

```
getwork()
    ↓
Build Memory DAG (seeded from epoch + prev_hash)
    ↓
Random Memory Walk (N steps — adaptive per RAM type)
    ├─ Each step: pos = H(prev_hash) % DAG_size
    ├─ Read 32 bytes from DAG[pos]
    ├─ H_new = sha3_256(H_prev ∥ DAG[pos])
    └─ Measure access latency (nanoseconds)
    ↓
Latency Proof embedded in block header
    ↓
submit() → Central node validates + adds to chain
```

---

## Legacy Boost Multipliers

Calibrated from real testnet measurements (March 2026):

| RAM Type | Multiplier | Measured Latency | Walk Steps |
|----------|-----------|-----------------|-----------|
| DDR2 | **6.00×** | ~6700–7700 ns | 80 |
| DDR3 | **2.80×** | ~1500–3000 ns | 150 |
| DDR4 | 1.00× | ~900–1700 ns | 500 |
| DDR5 | 0.70× | ~500–900 ns | 700 |

### Saturation Penalty (thread count)

| Threads | Penalty |
|---------|---------|
| 1–2 | 1.00× |
| 3–4 | 0.90× |
| 5–8 | 0.80× |
| 9–16 | 0.65× |
| 17+ | 0.50× |

---

## Architecture

```
┌─────────────────────────────┐
│   Central Node (any PC)     │  ← stores blockchain, validates blocks
│   polm.py node              │  ← REST API: /getwork /submit /chain
└──────────────┬──────────────┘
               │ HTTP
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Miner  │ │ Miner  │ │ Miner  │  ← any PC on the network
│ DDR2   │ │ DDR4   │ │ DDR4   │  ← polm.py miner <node_ip> <id> <ram>
└────────┘ └────────┘ └────────┘
```

Single file. No complex sync. Miners call `/getwork`, mine, and `/submit`.

---

## Quick Start

### Requirements

```bash
pip install flask
```

### 1. Start the central node

```bash
python3 polm.py node
```

### 2. Start miners

```bash
python3 polm.py miner <NODE_IP> <MINER_ID> <RAM_TYPE>

# Examples
python3 polm.py miner 192.168.0.103 MyAddress DDR2
python3 polm.py miner 192.168.0.103 MyAddress DDR4
```

### 3. Start the explorer

```bash
python3 polm_explorer.py http://NODE_IP:6060 5050
# Open http://localhost:5050
```

### 4. Run in background

```bash
nohup python3 polm.py node > /tmp/node.log 2>&1 &
nohup python3 polm.py miner 192.168.0.103 MyAddress DDR4 > /tmp/miner.log 2>&1 &
nohup python3 polm_explorer.py http://localhost:6060 5050 > /tmp/explorer.log 2>&1 &
```

---

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Node status and chain summary |
| `/getwork` | GET | Current mining job |
| `/submit` | POST | Submit a mined block |
| `/chain` | GET | List blocks (`?limit=N&offset=N`) |
| `/block/<height>` | GET | Get block by height |
| `/balance/<address>` | GET | Address balance |
| `/miners` | GET | Leaderboard with stats per miner |

---

## Protocol Parameters

| Parameter | Value |
|-----------|-------|
| Symbol | POLM |
| Max Supply | 32,000,000 |
| Block Time Target | 30 seconds |
| Initial Reward | 5.0 POLM |
| Halving | Every ~4 years |
| Difficulty Retarget | Every 144 blocks (±25% max) |
| Epoch Length | 100,000 blocks |
| Hash Algorithm | SHA3-256 |

---

## Files

```
polm.py              ← entire protocol: node + miner in one file
polm_explorer.py     ← web explorer (retro terminal UI)
README.md            ← this file
WHITEPAPER.md        ← full technical specification
LICENSE              ← MIT
requirements.txt     ← flask only
scripts/
└── deploy_network.sh
```

---

## Roadmap

- [x] v1.0 — Basic PoW with RAM latency measurement
- [x] v2.0 — Memory DAG + latency proof + legacy boost
- [x] v3.0 — Pool architecture (central node + remote miners)
- [x] v3.1 — Web explorer with live leaderboard ✅ **current**
- [ ] v3.2 — Wallet with ECDSA signatures + transactions
- [ ] v3.3 — P2P gossip (multiple full nodes)
- [ ] v4.0 — Mainnet genesis

---

## Status

🟡 **Experimental Testnet** — algorithm validated on real hardware, not production ready.

---

*PoLM is experimental software. Not financial advice.*
