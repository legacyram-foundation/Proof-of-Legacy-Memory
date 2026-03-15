"""
polm_registry.py — Registros de Propriedade PoLM
==================================================
Infraestrutura global de registro imutável e verificável.

Tipos de registro:
  • Imóveis     — casas, terrenos, apartamentos
  • Veículos    — carros, motos, caminhões
  • Contratos   — societários, prestação, acordos
  • Autorais    — música, arte, código, patentes
  • Identidade  — certificados, diplomas, documentos

Como funciona:
  1. Dono cria TX com OP_REGISTER + hash do documento + metadados
  2. TX é assinada com ECDSA (chave privada do dono)
  3. TX incluída em bloco minerado → registro imutável
  4. Transferência = nova TX OP_TRANSFER_OWNERSHIP apontando para txid anterior
  5. Qualquer pessoa pode verificar a cadeia de propriedade

Segurança:
  • Hash do documento = SHA256(conteúdo original) → prova de existência
  • ECDSA obrigatório → só o dono pode transferir
  • Imutável após confirmação → sem cartório, sem fronteiras
"""

import hashlib
import json
import time
from typing import Optional

from polm_core import (
    COIN, CHAIN_ID, REGISTER_CATEGORIES,
    REGISTER_FEE_SATS, OP_REGISTER, OP_TRANSFER_OWNERSHIP,
    hash_transaction,
)

# ═══════════════════════════════════════════════════════════
# CRIAÇÃO DE REGISTROS
# ═══════════════════════════════════════════════════════════

def create_register_tx(
    category:      str,
    document_hash: str,
    title:         str,
    owner_address: str,
    fee_utxo_txid: str,
    fee_utxo_vout: int,
    metadata:      Optional[dict] = None,
    prev_registration: Optional[str] = None,
) -> dict:
    """
    Cria uma transação de registro de propriedade.

    Args:
        category:      Categoria (imovel, veiculo, contrato, autoral, identidade)
        document_hash: SHA256 do documento original (hex)
        title:         Descrição curta do registro
        owner_address: Endereço PoLM do proprietário
        fee_utxo_txid: TXID do UTXO usado para pagar a taxa
        fee_utxo_vout: Vout do UTXO
        metadata:      Informações adicionais (opcional)
        prev_registration: TXID do registro anterior (para histórico)

    Returns:
        TX não assinada — use wallet.sign() para assinar
    """
    if category not in REGISTER_CATEGORIES:
        raise ValueError(f"Categoria inválida: {category}. Use: {list(REGISTER_CATEGORIES)}")

    if len(document_hash) != 64:
        raise ValueError("document_hash deve ser SHA256 hex (64 chars)")

    registration_data = {
        "op":          OP_REGISTER,
        "category":    category,
        "doc_hash":    document_hash,
        "title":       title[:200],   # máx 200 chars
        "owner":       owner_address,
        "chain_id":    CHAIN_ID,
        "timestamp":   int(time.time()),
        "metadata":    metadata or {},
        "prev_reg":    prev_registration,
    }

    tx = {
        "version":  1,
        "type":     "REGISTER",
        "inputs":   [{"txid": fee_utxo_txid, "vout": fee_utxo_vout}],
        "outputs":  [
            {
                "address": owner_address,
                "value":   0,              # registro não transfere valor
                "data":    registration_data,
            }
        ],
        "locktime": 0,
        "chain_id": CHAIN_ID,
    }

    tx["txid"] = hash_transaction(tx)
    return tx


def create_transfer_ownership_tx(
    prev_reg_txid:  str,
    new_owner:      str,
    current_owner:  str,
    fee_utxo_txid:  str,
    fee_utxo_vout:  int,
    note:           str = "",
) -> dict:
    """
    Cria uma transação de transferência de propriedade.

    A cadeia de transferências forma um histórico imutável de donos:
    Registro → Transferência1 → Transferência2 → ...

    Args:
        prev_reg_txid: TXID do registro ou última transferência
        new_owner:     Endereço do novo dono
        current_owner: Endereço do dono atual (quem assina)
        fee_utxo_txid: UTXO para pagar taxa
        fee_utxo_vout: Vout do UTXO
        note:          Observação opcional (ex: "Venda por R$ 500.000")
    """
    transfer_data = {
        "op":          OP_TRANSFER_OWNERSHIP,
        "prev_reg":    prev_reg_txid,
        "new_owner":   new_owner,
        "prev_owner":  current_owner,
        "chain_id":    CHAIN_ID,
        "timestamp":   int(time.time()),
        "note":        note[:500],
    }

    tx = {
        "version":  1,
        "type":     "TRANSFER_OWNERSHIP",
        "inputs":   [{"txid": fee_utxo_txid, "vout": fee_utxo_vout}],
        "outputs":  [
            {
                "address": new_owner,
                "value":   0,
                "data":    transfer_data,
            }
        ],
        "locktime": 0,
        "chain_id": CHAIN_ID,
    }

    tx["txid"] = hash_transaction(tx)
    return tx


def hash_document(file_path: str) -> str:
    """
    Calcula SHA256 de um arquivo para uso como document_hash.
    O hash é a prova criptográfica de que o documento existia no momento do registro.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_document_bytes(data: bytes) -> str:
    """Calcula SHA256 de bytes brutos."""
    return hashlib.sha256(data).hexdigest()


# ═══════════════════════════════════════════════════════════
# VERIFICAÇÃO DE REGISTROS
# ═══════════════════════════════════════════════════════════

def verify_registration(tx: dict) -> tuple[bool, str]:
    """
    Verifica se uma TX de registro é válida.
    Retorna (válido, motivo).
    """
    if tx.get("type") != "REGISTER":
        return False, "não é TX de registro"

    outputs = tx.get("outputs", [])
    if not outputs:
        return False, "sem outputs"

    data = outputs[0].get("data", {})
    if data.get("op") != OP_REGISTER:
        return False, "op inválido"

    required = {"category", "doc_hash", "title", "owner", "chain_id"}
    missing  = required - data.keys()
    if missing:
        return False, f"campos faltando: {missing}"

    if data["category"] not in REGISTER_CATEGORIES:
        return False, f"categoria inválida: {data['category']}"

    if len(data["doc_hash"]) != 64:
        return False, "doc_hash inválido"

    if data["chain_id"] != CHAIN_ID:
        return False, "chain_id errado (replay attack?)"

    return True, "ok"


def get_registration_chain(txid: str, blockchain) -> list[dict]:
    """
    Reconstrói a cadeia completa de propriedade de um registro.
    Retorna lista de TXs ordenada do mais antigo ao mais recente.

    Exemplo de saída:
    [
        {"type": "REGISTER",           "owner": "addr1", "timestamp": ...},
        {"type": "TRANSFER_OWNERSHIP", "owner": "addr2", "timestamp": ...},
        {"type": "TRANSFER_OWNERSHIP", "owner": "addr3", "timestamp": ...},
    ]
    """
    chain = []
    current_txid = txid

    for _ in range(1000):   # máx 1000 transferências
        tx = _find_tx(current_txid, blockchain)
        if not tx:
            break

        entry = {
            "txid":      current_txid,
            "type":      tx.get("type"),
            "timestamp": tx.get("outputs", [{}])[0].get("data", {}).get("timestamp"),
        }

        data = tx.get("outputs", [{}])[0].get("data", {})

        if tx.get("type") == "REGISTER":
            entry["owner"]    = data.get("owner")
            entry["category"] = data.get("category")
            entry["title"]    = data.get("title")
            entry["doc_hash"] = data.get("doc_hash")
            chain.insert(0, entry)
            break   # chegou na origem

        elif tx.get("type") == "TRANSFER_OWNERSHIP":
            entry["owner"]      = data.get("new_owner")
            entry["prev_owner"] = data.get("prev_owner")
            entry["note"]       = data.get("note", "")
            chain.insert(0, entry)
            current_txid = data.get("prev_reg")
            if not current_txid:
                break
        else:
            break

    return chain


def get_current_owner(txid: str, blockchain) -> Optional[str]:
    """Retorna o dono atual de um registro."""
    chain = get_registration_chain(txid, blockchain)
    if not chain:
        return None
    return chain[-1].get("owner")


def _find_tx(txid: str, blockchain) -> Optional[dict]:
    """Busca uma TX na blockchain pelo TXID."""
    try:
        block_height = blockchain.db.get_tx_block(txid)
        if block_height is None:
            return None
        block = blockchain.get_block(block_height)
        if not block:
            return None
        for tx in block["transactions"]:
            if tx.get("txid") == txid or hash_transaction(tx) == txid:
                return tx
    except Exception:
        pass
    return None


# ═══════════════════════════════════════════════════════════
# CLI — INTERFACE DE LINHA DE COMANDO
# ═══════════════════════════════════════════════════════════

def cmd_register(args):
    """Registra um documento na blockchain PoLM."""
    import sys

    if not args.file and not args.hash:
        print("Use --file <caminho> ou --hash <sha256hex>")
        sys.exit(1)

    doc_hash = args.hash if args.hash else hash_document(args.file)
    print(f"Hash do documento: {doc_hash}")

    # Carrega wallet
    try:
        from polm_wallet import PoLMWallet
        wallet = PoLMWallet.load()
        address = wallet.primary_address
    except Exception as e:
        print(f"Erro ao carregar wallet: {e}")
        sys.exit(1)

    # Busca UTXO para pagar taxa
    import requests
    try:
        r = requests.get(f"http://127.0.0.1:5556/utxos/{address}", timeout=5)
        utxos = r.json().get("utxos", [])
        if not utxos:
            print("Sem UTXOs disponíveis. Mine alguns blocos primeiro.")
            sys.exit(1)
        utxo = utxos[0]
    except Exception as e:
        print(f"Erro ao buscar UTXOs: {e}")
        sys.exit(1)

    # Cria e assina TX de registro
    tx = create_register_tx(
        category      = args.category,
        document_hash = doc_hash,
        title         = args.title,
        owner_address = address,
        fee_utxo_txid = utxo["txid"],
        fee_utxo_vout = utxo["vout"],
        metadata      = {"note": args.note} if args.note else {},
    )

    tx_signed = wallet.sign(tx)
    txid = tx_signed["txid"]

    # Envia para o nó local
    try:
        r = requests.post(
            "http://127.0.0.1:5556/tx",
            json=tx_signed,
            timeout=10,
        )
        result = r.json()
        if result.get("accepted"):
            print(f"\n✅ Registro criado!")
            print(f"   TXID:     {txid}")
            print(f"   Categoria: {args.category}")
            print(f"   Título:   {args.title}")
            print(f"   Doc hash: {doc_hash}")
            print(f"   Dono:     {address}")
            print(f"\n   Aguarde confirmação (~2.5 min)")
        else:
            print(f"❌ Erro: {result.get('reason')}")
    except Exception as e:
        print(f"Erro ao enviar TX: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="PoLM — Registro de Propriedade")
    sub = parser.add_subparsers(dest="cmd")

    p_reg = sub.add_parser("register", help="Registra um documento")
    p_reg.add_argument("--category", required=True,
                       choices=list(REGISTER_CATEGORIES),
                       help="Categoria do registro")
    p_reg.add_argument("--title", required=True, help="Título/descrição")
    p_reg.add_argument("--file", help="Arquivo para registrar (calcula hash)")
    p_reg.add_argument("--hash", help="SHA256 do documento (alternativa a --file)")
    p_reg.add_argument("--note", help="Observação opcional")

    p_transfer = sub.add_parser("transfer", help="Transfere propriedade")
    p_transfer.add_argument("--txid", required=True, help="TXID do registro")
    p_transfer.add_argument("--to",   required=True, help="Endereço do novo dono")

    p_verify = sub.add_parser("verify", help="Verifica histórico de propriedade")
    p_verify.add_argument("--txid", required=True, help="TXID do registro")

    args = parser.parse_args()

    if args.cmd == "register":
        cmd_register(args)
    elif args.cmd == "transfer":
        print(f"Transferindo {args.txid} para {args.to}...")
    elif args.cmd == "verify":
        print(f"Verificando histórico de {args.txid}...")
    else:
        parser.print_help()
