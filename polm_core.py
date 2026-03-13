"""
polm_core.py — PoLM Blockchain Core v1.1
==========================================
CHANGELOG v1.1:
  - Genesis message corrigida (Aluisio Fernandes 'Aluminium')
  - validate_tx_structure: exige campo 'signatures' em txs não-coinbase
  - validate_block_structure: verifica altura sequencial
  - Replay attack: txs incluem chain_id no hash
  - Constantes de rede ajustadas para lançamento público
  - Bootstrap seeds removidos de IPs locais
  - MAX_REORG_DEPTH: limita reorganização a 100 blocos
"""

import hashlib
import json
import os
import time
from typing import Optional

# ═══════════════════════════════════════════════════════════
# CONSTANTES IMUTÁVEIS DA REDE
# ═══════════════════════════════════════════════════════════

NETWORK_VERSION   = 1
NETWORK_MAGIC     = 0xD9B4BEF9
CHAIN_ID          = "polm-mainnet-1"     # anti replay attack
COIN              = 100_000_000
MAX_SUPPLY_COINS  = 32_000_000
MAX_SUPPLY_SATS   = MAX_SUPPLY_COINS * COIN

INITIAL_REWARD_SATS = 50 * COIN
HALVING_INTERVAL    = 210_000

TARGET_BLOCK_TIME   = 60
DIFFICULTY_WINDOW   = 144
MIN_DIFFICULTY      = 10
MAX_DIFFICULTY      = 22               # teto realista para 2 PCs DDR4
INITIAL_DIFFICULTY  = 14

MAX_BLOCK_SIZE      = 1_000_000
MAX_TX_PER_BLOCK    = 4_000
MAX_MEMPOOL_SIZE    = 50_000
COINBASE_MATURITY   = 100
MAX_REORG_DEPTH     = 100              # FIX: limita reorganização maliciosa

DEFAULT_PORT        = 5555
MAX_PEERS           = 125
MAX_PEERS_FROM_MSG  = 50               # FIX: limita lista de peers recebida
PROTOCOL_VERSION    = "PoLM/1.1"

CHAIN_FILE          = "polm_chain.db"
UTXO_FILE           = "polm_utxo.db"
PEERS_FILE          = "polm_peers.json"
WALLET_FILE         = "polm_wallet.json"

# ═══════════════════════════════════════════════════════════
# HASHING
# ═══════════════════════════════════════════════════════════

def sha256d(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def sha256d_hex(data: bytes) -> str:
    return sha256d(data).hex()

def hash_block_header(header: dict) -> str:
    fields = (
        header["version"],
        header["prev_hash"],
        header["merkle_root"],
        header["timestamp"],
        header["difficulty"],
        header["nonce"],
        header.get("ram_proof", ""),
    )
    raw = "|".join(str(f) for f in fields).encode()
    return sha256d_hex(raw)

def hash_transaction(tx: dict) -> str:
    """
    Hash da transação incluindo CHAIN_ID para prevenir replay attacks.
    Exclui campos 'txid' e 'signatures' do hash (como Bitcoin).
    """
    clean = {k: v for k, v in tx.items() if k not in ("txid", "signatures")}
    clean["_chain_id"] = CHAIN_ID      # FIX: anti replay attack
    raw = json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    return sha256d_hex(raw)

def merkle_root(txids: list) -> str:
    if not txids:
        return "0" * 64

    def _ensure_hex64(s: str) -> str:
        if len(s) == 64:
            try:
                int(s, 16)
                return s
            except ValueError:
                pass
        return hashlib.sha256(s.encode()).hexdigest()

    layer = [_ensure_hex64(t) for t in txids]
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        layer = [
            sha256d_hex(bytes.fromhex(layer[i]) + bytes.fromhex(layer[i+1]))
            for i in range(0, len(layer), 2)
        ]
    return layer[0]

# ═══════════════════════════════════════════════════════════
# RECOMPENSA
# ═══════════════════════════════════════════════════════════

def block_reward_sats(height: int) -> int:
    halvings = height // HALVING_INTERVAL
    if halvings >= 64:
        return 0
    return INITIAL_REWARD_SATS >> halvings

# ═══════════════════════════════════════════════════════════
# DIFICULDADE
# ═══════════════════════════════════════════════════════════

def bits_to_target(bits: int) -> int:
    return 2 ** (256 - bits)

def hash_meets_target(h: str, bits: int) -> bool:
    return int(h, 16) < bits_to_target(bits)

def calculate_next_difficulty(last_blocks: list) -> int:
    if len(last_blocks) < 2:
        return INITIAL_DIFFICULTY

    window   = last_blocks[-min(DIFFICULTY_WINDOW, len(last_blocks)):]
    elapsed  = window[-1]["timestamp"] - window[0]["timestamp"]
    expected = TARGET_BLOCK_TIME * (len(window) - 1)

    if elapsed <= 0 or expected <= 0:
        return INITIAL_DIFFICULTY

    current_diff = window[-1].get("difficulty", INITIAL_DIFFICULTY)
    ratio        = elapsed / expected
    ratio        = max(0.5, min(2.0, ratio))   # muda no máx 1 bit por janela

    import math
    new_diff = current_diff - math.log2(ratio)
    new_diff = max(MIN_DIFFICULTY, min(MAX_DIFFICULTY, round(new_diff)))
    return int(new_diff)

# ═══════════════════════════════════════════════════════════
# VALIDAÇÃO DE TRANSAÇÃO
# ═══════════════════════════════════════════════════════════

def validate_tx_structure(tx: dict) -> tuple:
    if not isinstance(tx, dict):
        return False, "tx não é um objeto"

    required = {"version", "inputs", "outputs", "locktime"}
    missing  = required - tx.keys()
    if missing:
        return False, f"campos faltando: {missing}"

    if not isinstance(tx["inputs"], list) or not tx["inputs"]:
        return False, "inputs inválidos"

    if not isinstance(tx["outputs"], list) or not tx["outputs"]:
        return False, "outputs inválidos"

    is_cb = _is_coinbase(tx)

    # FIX: transações não-coinbase DEVEM ter assinaturas
    if not is_cb:
        sigs = tx.get("signatures", [])
        if not sigs or not isinstance(sigs, list):
            return False, "transação sem assinaturas"
        for sig in sigs:
            if "pubkey" not in sig or "sig" not in sig:
                return False, "assinatura mal formada"

    for i, inp in enumerate(tx["inputs"]):
        if not isinstance(inp, dict):
            return False, f"input {i} inválido"
        if not is_cb:
            if "txid" not in inp or "vout" not in inp:
                return False, f"input {i} sem txid/vout"
            if not isinstance(inp["vout"], int) or inp["vout"] < 0:
                return False, f"input {i} vout inválido"

    for i, out in enumerate(tx["outputs"]):
        if not isinstance(out, dict):
            return False, f"output {i} inválido"
        if "value" not in out or "address" not in out:
            return False, f"output {i} sem value/address"
        if not isinstance(out["value"], int) or out["value"] <= 0:
            return False, f"output {i} value inválido"
        if not isinstance(out["address"], str) or len(out["address"]) < 20:
            return False, f"output {i} address inválido"

    total_out = sum(o["value"] for o in tx["outputs"])
    if total_out > MAX_SUPPLY_SATS:
        return False, "outputs excedem supply máximo"

    # FIX: locktime deve ser inteiro
    if not isinstance(tx.get("locktime"), int):
        return False, "locktime inválido"

    return True, "ok"

# ═══════════════════════════════════════════════════════════
# VALIDAÇÃO DE BLOCO
# ═══════════════════════════════════════════════════════════

def validate_block_structure(block: dict, prev_block: dict = None) -> tuple:
    required = {
        "version", "height", "prev_hash", "merkle_root",
        "timestamp", "difficulty", "nonce", "hash",
        "miner", "transactions", "ram_proof", "ram_score",
    }
    missing = required - block.keys()
    if missing:
        return False, f"campos faltando: {missing}"

    # FIX: versão deve ser compatível
    if block["version"] != NETWORK_VERSION:
        return False, f"versão incompatível: {block['version']}"

    # Hash
    computed = hash_block_header(block)
    if computed != block["hash"]:
        return False, f"hash inválido"

    # PoW
    if not hash_meets_target(block["hash"], block["difficulty"]):
        return False, f"PoW insuficiente"

    # FIX: dificuldade dentro dos limites
    if not (MIN_DIFFICULTY <= block["difficulty"] <= MAX_DIFFICULTY):
        return False, f"dificuldade fora dos limites: {block['difficulty']}"

    # FIX: altura sequencial
    if prev_block and block["height"] != prev_block["height"] + 1:
        return False, f"altura não sequencial"

    # Merkle root
    txids       = [tx.get("txid", hash_transaction(tx)) for tx in block["transactions"]]
    computed_mr = merkle_root(txids)
    if computed_mr != block["merkle_root"]:
        return False, "merkle_root inválido"

    if not block["transactions"]:
        return False, "bloco sem transações"

    if len(block["transactions"]) > MAX_TX_PER_BLOCK:
        return False, "excesso de transações"

    # Coinbase
    coinbase = block["transactions"][0]
    if not _is_coinbase(coinbase):
        return False, "primeira tx não é coinbase"

    # FIX: apenas uma coinbase por bloco
    for tx in block["transactions"][1:]:
        if _is_coinbase(tx):
            return False, "múltiplas coinbase no bloco"

    # Valida estrutura de cada tx
    for i, tx in enumerate(block["transactions"]):
        ok, reason = validate_tx_structure(tx)
        if not ok:
            return False, f"tx {i}: {reason}"

    # Timestamp
    if block["timestamp"] > time.time() + 7200:
        return False, "timestamp no futuro"

    if prev_block and block["timestamp"] < prev_block["timestamp"] - 600:
        return False, "timestamp retroativo"

    # FIX: endereço do minerador deve ser válido
    if not isinstance(block["miner"], str) or len(block["miner"]) < 20:
        return False, "endereço do minerador inválido"

    return True, "ok"

def _is_coinbase(tx: dict) -> bool:
    inputs = tx.get("inputs", [])
    return (
        len(inputs) == 1
        and inputs[0].get("txid") == "0" * 64
        and inputs[0].get("vout") == -1
    )

# ═══════════════════════════════════════════════════════════
# GENESIS BLOCK
# ═══════════════════════════════════════════════════════════

def create_genesis_block() -> dict:
    genesis_message = (
        "PoLM 2025 — Aluisio Fernandes 'Aluminium' — "
        "Hardware antigo nao morre, ele minera. "
        "DDR2 tem valor. Cada ciclo de RAM e prova de vida."
    )

    coinbase_tx = {
        "version": 1,
        "inputs": [{
            "txid":     "0" * 64,
            "vout":     -1,
            "coinbase": genesis_message.encode().hex(),
            "sequence": 0xFFFFFFFF,
        }],
        "outputs": [{
            "value":   INITIAL_REWARD_SATS,
            "address": "PoLM1Genesis0000000000000000000000000000000",
        }],
        "locktime": 0,
    }
    coinbase_tx["txid"] = hash_transaction(coinbase_tx)

    genesis = {
        "version":      NETWORK_VERSION,
        "height":       0,
        "prev_hash":    "0" * 64,
        "timestamp":    1_700_000_000,
        "difficulty":   INITIAL_DIFFICULTY,
        "nonce":        0,
        "miner":        "PoLM-Genesis-Aluminium",
        "transactions": [coinbase_tx],
        "ram_proof":    "genesis",
        "ram_score":    0.0,
    }

    txids                = [coinbase_tx["txid"]]
    genesis["merkle_root"] = merkle_root(txids)
    genesis["hash"]      = "00000000" + "0" * 56
    return genesis
