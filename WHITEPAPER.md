# Proof of Legacy Memory (PoLM)

## Abstract

Proof of Legacy Memory is an experimental blockchain protocol designed
to make old hardware economically useful again.

Instead of favouring modern GPUs and ASICs, PoLM attempts to balance
mining efficiency across generations of hardware.

Older CPUs and memory architectures such as DDR2 and DDR3 can still
participate in the network.

## Motivation

Modern proof-of-work systems quickly obsolete hardware.

PoLM attempts to reverse this by designing workloads that
remain usable on legacy systems.

This helps reduce electronic waste and improves decentralization.

## Mining Model

PoLM mining uses:

• CPU hashing
• memory access patterns
• latency oriented workload

Nodes perform repeated hash attempts while accessing memory buffers.

## Block Structure

Blocks contain:

hash  
parent hash  
miner address  
reward  
timestamp  

## Supply

Total supply: 32,000,000 PoLM

Inspired by the 32-bit hardware era.

## Network

Nodes communicate using TCP peer discovery.

Peers broadcast blocks across the network.

## Status

Experimental research protocol.
