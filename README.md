# PoLM — Proof of Legacy Memory

**Blockchain com consenso por Latência de RAM**  
Hardware antigo (DDR2, DDR3) tem vantagem na mineração.  
Supply total: **32.000.000 PoLM** (como os 32 bits da era clássica).

---

## Instalação Rápida

```bash
# 1. Instale as dependências
pip install -r requirements.txt

# 2. Crie sua wallet
python3 polm_wallet.py create

# 3. Inicie o nó + minerador
python3 polm_node.py

# 4. (Opcional) Abra o explorer
python3 polm_explorer.py
# Acesse: http://localhost:5000
```

---

## Estrutura do Projeto

```
polm_core.py      — Constantes, hashing, validação, genesis block
polm_wallet.py    — Carteira HD (24 palavras, ECDSA secp256k1)
polm_ram.py       — Prova de Latência de RAM (consenso PoLM)
polm_chain.py     — Blockchain + UTXO set + armazenamento
polm_network.py   — Rede P2P (peers, broadcast, sync)
polm_node.py      — Nó completo (minerador + mempool + integração)
polm_explorer.py  — Block explorer web
requirements.txt  — Dependências Python
```

---

## Arquitetura do Consenso (Proof of Legacy Memory)

### Como funciona a mineração

1. **Detecção de RAM**: O nó identifica automaticamente o tipo de RAM (DDR2/3/4/5)
2. **Memory Storm**: Executa 300.000 acessos pseudo-aleatórios ao buffer RAM
3. **Score de latência**: RAM mais lenta = score mais alto = maior chance de encontrar bloco
4. **PoW combinado**: O hash do bloco deve satisfazer a dificuldade atual (bits zero)

### Multiplicadores por geração de RAM

| Geração | Mult. | Vantagem |
|---------|-------|----------|
| DDR2    | 2.5×  | +++      |
| DDR3    | 1.8×  | ++       |
| DDR4    | 1.0×  | neutro   |
| DDR5    | 0.6×  | penalizado |

### Por que isso não pode ser trapaceado

- Buffer de 256 MB de bytes aleatórios (sem zero-page collapse)
- Acesso com stride variável (invalida L1/L2/L3 cache)
- Checksum encadeado (cada leitura depende da anterior)
- Resultado do `work` é verificável por qualquer peer re-executando com o mesmo seed

---

## Supply e Emissão (como Bitcoin)

- **Supply total**: 32.000.000 PoLM
- **Recompensa inicial**: 50 PoLM/bloco
- **Halving**: a cada 210.000 blocos
- **Tempo alvo**: 60 segundos/bloco
- **Duração estimada**: ~100 anos até supply esgotado

```
Epoch  0 (blocos       0 – 209.999): 50,0 PoLM/bloco
Epoch  1 (blocos 210.000 – 419.999): 25,0 PoLM/bloco
Epoch  2 (blocos 420.000 – 629.999): 12,5 PoLM/bloco
...
```

---

## Wallet (Carteira HD)

A wallet usa criptografia padrão da indústria:

- **Seed de 24 palavras** (BIP-39, PBKDF2-HMAC-SHA512)
- **Chaves ECDSA secp256k1** (mesma curva do Bitcoin)
- **Endereços Base58Check** (checksum embutido, à prova de erro de digitação)
- **Múltiplos endereços** derivados da mesma seed

```bash
# Criar wallet
python3 polm_wallet.py create

# Ver endereços
python3 polm_wallet.py info

# Endereço para receber
python3 polm_wallet.py receive

# Backup criptografado (AES-256-GCM)
python3 polm_wallet.py export --password SUASENHA

# Restaurar de backup
python3 polm_wallet.py import --file polm_wallet_backup.json --password SUASENHA
```

---

## Nó (Node)

```bash
# Nó completo com mineração (padrão)
python3 polm_node.py

# Hardware limitado
python3 polm_node.py --threads 1 --ram 128

# Nó relay (sem mineração)
python3 polm_node.py --no-mine

# Endereço explícito
python3 polm_node.py --address SEU_ENDERECO_POLM

# Debug
python3 polm_node.py --debug
```

---

## Segurança

### Proteções implementadas

| Vetor de ataque | Proteção |
|---|---|
| Hash falso no bloco | Hash cobre todos os campos (version, prev_hash, merkle_root, ts, diff, nonce, ram_proof) |
| Transação forjada | ECDSA secp256k1 + TXID = hash da tx |
| Double spend | UTXO set indexado, verificado antes de aceitar bloco |
| Fork 51% | Regra da cadeia mais longa (Nakamoto) + detecção de reorganização |
| Peer malicioso | Rate limiting (100 msg/s) + banimento temporário + score de confiança |
| DoS via bloco gigante | Limite de 2 MB por mensagem P2P + 4000 TXs por bloco |
| Mempool spam | Ordenação por taxa + limite de 50.000 TXs |
| Buffer RAM otimizado | Bytes aleatórios (anti zero-page mapping) |
| Coinbase imatura | Maturidade de 100 blocos para gastar recompensa |
| Timestamp manipulation | Máximo 2h no futuro, não pode ser retroativo |
| Supply infinito | Halving idêntico ao Bitcoin, verificado por cada nó |

### .gitignore obrigatório

```
polm_wallet.json
polm_chain.db
polm_utxo.db
polm_peers.json
polm_node.log
*.tmp
__pycache__/
*.pyc
```

---

## Protocolo P2P

Mensagens:
```
VERSION   — handshake (versão, altura)
VERACK    — confirma handshake
GETBLOCKS — pede blocos por hash conhecido
BLOCK     — envia bloco completo
TX        — anuncia transação
GETPEERS  — pede lista de peers
PEERS     — envia lista de peers
PING/PONG — keep-alive
```

---

## Estrutura de um Bloco

```json
{
  "version": 1,
  "height": 1000,
  "prev_hash": "00000...",
  "merkle_root": "abc123...",
  "timestamp": 1700001000,
  "difficulty": 22,
  "nonce": 48291,
  "miner": "PoLM1xyz...",
  "transactions": [...],
  "ram_proof": 3847291,
  "ram_score": 12.45,
  "ram_seed": 1234567,
  "ram_latency": 0.0834,
  "ram_type": "DDR3",
  "hash": "00000abc..."
}
```

---

## Licença

MIT — livre para uso, modificação e distribuição.
