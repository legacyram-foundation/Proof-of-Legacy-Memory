# PoLM — Proof of Latency Mining

Author: Aluisio Fernandes de Souza

## Abstract

PoLM (Proof of Latency Mining) is a blockchain consensus algorithm designed to utilize real hardware latency characteristics, particularly memory access latency, as a source of computational work.

Unlike traditional Proof-of-Work systems that rely heavily on raw hash power or GPU parallelism, PoLM attempts to balance mining by emphasizing memory latency and unpredictable memory access patterns.

This approach allows older hardware, especially systems with lower memory latency, to remain competitive in the mining process.

## Motivation

Modern mining algorithms often lead to:

- GPU centralization
- ASIC domination
- high energy consumption

PoLM attempts to mitigate these problems by using:

- random memory traversal
- latency-sensitive workloads
- hardware fingerprinting

This encourages a wider distribution of mining hardware.

## Core Principles

PoLM relies on three main elements:

1. **Memory Latency Workload**

The miner performs a pointer-chasing workload across memory, generating unpredictable access patterns.

2. **Latency Measurement**

The time required to complete the workload becomes part of the block scoring mechanism.

3. **Hardware Fingerprint**

Each miner generates a hardware fingerprint derived from CPU characteristics and memory behavior.

## Block Structure

Example block:
# PoLM — Proof of Latency Mining

Author: Aluisio Fernandes de Souza

## Abstract

PoLM (Proof of Latency Mining) is a blockchain consensus algorithm designed to utilize real hardware latency characteristics, particularly memory access latency, as a source of computational work.

Unlike traditional Proof-of-Work systems that rely heavily on raw hash power or GPU parallelism, PoLM attempts to balance mining by emphasizing memory latency and unpredictable memory access patterns.

This approach allows older hardware, especially systems with lower memory latency, to remain competitive in the mining process.

## Motivation

Modern mining algorithms often lead to:

- GPU centralization
- ASIC domination
- high energy consumption

PoLM attempts to mitigate these problems by using:

- random memory traversal
- latency-sensitive workloads
- hardware fingerprinting

This encourages a wider distribution of mining hardware.

## Core Principles

PoLM relies on three main elements:

1. **Memory Latency Workload**

The miner performs a pointer-chasing workload across memory, generating unpredictable access patterns.

2. **Latency Measurement**

The time required to complete the workload becomes part of the block scoring mechanism.

3. **Hardware Fingerprint**

Each miner generates a hardware fingerprint derived from CPU characteristics and memory behavior.

## Block Structure

Example block:
# PoLM — Proof of Latency Mining

Author: Aluisio Fernandes de Souza

## Abstract

PoLM (Proof of Latency Mining) is a blockchain consensus algorithm designed to utilize real hardware latency characteristics, particularly memory access latency, as a source of computational work.

Unlike traditional Proof-of-Work systems that rely heavily on raw hash power or GPU parallelism, PoLM attempts to balance mining by emphasizing memory latency and unpredictable memory access patterns.

This approach allows older hardware, especially systems with lower memory latency, to remain competitive in the mining process.

## Motivation

Modern mining algorithms often lead to:

- GPU centralization
- ASIC domination
- high energy consumption

PoLM attempts to mitigate these problems by using:

- random memory traversal
- latency-sensitive workloads
- hardware fingerprinting

This encourages a wider distribution of mining hardware.

## Core Principles

PoLM relies on three main elements:

1. **Memory Latency Workload**

The miner performs a pointer-chasing workload across memory, generating unpredictable access patterns.

2. **Latency Measurement**

The time required to complete the workload becomes part of the block scoring mechanism.

3. **Hardware Fingerprint**

Each miner generates a hardware fingerprint derived from CPU characteristics and memory behavior.

## Block Structure

Example block:

## Mining Process

1. Generate seed
2. Traverse memory graph
3. Measure latency
4. Compute block score
5. Attempt hash threshold

If successful, the block is broadcast to peers.

## Advantages

- reduces GPU advantage
- supports older hardware
- encourages decentralized mining
- enables experimental latency-based consensus

## Future Work

- DAG scaling
- hardware reputation system
- adaptive difficulty
- real transaction layer
- PoLM testnet

## Conclusion

PoLM introduces a new direction for blockchain consensus by incorporating hardware latency characteristics into the mining process.

This work serves as an experimental foundation for further research into hardware-aware consensus mechanisms.
