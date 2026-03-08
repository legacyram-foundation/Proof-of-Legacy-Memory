# Proof of Legacy Memory (PoLM)

## Abstract

Proof of Legacy Memory is an experimental blockchain protocol designed
to make old hardware economically useful again.

Instead of favouring high-end GPUs or ASICs, PoLM attempts to
balance mining performance across generations of hardware.

Older CPUs and memory architectures such as DDR2 and DDR3
remain capable of participating in the network.

## Motivation

Modern proof-of-work systems rapidly obsolete hardware.

PoLM attempts to reverse this by designing workloads that
remain efficient on legacy systems.

This reduces electronic waste and increases decentralization.

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

Peers broadcast new blocks across the network.

## Status

Experimental research protocol.
