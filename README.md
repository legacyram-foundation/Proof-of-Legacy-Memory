# PoLM — Proof of Legacy Memory

<div align="center">

**https://polm.com.br**

[![Version](https://img.shields.io/badge/version-1.2.0-00e5ff?style=flat-square&labelColor=0d1520)](https://polm.com.br)
[![Website](https://img.shields.io/badge/website-polm.com.br-22d3ee?style=flat-square&labelColor=0d1520)](https://polm.com.br)
[![Twitter](https://img.shields.io/badge/@polm2026-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/polm2026)
[![Founder](https://img.shields.io/badge/@aluisiofer-000000?style=flat-square&logo=x&logoColor=white)](https://x.com/aluisiofer)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078d4?style=flat-square&labelColor=0d1520)](.)
[![Linux](https://img.shields.io/badge/Linux-✓-f97316?style=flat-square&labelColor=0d1520)](.)
[![macOS](https://img.shields.io/badge/macOS-✓-888888?style=flat-square&labelColor=0d1520)](.)
[![License](https://img.shields.io/badge/license-MIT-ffffff?style=flat-square&labelColor=0d1520)](LICENSE)

*The first RAM-latency-bound Proof-of-Work consensus algorithm.*  
*Giving computational relevance back to legacy hardware.*

</div>

---

## What is PoLM?

Most Proof-of-Work algorithms reward whoever has the most powerful hardware. PoLM flips this: the bottleneck is **real DRAM latency** — a physical property that cannot be miniaturized, parallelized, or replicated in ASIC silicon.

A **Core 2 Duo from 2006 with DDR2** leads the network against modern i5 12th gen machines with 16 threads.

---

## Proven on real hardware

Testnet running since **March 15, 2026** — **816 blocks mined across 4 hardware generations:**

| Rank | Miner | CPU | RAM | Latency | Boost | Blocks | Share |
|------|-------|-----|-----|---------|-------|--------|-------|
| 🥇 | POLMBE9E… | Core 2 Duo 2006 | **DDR2** | ~3800 ns | **10×** | 428 | **52.4%** |
| 🥈 | POLM6837… | i5 7th gen 4t | DDR4 | ~1741 ns | 1× | 284 | 34.8% |
| 🥉 | POLM_AMD… | AMD 2t | DDR3 | ~12988 ns | 8× | 62 | 7.6% |
| 4 | POLM_Aluisio | i5 12th gen 16t | DDR4 | ~1060 ns | 1× (0.65 pen.) | 43 | 5.3% |

**Key result**: a 2006 Core 2 Duo with DDR2 mined **52.4% of all blocks** — beating every modern machine on the network. Maximum advantage between generations: **~2.5×** (vs 100× in SHA-256).

---

## Quick Install

### Windows

```
1. Install Python 3.9+ from https://python.org
   ✓ Check "Add Python to PATH" during installation

2. Double-click:  scripts\install.bat

3. Double-click:  start_all.bat

4. Browser opens automatically → http://localhost:7070
```

### Linux / macOS

```bash
chmod +x scripts/install.sh && bash scripts/install.sh
./start_all.sh
```

---

## Services

| Service | URL | Description |
|---------|-----|-------------|
| **Wallet** | http://localhost:7070 | Send · Receive · History · QR code |
| **Explorer** | http://localhost:5050 | Blocks · Rankings · Transactions |
| **Node API** | http://localhost:6060 | REST · P2P · Mining |

---

## Usage

### Windows

```bat
:: Start everything (recommended)
start_all.bat

:: Individual services
start_node.bat        :: full node
start_miner.bat       :: miner
start_wallet.bat      :: wallet UI
start_explorer.bat    :: explorer

:: Command line
polm.bat node 6060
polm.bat miner http://localhost:6060 YOUR_ADDRESS DDR2
polm.bat info
```

### Linux / macOS

```bash
# Start everything (recommended)
./start_all.sh

# Individual
./start_node.sh
./start_miner.sh
./start_wallet.sh
./start_explorer.sh

# Command line
python3 polm.py node 6060
python3 polm.py miner http://localhost:6060 YOUR_ADDRESS DDR2
python3 polm.py info

# Wallet CLI
python3 polm_wallet.py show
python3 polm_wallet.py new "Mining rewards"
python3 polm_wallet.py balance http://localhost:6060
python3 polm_wallet.py send FROM_ADDR TO_ADDR 10.0
```

### Join mainnet

```bash
# Connect your node to polm.com.br seed nodes
python3 polm.py node 6060 node1.polm.com.br:6060 node2.polm.com.br:6060

# Mine on mainnet
python3 polm.py miner http://node1.polm.com.br:6060 YOUR_ADDRESS DDR2
```

---

## Algorithm

### Score formula (Whitepaper §7)

```
score = (1 / latency_ns) × boost × thread_penalty
```

Older hardware (higher DRAM latency) gets a higher boost, compensating for slower processing. The physics of RAM cannot be faked or miniaturized.

### Dynamic legacy boost (Whitepaper §8)

```
boost = (latency_ns / 1000) ^ 0.8
```

Continuous boost based on measured latency — no fixed table. DDR2 at 3800ns gets ~11×. DDR4 at 1060ns gets ~1×.

### Validated boost multipliers

| RAM | Testnet Latency | Boost | Testnet Share |
|-----|----------------|-------|--------------|
| DDR2 | ~3800 ns | **10×** | 52.4% 🏆 |
| DDR3 | ~1500–13000 ns | **8×** | 7.6% |
| DDR4 | ~900–1900 ns | **1×** | 40.1% |
| DDR5 | ~500–900 ns | **0.5×** | penalized |

### Thread saturation penalty

| Threads | Penalty | Reason |
|---------|---------|--------|
| 1–2 | 1.00× | Full reward |
| 3–4 | 0.90× | Light penalty |
| 5–8 | 0.80× | Moderate |
| 9–16 | 0.65× | Heavy (server CPUs) |
| 17+ | 0.50× | Maximum penalty |

---

## RAM Detection

| OS | Method | Manual override |
|----|--------|----------------|
| Windows | `wmic memorychip` + PowerShell | `set POLM_RAM_TYPE=DDR3` |
| Linux | `dmidecode` | `export POLM_RAM_TYPE=DDR3` |
| macOS | `system_profiler` | `export POLM_RAM_TYPE=DDR3` |

---

## Protocol Parameters

| Parameter | Testnet | Mainnet |
|-----------|---------|---------|
| Symbol | POLM | POLM |
| Max Supply | 32,000,000 | 32,000,000 |
| Block Time | 30s | 30s |
| Initial Reward | 5.0 POLM | 5.0 POLM |
| Halving Interval | 4,200,000 blocks | 4,200,000 blocks (~4 years) |
| DAG Size | 4 MB | 256 MB + 64 MB/epoch |
| Walk Steps | 500 | 100,000 |
| Difficulty Retarget | 144 blocks (±25%) | 144 blocks (±25%) |
| Hash Algorithm | SHA3-256 | SHA3-256 |
| Epoch Length | 100,000 blocks | 100,000 blocks |

---

## REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Node status + chain summary |
| `/getwork` | GET | Mining job + pending transactions |
| `/submit` | POST | Submit mined block |
| `/tx/send` | POST | Broadcast transaction |
| `/tx/<id>` | GET | Transaction by ID |
| `/mempool` | GET | Pending transactions |
| `/chain` | GET | Block list (`?limit=N&offset=N`) |
| `/block/<h>` | GET | Block + embedded transactions |
| `/balance/<addr>` | GET | Address balance |
| `/history/<addr>` | GET | Transaction history |
| `/miners` | GET | Mining leaderboard |
| `/peers` | GET | Connected peers |
| `/peers/add` | POST | Add peer |
| `/info` | GET | Node platform info |

---

## Files

```
polm.py              ← Full node + miner  (Windows / Linux / macOS)
polm_wallet.py       ← Web wallet UI + CLI
polm_explorer.py     ← Blockchain explorer v4.0
requirements.txt     ← flask  cryptography  requests
README.md            ← this file
WHITEPAPER.md        ← full technical specification
LICENSE              ← MIT
scripts/
├── install.bat      ← Windows one-click installer
└── install.sh       ← Linux / macOS installer
```

---

## Economics

| Period | Reward | Approx supply |
|--------|--------|--------------|
| Year 1–4 | 5.0 POLM | ~21M |
| Year 5–8 | 2.5 POLM | ~27M |
| Year 9–12 | 1.25 POLM | ~30M |
| Year 13+ | decreasing | → 32M |

### Founder allocation

| Parameter | Value |
|-----------|-------|
| Allocation | 1,600,000 POLM (5% of max supply) |
| Lock period | 5,256,000 blocks (~5 years) |
| Vesting | Linear over 24 months after unlock |

---

## Security

| Attack | Defense |
|--------|---------|
| ASIC | 256 MB DAG + latency-hard walk — DRAM physics cannot be miniaturized |
| GPU | GDDR latency > DDR latency — no bandwidth advantage |
| Cache exploit | Latency < 5 ns → block rejected by all nodes |
| Fake RAM | Dynamic boost measures real latency, not declared RAM type |
| Timestamp | ±120s tolerance enforced at consensus level |
| Sybil | Peer scoring + DNS seed bootstrap |

---

## Windows Troubleshooting

| Problem | Solution |
|---------|---------|
| Python not found | Install from python.org — check "Add to PATH" |
| Permission denied | Right-click install.bat → Run as Administrator |
| Wrong RAM detected | `set POLM_RAM_TYPE=DDR2` before running |
| Port 6060 in use | `netstat -ano \| findstr 6060` |
| Wallet won't open | Go to http://localhost:7070 manually |
| Node offline | Check Windows Firewall — allow Python |

---

## Roadmap

- [x] v1.0 — PoLM algorithm validated on real hardware
- [x] v1.0 — Full node + miner + P2P gossip
- [x] v1.1 — Web wallet + transaction mempool + ECDSA signatures
- [x] v1.2 — Windows 10/11 full support · polm.com.br · mainnet ready ✅ **current**
- [ ] v1.3 — Mining gateway + Stratum protocol
- [ ] v2.0 — Rust/Go production node
- [ ] v3.0 — **Mainnet genesis**

---

## Community

| Channel | Link |
|---------|------|
| Website | https://polm.com.br |
| Project Twitter | https://x.com/polm2026 |
| Founder Twitter | https://x.com/aluisiofer |
| GitHub | https://github.com/proof-of-legacy/Proof-of-Legacy-Memory |

---

🟢 **Mainnet ready** — algorithm validated. Genesis block pending.

*PoLM is experimental software. Not financial advice.*
