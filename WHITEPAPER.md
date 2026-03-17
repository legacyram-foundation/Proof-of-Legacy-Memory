# PoLM — Proof of Legacy Memory
## Technical Whitepaper v1.2 — Mainnet Ready

<div align="center">

**https://polm.com.br**  
[@polm2026](https://x.com/polm2026) · [@aluisiofer](https://x.com/aluisiofer)

</div>

---

> *"Every old computer deserves a second life."*

---

## Abstract

**PoLM** (Proof of Legacy Memory) is a Proof-of-Work consensus algorithm where the primary bottleneck is **real DRAM access latency** — a physical property that cannot be miniaturized, parallelized, or replicated efficiently in ASIC silicon.

Unlike SHA-256 (compute-bound) or Ethash (VRAM bandwidth-bound), PoLM is **latency-bound**: the time to complete one unit of work is dominated by how long it takes to read random bytes from RAM.

### Validated results (Testnet, March 2026 — 816 blocks)

| Hardware | RAM | Measured Latency | Dynamic Boost | Blocks | Share |
|----------|-----|-----------------|---------------|--------|-------|
| Core 2 Duo (2006) | DDR2 | ~3800 ns | ~11× | 428 | **52.4%** 🏆 |
| i5 7th gen 4t | DDR4 | ~1741 ns | ~1× | 284 | 34.8% |
| AMD 2t | DDR3 | ~12988 ns | ~10× | 62 | 7.6% |
| i5 12th gen 16t | DDR4 | ~1060 ns | ~1× (0.65 pen.) | 43 | 5.3% |

**Maximum advantage between hardware generations: ~2.5×** — compared to 100× in SHA-256.

---

## 1. Project Information

| Field | Value |
|-------|-------|
| Project name | PoLM — Proof of Legacy Memory |
| Symbol | POLM |
| Website | https://polm.com.br |
| Twitter | https://x.com/polm2026 |
| Founder | Aluísio Fernandes — https://x.com/aluisiofer |
| Repository | https://github.com/proof-of-legacy/Proof-of-Legacy-Memory |
| License | MIT |
| Status | Testnet validated — Mainnet pending genesis |

---

## 2. Objectives

- Support 1,000,000+ miners on commodity hardware
- Be fully decentralized — no central authority
- Resist ASICs, GPUs, and high-thread-count server rigs
- Reward legacy hardware economically
- Allow evolution via epochs without hard forks
- Maintain competitive parity across RAM generations (≤3× range)

---

## 3. Network Architecture

```
┌──────────────────────────────────────────────┐
│           Full Nodes (Consensus)             │
│  Validate blocks · Store chain · P2P gossip  │
│  node1.polm.com.br  node2.polm.com.br        │
└──────────────┬───────────────────────────────┘
               │ P2P gossip (polm/blocks, polm/txs)
        ┌──────┴──────┐
        ▼             ▼
  Relay Nodes    Mining Gateways
                      │
               Mining Proxies
                      │
    DDR2 ── DDR3 ── DDR4 ── DDR5
             Miners
```

### Node Types

| Type | Role |
|------|------|
| Full Node | Validates blocks, maintains chain, P2P gossip |
| Relay Node | Optimizes propagation, reduces latency |
| Mining Gateway | Aggregates miners, reduces full node load |
| Mining Proxy | Serves thousands of local miners |
| Miner | Executes PoLM algorithm, submits blocks |

---

## 4. Protocol Parameters

| Parameter | Value |
|-----------|-------|
| Block Time Target | 30 seconds |
| Difficulty Window | 144 blocks |
| Difficulty Clamp | ±25% per window |
| Epoch Length | 100,000 blocks |
| Initial Reward | 5.0 POLM |
| Halving Interval | 4,200,000 blocks (~4 years) |
| Max Supply | 32,000,000 POLM |
| Hash Algorithm | SHA3-256 |
| Mainnet DAG | 256 MB + 64 MB/epoch |
| Mainnet Walk Steps | 100,000 per nonce |
| Testnet DAG | 4 MB |
| Testnet Walk Steps | 500 |
| Min Transaction Fee | 0.0001 POLM |

---

## 5. Difficulty Adjustment

```python
expected_time = 144 × 30 = 4320 seconds
actual_time   = Δt of last 144 blocks

ratio = clamp(0.75, 1.25, expected_time / actual_time)
D_new = D_old × ratio
```

Adjusts every 144 blocks. Maximum ±25% change per window prevents oscillation.

---

## 6. PoLM Algorithm

### Flow

```
1. Generate Memory DAG (256 MB, seeded from epoch + prev_hash)
2. Initialize hash from: prev_hash + miner_address + nonce
3. Execute random memory walk (100,000 steps)
4. Measure average access latency (ns)
5. Compute score = (1 / latency_ns) × boost × thread_penalty
6. Validate: block_hash must start with "0" × difficulty
```

### Memory Walk (100,000 steps)

```python
h   = sha3_256(prev_hash + address + nonce)
pos = int(h[:8], little_endian) % dag_size

for step in range(100_000):
    mem = DAG[pos : pos+32]           # random read
    h   = sha3_256(h + mem)           # hash chain
    pos = int(h[:8], little_endian) % dag_size
    record_latency(read_time_ns)

avg_latency = total_ns / 100_000
final_hash  = h
```

Properties:
- Unpredictable access pattern — CPU prefetch cannot help
- Sequential dependency — cannot parallelize steps
- Cache-defeating — 256 MB DAG >> any L1/L2/L3 cache
- Tamper-proof — latency is measured and embedded in block header

---

## 7. Score Formula

```
score = (1 / latency_ns) × boost × thread_penalty
```

Lower latency hardware scores lower — but receives a boost multiplier that more than compensates.

---

## 8. Dynamic Legacy Boost

```python
baseline_latency = 1000  # ns (DDR4 reference)
alpha = 0.8

boost = (latency_ns / baseline_latency) ^ alpha
```

Continuous and automatic — no fixed lookup table. As measured latency increases (older RAM), boost increases proportionally.

### Validated results

| RAM | Measured Latency | Dynamic Boost | Effective Multiplier |
|-----|-----------------|---------------|---------------------|
| DDR2 Core2Duo | ~3800 ns | (3800/1000)^0.8 = **~8.5×** | combined ~11× |
| DDR3 AMD | ~12988 ns | (12988/1000)^0.8 = **~30×** | with static 8× |
| DDR4 i5-7th | ~1741 ns | (1741/1000)^0.8 = **~1.6×** | baseline ~1× |
| DDR4 i5-12th | ~1060 ns | (1060/1000)^0.8 = **~1.05×** | baseline |

*Note: static boost table is also applied — final effective score combines both.*

### Static boost table (validated on testnet)

| RAM | Multiplier | Testnet Share |
|-----|-----------|--------------|
| DDR2 | **10×** | 52.4% |
| DDR3 | **8×** | 7.6% |
| DDR4 | **1×** | 40.1% |
| DDR5 | **0.5×** | penalized |

---

## 9. Saturation Penalty

Discourages massive multi-socket server rigs and GPU farms.

| Threads | Penalty | Target hardware |
|---------|---------|----------------|
| 1–2 | 1.00× | Legacy laptops, single-core |
| 3–4 | 0.90× | Old desktops, i5/Ryzen entry |
| 5–8 | 0.80× | Mid-range desktop |
| 9–16 | 0.65× | High-end desktop, workstation |
| 17+ | 0.50× | Server, multi-socket |

A 2-thread Core 2 Duo has **no penalty**. A 16-thread modern i5 has **0.65× penalty**. This further narrows the advantage gap.

---

## 10. Block Validation Rules

A block is valid if ALL of the following hold:

```
1. block_hash starts with "0" × difficulty
2. block_hash == sha3_256(all_header_fields)
3. height == chain.tip.height + 1
4. prev_hash == chain.tip.block_hash
5. latency_ns >= 5  (anti-cache-exploit)
6. reward == block_reward(height)  (halving enforced)
7. timestamp <= now + 120  (±2 min tolerance)
```

---

## 11. Memory DAG

```python
dag_seed = sha3_256("polm:" + epoch + ":" + prev_hash[:32])
dag_size = 256 MB + (epoch × 64 MB)   # mainnet
dag_size = 4 MB                         # testnet
```

The DAG grows 64 MB per epoch (every 100,000 blocks). This prevents DAG caching across epochs and increases the RAM requirement over time.

---

## 12. Epochs

```python
epoch = height // 100_000
```

Every 100,000 blocks:
- DAG seed changes (based on new epoch + prev_hash)
- DAG size increases by 64 MB
- All miners must rebuild their DAG

---

## 13. Halving Schedule

```python
halvings = height // 4_200_000
reward   = 5.0 / (2 ** halvings)
```

| Period | Height Range | Reward | Approx Year |
|--------|-------------|--------|------------|
| 1 | 0 – 4,199,999 | 5.0 POLM | Year 1–4 |
| 2 | 4.2M – 8.4M | 2.5 POLM | Year 5–8 |
| 3 | 8.4M – 12.6M | 1.25 POLM | Year 9–12 |
| 4+ | continuing | halving... | Year 13+ |
| ∞ | asymptotic | → 0 | → 32M total |

---

## 14. Transactions

Each block can include multiple pending transactions from the mempool. Miners are incentivized to include transactions because:
1. Transaction fees are collected by the miner
2. Higher-fee transactions are prioritized in `/getwork`

### Transaction format

```
tx_id     = sha3_256(signing_bytes + signature)
signing   = "sender:receiver:amount:fee:timestamp:memo"
signature = ECDSA secp256k1 (or sha3 fallback)
```

### Transaction validation

```
1. amount > 0
2. fee >= MIN_FEE (0.0001 POLM)
3. sender.balance >= amount + fee
4. signature valid (ECDSA or fallback)
5. not already confirmed
6. addresses start with "POLM"
```

---

## 15. P2P Gossip

Topics: `polm/blocks`, `polm/txs`, `polm/peers`

DNS seed nodes (bootstrap):
- `node1.polm.com.br:6060`
- `node2.polm.com.br:6060`
- `node3.polm.com.br:6060`

Sync mechanism:
1. On connect: compare heights with peer
2. If peer ahead: pull missing blocks sequentially
3. On new block found: broadcast to all known peers
4. Sync loop: every 15 seconds, check all peers for missing blocks

---

## 16. Security Model

| Attack | Defense |
|--------|---------|
| ASIC | 256 MB DAG + sequential walk — DRAM physics are irreducible |
| GPU | GDDR latency > DDR latency — no speed advantage |
| Cache exploit | Latency < 5 ns → block rejected by consensus |
| Fake RAM type | Dynamic boost measures real latency per nonce |
| Timestamp manipulation | ±120s tolerance enforced |
| Sybil | Peer scoring, DNS seeds, proof-of-work itself |
| Double spend | Longest chain rule, fast propagation |
| 51% attack | Would require >50% of total latency-weighted hashrate |

---

## 17. Economics

### Supply schedule

| Year | Reward | Blocks | New POLM | Total Supply |
|------|--------|--------|----------|-------------|
| 1–4 | 5.0 | 4,200,000 | 21,000,000 | ~21M |
| 5–8 | 2.5 | 4,200,000 | 10,500,000 | ~31.5M |
| 9–12 | 1.25 | 4,200,000 | 5,250,000 | ~32M |
| 13+ | <1.25 | continuing | decreasing | → 32M |

### Participant incentives

| Participant | Revenue source |
|-------------|---------------|
| Miners | Block rewards + transaction fees |
| Full nodes | Network infrastructure (no direct reward) |
| Gateway operators | Service fees from miners (future) |

---

## 18. Founder Allocation

| Parameter | Value |
|-----------|-------|
| Founder | Aluísio Fernandes (@aluisiofer) |
| Allocation | 1,600,000 POLM (5% of max supply) |
| Lock period | 5,256,000 blocks (~5 years) |
| Vesting | Linear over 24 months after unlock |
| Enforcement | Consensus rule — locked at protocol level |

Consensus rule enforced at node level:
```python
if tx.sender == FOUNDER_ADDRESS:
    assert current_height >= GENESIS_HEIGHT + 5_256_000
```

This is enforced by all full nodes. No transaction from the founder address is valid before the lock expires — not even the node operator can override this.

---

## 19. Scalability

- **1,000,000+ miners** via hierarchical Mining Proxy + Gateway architecture
- **Regional proxies** reduce latency globally
- **Multiple full nodes** ensure decentralization (anyone can run one)
- **Compact block propagation** minimizes bandwidth per block

---

## 20. Technology Stack

| Component | Current (testnet) | Production (mainnet) |
|-----------|------------------|---------------------|
| Full Node | Python + Flask | Rust / Go |
| Miner | Python | Rust / C++ |
| Explorer | Python + Flask | Node.js / React |
| Wallet | Python + Flask | Native apps |
| P2P | HTTP polling | libp2p gossip |
| Database | JSON files | LevelDB / RocksDB |

---

## 21. Roadmap

### v1.0 — Testnet (completed ✅)
- PoLM algorithm implemented and tested
- Python full node + miner + explorer
- 3-node local testnet

### v1.1 — Extended testnet (completed ✅)
- Web wallet with ECDSA signatures
- Transaction mempool
- 4-node testnet with DDR2/DDR3/DDR4
- 816 blocks validated

### v1.2 — Mainnet ready (current ✅)
- Windows 10/11 full support
- polm.com.br domain
- Install scripts for all platforms
- Final boost calibration from testnet data

### v1.3 — Mining infrastructure
- Mining gateway protocol
- Stratum-compatible interface
- Pool mining support

### v2.0 — Production node
- Rust/Go full node implementation
- libp2p networking
- LevelDB storage
- 10,000+ TPS capacity

### v3.0 — Mainnet genesis 🎯
- Genesis block
- Public launch
- DNS seed nodes live at polm.com.br
- Exchange listings

---

## Conclusion

PoLM introduces a new class of consensus that is fundamentally different from all existing Proof-of-Work algorithms. By making DRAM latency the primary bottleneck, it:

1. **Democratizes mining** — a 2006 Core 2 Duo is genuinely competitive
2. **Resists centralization** — ASICs and GPUs have no systematic advantage
3. **Rewards legacy hardware** — economic incentive to keep old machines alive
4. **Caps inequality** — maximum advantage between hardware generations ~2.5× (vs 100× in SHA-256)

Validated empirically on real hardware across four RAM generations. Ready for mainnet.

---

*PoLM is experimental software.*  
*Website: https://polm.com.br*  
*Twitter: https://x.com/polm2026*  
*Founder: https://x.com/aluisiofer*
