# PoLM — Proof of Legacy Memory

> *"Hardware antigo não morre, ele minera. DDR2 tem valor. Cada ciclo de RAM é prova de vida."*  
> — Aluisio Fernandes "Aluminium", bloco genesis PoLM #0

---

## ⚠️ Licença Proprietária

**© 2025 Aluisio Fernandes "Aluminium" — Todos os direitos reservados.**

Este projeto é distribuído sob a **Licença Proprietária PoLM v1.0**.  
É **proibido** copiar, fazer fork, rebrandear ou criar projetos derivados sem autorização escrita do fundador.  
Veja o arquivo [LICENSE](LICENSE) para os termos completos.

---

## O que é o PoLM?

**PoLM (Proof of Legacy Memory)** é uma blockchain descentralizada com um mecanismo de consenso único no mundo: **Prova de Latência de RAM**.

Diferente do Bitcoin (favorece hardware novo e caro) e do Ethereum (favorece quem tem mais dinheiro), o PoLM **inverte a lógica**:

| Tipo de RAM | Multiplicador | Hardware |
|-------------|:------------:|---------|
| DDR2 | **2.5x** | PCs 2004–2009 |
| DDR3 | **1.8x** | PCs 2007–2014 |
| DDR4 | **1.0x** | PCs 2014–2020 |
| DDR5 | **0.6x** | PCs 2021+ |

**Um Core 2 Duo com DDR2 de 2005 minera 2.5x mais que um PC novo.**

---

## Para que serve o PoLM?

Além da mineração, o PoLM é uma **infraestrutura global de registro de propriedade**:

- 🏠 **Imóveis** — registro imutável de casas, terrenos, apartamentos
- 🚗 **Veículos** — carros, motos, caminhões
- 📄 **Contratos** — acordos, participação societária, patentes
- 🎨 **Direitos autorais** — música, arte, código, projetos
- 🪪 **Identidade digital** — certificados, diplomas, documentos

Qualquer registro é **imutável**, **verificável** e **permanente** — sem cartório, sem fronteiras.

---

## Segurança

O PoLM usa múltiplas camadas de proteção contra trapaça:

- 🔒 **Anti-VM** — detecta e bloqueia VMware, VirtualBox, QEMU, WSL, Docker, KVM
- 🔑 **Fingerprint físico** — cada prova é vinculada ao hardware real (motherboard, CPU, RAM)
- 📊 **Validação de latência** — detecta quem falsifica o tipo de RAM
- 🔄 **Anti-replay** — provas antigas não podem ser reutilizadas
- ⛓️ **Anti-reorg** — reorganização de cadeia limitada a 100 blocos

---

## Especificações Técnicas

| Parâmetro | Valor |
|-----------|-------|
| Supply máximo | 32.000.000 POLM |
| Recompensa inicial | 50 POLM/bloco |
| Halving | A cada 210.000 blocos |
| Tempo alvo | 60 segundos/bloco |
| Porta P2P | 5555 |
| Algoritmo | Proof of Legacy Memory |
| Assinatura | ECDSA secp256k1 |
| Modelo UTXO | Sim (como Bitcoin) |

---

## Como minerar

### Requisitos
- Ubuntu 20.04+ ou qualquer Linux
- Python 3.10+
- Hardware físico (VMs são bloqueadas)
- RAM: DDR2, DDR3, DDR4 ou DDR5

### Instalação

```bash
git clone https://github.com/proof-of-legacy/Proof-of-Legacy-Memory.git
cd Proof-of-Legacy-Memory
pip install -r requirements.txt --break-system-packages
python3 polm_wallet.py create
```

### Iniciar mineração

```bash
# DDR2 (2.5x)
python3 polm_node.py --ram-type DDR2

# DDR3 (1.8x)
python3 polm_node.py --ram-type DDR3

# DDR4 (1.0x)
python3 polm_node.py --ram-type DDR4
```

### Consultar saldo

```bash
python3 polm_wallet.py balance
```

### Enviar PoLM

```bash
python3 polm_wallet.py send --to <endereço> --amount 10 --fee 0.001
```

---

## Explorer

```bash
python3 polm_explorer.py
```

Acesse: http://localhost:5000

---

## Fundador

**Aluisio Fernandes "Aluminium"**  
Criador e fundador da rede PoLM.

O bloco genesis da blockchain PoLM contém a mensagem:  
*"PoLM 2025 — Aluisio Fernandes 'Aluminium' — Hardware antigo nao morre, ele minera. DDR2 tem valor. Cada ciclo de RAM e prova de vida."*

Esta mensagem é **imutável** e estará na blockchain para sempre.

---

## Roadmap

- [x] Blockchain funcional com Proof of Legacy Memory
- [x] Rede P2P com múltiplos nós
- [x] Transferências ECDSA
- [x] Explorer web
- [x] Anti-VM e fingerprint de hardware
- [x] Licença proprietária
- [ ] Registro de ativos na blockchain
- [ ] Interface web de registro
- [ ] API para integração governamental
- [ ] Listagem em exchanges
- [ ] Aplicativo móvel

---

## ⚠️ Aviso Legal

Este repositório é público para fins de **transparência e auditoria**.  
O código-fonte **NÃO é open source**.  
Qualquer uso além da mineração pessoal requer autorização do fundador.

*© 2025 Aluisio Fernandes "Aluminium". Todos os direitos reservados.*
