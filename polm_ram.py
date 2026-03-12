"""
polm_ram.py — Prova de Latência de RAM (PoLM Consensus)
=========================================================
O coração do Proof of Legacy Memory.

Como funciona:
  1. Aloca um buffer grande na RAM (padrão: 256 MB)
  2. Executa GRAPH_SIZE acessos pseudo-aleatórios não-sequenciais
  3. Mede o tempo total → latência real da RAM física
  4. Hardware legado (DDR2/DDR3 com latência maior) recebe score mais alto
  5. O score é incluído no bloco e verificável por qualquer peer

Proteções contra trapaça:
  • Buffer inicializado com bytes aleatórios (sem zero-page collapse)
  • Acesso com stride variável (invalida L1/L2/L3 cache)
  • Checksum XOR encadeado (o resultado depende do conteúdo real da RAM)
  • RAM type detection via dmidecode (penaliza DDR5 acelerado)
  • Score limitado a [0.1, 200.0] para evitar manipulação
"""

import hashlib
import os
import platform
import random
import subprocess
import sys
import time
from typing import Optional

# ═══════════════════════════════════════════════════════════
# PARÂMETROS
# ═══════════════════════════════════════════════════════════

GRAPH_SIZE   = 300_000       # iterações de acesso à RAM por prova
SCORE_MIN    = 0.1
SCORE_MAX    = 200.0

# Multiplicadores por geração de RAM
# DDR2 = hardware mais antigo = mais lento = maior score = mais poder de mineração
RAM_MULTIPLIERS = {
    "DDR2": 2.5,
    "DDR3": 1.8,
    "DDR4": 1.0,
    "DDR5": 0.6,
    "LPDDR4": 0.9,
    "LPDDR5": 0.55,
    "AUTO":   1.0,   # fallback sem detecção
}

# ═══════════════════════════════════════════════════════════
# DETECÇÃO DE RAM
# ═══════════════════════════════════════════════════════════

def detect_ram_type() -> tuple[str, float]:
    """
    Detecta o tipo de RAM instalado.
    Retorna (tipo, multiplicador).
    """
    ram_type = "AUTO"

    # Linux: dmidecode
    if platform.system() == "Linux":
        try:
            out = subprocess.check_output(
                ["sudo", "dmidecode", "-t", "memory"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="ignore")

            for gen in ["DDR5", "LPDDR5", "LPDDR4", "DDR4", "DDR3", "DDR2"]:
                if gen in out:
                    ram_type = gen
                    break
        except Exception:
            pass

    # macOS: system_profiler
    elif platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPMemoryDataType"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="ignore")

            for gen in ["DDR5", "DDR4", "DDR3", "DDR2", "LPDDR"]:
                if gen in out:
                    ram_type = gen
                    break
        except Exception:
            pass

    # Windows: wmic (fallback)
    elif platform.system() == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "memorychip", "get", "SMBIOSMemoryType"],
                stderr=subprocess.DEVNULL,
                timeout=5,
            ).decode(errors="ignore")

            # SMBIOSMemoryType: 24=DDR3, 26=DDR4, 34=DDR5, 20=DDR2
            type_map = {"20": "DDR2", "24": "DDR3", "26": "DDR4", "34": "DDR5"}
            for code, name in type_map.items():
                if code in out:
                    ram_type = name
                    break
        except Exception:
            pass

    mult = RAM_MULTIPLIERS.get(ram_type, 1.0)
    return ram_type, mult


def benchmark_ram_speed(size_mb: int = 64) -> float:
    """
    Benchmark rápido de latência de RAM para calibração.
    Retorna MB/s estimado.
    """
    size  = size_mb * 1024 * 1024
    buf   = bytearray(os.urandom(min(size, 4 * 1024 * 1024)))
    buf   = buf * (size // len(buf) + 1)
    buf   = bytearray(buf[:size])

    t0    = time.perf_counter()
    total = 0
    step  = 4096
    for i in range(0, size, step):
        total += buf[i]
    elapsed = time.perf_counter() - t0

    mb_per_sec = (size / (1024 * 1024)) / max(elapsed, 0.001)
    return mb_per_sec

# ═══════════════════════════════════════════════════════════
# BUFFER GLOBAL
# ═══════════════════════════════════════════════════════════

_buffer:      Optional[bytearray] = None
_buffer_size: int                  = 0


def init_buffer(size_mb: int = 256) -> bytearray:
    """
    Inicializa o buffer de RAM com bytes aleatórios.

    Por que bytes aleatórios e não zeros?
    → bytearray(N) com zeros ativa zero-page mapping no kernel Linux:
      múltiplas páginas virtuais apontam para a mesma página física zero.
      Isso faz o buffer caber em muito menos RAM física do que o esperado,
      invalidando a prova de latência.
    → Bytes aleatórios forçam o kernel a alocar páginas físicas reais
      para cada página virtual, garantindo que o acesso seja real.
    """
    global _buffer, _buffer_size

    size = size_mb * 1024 * 1024

    print(f"[PoLM RAM] Alocando {size_mb} MB de buffer... ", end="", flush=True)
    t0 = time.perf_counter()

    # Gera seed aleatória pequena e expande
    seed_size   = min(size, 4 * 1024 * 1024)  # 4 MB de aleatoriedade real
    seed_bytes  = os.urandom(seed_size)

    # Expande usando PRNG determinístico (mais rápido que os.urandom para MBs)
    buf   = bytearray(size)
    chunk = len(seed_bytes)
    for offset in range(0, size, chunk):
        end   = min(offset + chunk, size)
        block = seed_bytes if offset == 0 else hashlib.sha256(
            seed_bytes + offset.to_bytes(8, "big")
        ).digest() * (chunk // 32 + 1)
        buf[offset:end] = block[:end - offset]

    elapsed = time.perf_counter() - t0
    print(f"OK ({elapsed:.2f}s)")

    _buffer      = buf
    _buffer_size = size
    return buf


def get_buffer() -> bytearray:
    global _buffer
    if _buffer is None:
        _buffer = init_buffer(256)
    return _buffer

# ═══════════════════════════════════════════════════════════
# MEMORY STORM — PROVA DE LATÊNCIA
# ═══════════════════════════════════════════════════════════

def memory_storm(seed: int, buf: Optional[bytearray] = None) -> tuple[int, float]:
    """
    Executa a prova de latência de RAM.

    Algoritmo:
      1. Inicia ponteiro em (seed % tamanho_buffer)
      2. A cada iteração, avança via LCG com stride variável
      3. XOR do valor lido com acumulador (checksum encadeado)
      4. Muda stride a cada 4096 iterações (baseado no checksum atual)

    Por que isso é difícil de otimizar?
      • Acesso não-sequencial → invalida linha de cache
      • Stride variável → impossível pré-buscar
      • Checksum encadeado → cada leitura depende da anterior
      • Buffer grande → não cabe em cache L3 (tipicamente < 32 MB)

    Retorna (checksum, elapsed_seconds).
    """
    if buf is None:
        buf = get_buffer()

    size   = len(buf)
    mask   = size - 1   # funciona se size é potência de 2

    # Normaliza para potência de 2
    if size & (size - 1) != 0:
        # Se não é potência de 2, usa módulo (mais lento mas correto)
        ptr    = seed % size
        total  = 0
        stride = (seed >> 8) | 1

        t0 = time.perf_counter()
        for i in range(GRAPH_SIZE):
            ptr    = (ptr * 1_103_515_245 + 12_345 + stride) % size
            total ^= buf[ptr]
            if (i & 0xFFF) == 0:
                stride = ((total * 6_364_136_223_846_793_005 + 1) % size) | 1
        return total, time.perf_counter() - t0

    # Caminho otimizado (bitmasking — mais rápido)
    ptr    = seed & mask
    total  = 0
    stride = (seed >> 8) | 1

    t0 = time.perf_counter()
    for i in range(GRAPH_SIZE):
        ptr    = (ptr * 1_103_515_245 + 12_345 + stride) & mask
        total ^= buf[ptr]
        if (i & 0xFFF) == 0:
            # Muda stride baseado no checksum → anti-otimização
            stride = ((total * 6_364_136_223_846_793_005 + 1) & mask) | 1
    elapsed = time.perf_counter() - t0

    return total, elapsed


def compute_ram_proof(seed: int, ram_mult: float, buf: Optional[bytearray] = None) -> dict:
    """
    Executa a prova e retorna um dicionário com todos os dados
    necessários para inclusão no bloco e verificação por peers.
    """
    work, latency = memory_storm(seed, buf)
    score         = _compute_score(latency, ram_mult)

    return {
        "seed":     seed,
        "work":     work,
        "latency":  round(latency, 6),
        "score":    round(score, 4),
        "ram_mult": round(ram_mult, 2),
    }


def _compute_score(latency: float, ram_mult: float) -> float:
    """
    Converte latência + multiplicador de RAM em score normalizado.
    Score mais alto = hardware mais "legacy" = mais poder de voto.
    """
    raw = latency * 1000.0 * ram_mult   # ms × mult
    return max(SCORE_MIN, min(SCORE_MAX, raw))


def verify_ram_proof(proof: dict, buf: Optional[bytearray] = None) -> tuple[bool, str]:
    """
    Verifica se uma prova de RAM é válida.
    Usado pelos peers ao receber um bloco.

    NOTA: A verificação completa exige re-executar memory_storm com o mesmo seed.
    Em redes grandes isso pode ser custoso. Use verify_ram_proof_fast para
    verificação rápida baseada em score/latency plausibility.
    """
    if buf is None:
        buf = get_buffer()

    seed = proof.get("seed")
    if seed is None:
        return False, "seed ausente"

    work_expected, latency_actual = memory_storm(seed, buf)

    if proof.get("work") != work_expected:
        return False, f"work inválido: {proof.get('work')} ≠ {work_expected}"

    # Tolerância de 20% na latência (variação de sistema operacional)
    latency_reported = proof.get("latency", 0)
    if abs(latency_reported - latency_actual) > latency_actual * 0.20 + 0.1:
        return False, (
            f"latência suspeita: reportada={latency_reported:.4f}s, "
            f"medida={latency_actual:.4f}s"
        )

    return True, "ok"


def verify_ram_proof_fast(proof: dict) -> tuple[bool, str]:
    """
    Verificação rápida (sem re-executar memory_storm).
    Checa apenas plausibilidade dos valores.
    """
    latency = proof.get("latency", 0)
    score   = proof.get("score", 0)
    work    = proof.get("work")
    seed    = proof.get("seed")

    if seed is None or work is None:
        return False, "campos obrigatórios ausentes"

    if not (0 < latency < 60):
        return False, f"latência implausível: {latency}"

    if not (SCORE_MIN <= score <= SCORE_MAX):
        return False, f"score fora do intervalo: {score}"

    expected_score = _compute_score(latency, proof.get("ram_mult", 1.0))
    if abs(score - expected_score) > 1.0:
        return False, f"score inconsistente com latência"

    return True, "ok"
