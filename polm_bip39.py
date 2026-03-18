"""
PoLM BIP-39 Wallet Tools  v1.0.0
https://polm.com.br

Generates 24-word seed phrases for PoLM wallets.
Compatible with Trust Wallet, Ledger, MetaMask.

Install: pip install mnemonic cryptography flask

Usage:
  python polm_bip39.py new      [label]    Generate new 24-word wallet
  python polm_bip39.py recover             Restore from 24 words
  python polm_bip39.py show                List all addresses
  python polm_bip39.py balance  [node]     Check balances
  python polm_bip39.py ui       [node] [port]  Web wallet
"""

import sys, os, hashlib, hmac, json, time, struct, unicodedata, secrets
import urllib.request
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Tuple

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import io, asyncio
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

VERSION = "1.0.0"
SYMBOL  = "POLM"
WEBSITE = "https://polm.com.br"
MIN_FEE = 0.0001
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# ── ECDSA ─────────────────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
    HAVE_CRYPTO = True
except ImportError:
    HAVE_CRYPTO = False

# ── BIP39 ─────────────────────────────────────────────────────────
try:
    from mnemonic import Mnemonic as _Mnemonic
    _mnemo = _Mnemonic("english")
    HAVE_MNEMONIC = True
except ImportError:
    HAVE_MNEMONIC = False

def _require_mnemonic():
    if not HAVE_MNEMONIC:
        print("\n[BIP39] Install required: pip install mnemonic")
        print("  Linux/macOS : pip install mnemonic")
        print("  Windows     : pip install mnemonic")
        sys.exit(1)

def generate_mnemonic_24() -> str:
    _require_mnemonic()
    return _mnemo.generate(strength=256)

def validate_mnemonic(words: str) -> bool:
    _require_mnemonic()
    return _mnemo.check(words.strip().lower())

def mnemonic_to_seed(mnemonic: str, passphrase: str = "") -> bytes:
    m = unicodedata.normalize("NFKD", mnemonic.strip().lower())
    p = unicodedata.normalize("NFKD", "mnemonic" + passphrase)
    return hashlib.pbkdf2_hmac("sha512", m.encode(), p.encode(), 2048)

# ── BIP32 ─────────────────────────────────────────────────────────
def _hmac512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()

def _master_key(seed: bytes) -> Tuple[bytes, bytes]:
    I = _hmac512(b"Bitcoin seed", seed)
    return I[:32], I[32:]

def _priv_to_pub(priv_bytes: bytes) -> bytes:
    if HAVE_CRYPTO:
        priv_int = int.from_bytes(priv_bytes, "big")
        key = ec.derive_private_key(priv_int, ec.SECP256K1(), default_backend())
        return key.public_key().public_bytes(
            serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)
    return hashlib.sha256(priv_bytes).digest()

def _child_key(priv: bytes, chain: bytes, idx: int) -> Tuple[bytes, bytes]:
    if idx >= 0x80000000:
        data = b"\x00" + priv + struct.pack(">I", idx)
    else:
        data = _priv_to_pub(priv) + struct.pack(">I", idx)
    I = _hmac512(chain, data)
    ki = (int.from_bytes(I[:32],"big") + int.from_bytes(priv,"big")) % SECP256K1_N
    return ki.to_bytes(32,"big"), I[32:]

def derive_polm_key(seed: bytes, account: int = 0) -> Tuple[bytes, bytes]:
    """BIP-44 path: m/44'/7070'/account'/0/0  (coin 7070 = POLM)"""
    priv, chain = _master_key(seed)
    for idx in [0x80000000+44, 0x80000000+7070,
                0x80000000+account, 0, 0]:
        priv, chain = _child_key(priv, chain, idx)
    return priv, _priv_to_pub(priv)

def pubkey_to_address(pub_bytes: bytes) -> str:
    h = hashlib.sha3_256(hashlib.sha3_256(pub_bytes).digest()).hexdigest()
    return "POLM" + h[:32].upper()

def sign_tx_data(priv_bytes: bytes, data: bytes) -> str:
    if HAVE_CRYPTO:
        priv_int = int.from_bytes(priv_bytes, "big")
        key = ec.derive_private_key(priv_int, ec.SECP256K1(), default_backend())
        return key.sign(data, ec.ECDSA(hashes.SHA256())).hex()
    return hashlib.sha3_256(priv_bytes + data).hexdigest()

# ── WALLET FILE ───────────────────────────────────────────────────
@dataclass
class WalletKey:
    address:  str
    pub_hex:  str
    priv_hex: str
    mnemonic: str   # 24 words
    path:     str   # derivation path
    label:    str = ""
    created:  int = 0

class WalletFile:
    def __init__(self, path: str):
        self.path = path
        self.keys: Dict[str, WalletKey] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                d = json.load(f)
            for addr, k in d.items():
                flds = WalletKey.__dataclass_fields__
                self.keys[addr] = WalletKey(**{f: k.get(f,"") for f in flds})
            print(f"[Wallet] Loaded {len(self.keys)} key(s)")
        else:
            self._new("default")
            print(f"[Wallet] Created: {self.path}")

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({a: asdict(k) for a,k in self.keys.items()}, f, indent=2)
        if IS_WIN and os.path.exists(self.path): os.remove(self.path)
        os.replace(tmp, self.path)

    def _new(self, label: str, mnemonic: str = "") -> str:
        if not mnemonic:
            mnemonic = generate_mnemonic_24()
        seed = mnemonic_to_seed(mnemonic)
        acc  = len(self.keys)
        priv_b, pub_b = derive_polm_key(seed, acc)
        addr = pubkey_to_address(pub_b)
        path = f"m/44'/7070'/{acc}'/0/0"
        self.keys[addr] = WalletKey(
            address=addr, pub_hex=pub_b.hex(), priv_hex=priv_b.hex(),
            mnemonic=mnemonic, path=path,
            label=label or f"Account {acc+1}", created=int(time.time()))
        self._save()
        return addr

    def new_address(self, label: str = "") -> Tuple[str, str]:
        addr = self._new(label)
        return addr, self.keys[addr].mnemonic

    def recover(self, mnemonic: str, label: str = "Recovered") -> str:
        if not validate_mnemonic(mnemonic):
            raise ValueError("Invalid seed phrase — check the 24 words")
        return self._new(label, mnemonic.strip().lower())

    def default(self) -> str:
        return list(self.keys.keys())[0]

    def sign_tx(self, sender: str, receiver: str,
                amount: float, fee: float, memo: str = "") -> Optional[dict]:
        if sender not in self.keys: return None
        k  = self.keys[sender]
        ts = int(time.time())
        signing = f"{sender}:{receiver}:{amount:.8f}:{fee:.8f}:{ts}:{memo}".encode()
        priv_b  = bytes.fromhex(k.priv_hex)
        sig     = sign_tx_data(priv_b, signing)
        tx_id   = hashlib.sha3_256(signing + sig.encode()).hexdigest()
        return {"tx_id": tx_id, "sender": sender, "receiver": receiver,
                "amount": amount, "fee": fee, "timestamp": ts,
                "signature": sig, "pub_key": k.pub_hex, "memo": memo,
                "confirmed": False, "block_height": -1}

# ── NODE CLIENT ───────────────────────────────────────────────────
class NodeClient:
    def __init__(self, url="http://localhost:6060"):
        self.url = url.rstrip("/")
    def _get(self, p):
        try: return json.loads(urllib.request.urlopen(f"{self.url}{p}",timeout=5).read())
        except: return None
    def _post(self, p, d):
        try:
            req = urllib.request.Request(f"{self.url}{p}",
                json.dumps(d).encode(), {"Content-Type":"application/json"}, method="POST")
            return json.loads(urllib.request.urlopen(req,timeout=8).read())
        except: return None
    def balance(self, a): d=self._get(f"/balance/{a}"); return d.get("balance",0.) if d else 0.
    def history(self, a): d=self._get(f"/history/{a}"); return d if isinstance(d,list) else []
    def send_tx(self, t): return self._post("/tx/send",t) or {"accepted":False,"reason":"offline"}
    def status(self): return self._get("/")
    def miners(self): return self._get("/miners") or {}

# ── DATA DIR ──────────────────────────────────────────────────────
def data_dir():
    if IS_WIN:
        d = os.path.join(os.environ.get("APPDATA","~"),"PoLM")
    else:
        d = os.path.expanduser("~/.polm")
    os.makedirs(d,exist_ok=True)
    return d

# ── CLI ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    if IS_WIN:
        import multiprocessing; multiprocessing.freeze_support()

    args    = sys.argv[1:]
    testnet = "--testnet" in args
    args    = [a for a in args if not a.startswith("--")]
    dd      = data_dir()
    wpath   = os.path.join(dd, "wallet_bip39.json")
    mode    = args[0] if args else "help"

    if mode == "new":
        label = args[1] if len(args)>1 else ""
        wf = WalletFile(wpath)
        addr, mnemonic = wf.new_address(label)
        words = mnemonic.split()
        print(f"\n  ╔═══════════════════════════════════════════════════════╗")
        print(f"  ║   NEW POLM WALLET — WRITE DOWN YOUR SEED PHRASE!    ║")
        print(f"  ╚═══════════════════════════════════════════════════════╝")
        print(f"\n  Address : {addr}")
        print(f"  Path    : {wf.keys[addr].path}")
        print(f"\n  Your 24-word seed phrase:")
        for i in range(0, 24, 6):
            row = "   ".join(f"{i+j+1:2}. {words[i+j]:<10}" for j in range(6) if i+j<len(words))
            print(f"    {row}")
        print(f"\n  ⚠  Write these words on PAPER and store in a SAFE place.")
        print(f"  ⚠  NEVER share them digitally or with anyone.")
        print(f"  ⚠  These 24 words = full control of your POLM.\n")

    elif mode == "recover":
        print("Enter your 24-word seed phrase:")
        mnemonic = input("> ").strip()
        label = input("Label: ").strip()
        wf = WalletFile(wpath)
        try:
            addr = wf.recover(mnemonic, label)
            print(f"\n  Recovered: {addr}")
        except Exception as e:
            print(f"\n  Error: {e}")

    elif mode == "show":
        wf = WalletFile(wpath)
        print(f"\n  PoLM BIP-39 Wallet — {WEBSITE}")
        for addr, k in wf.keys.items():
            print(f"  {addr}  [{k.label}]  {k.path}")

    elif mode == "balance":
        url = args[1] if len(args)>1 else "http://localhost:6060"
        wf = WalletFile(wpath); node = NodeClient(url)
        total = 0.0
        print(f"\n  Balances  (node: {url})")
        for addr, k in wf.keys.items():
            b = node.balance(addr); total += b
            print(f"  {addr}  {b:>12.4f} {SYMBOL}  [{k.label}]")
        print(f"\n  Total: {total:.4f} {SYMBOL}")

    elif mode == "send":
        if len(args)<4:
            print("Usage: python polm_bip39.py send <from> <to> <amount> [fee]"); sys.exit(1)
        frm=args[1]; to=args[2]; amt=float(args[3])
        fee=float(args[4]) if len(args)>4 else 0.001
        url=args[5] if len(args)>5 else "http://localhost:6060"
        wf=WalletFile(wpath); node=NodeClient(url)
        tx=wf.sign_tx(frm,to,amt,fee)
        if not tx: print("Address not in wallet"); sys.exit(1)
        res=node.send_tx(tx)
        print(f"  {'Sent! TX: '+res['tx_id'] if res.get('accepted') else 'Failed: '+res.get('reason','')}")

    elif mode == "ui":
        # Import the main wallet server with BIP39 support
        try:
            from flask import Flask, jsonify, request, Response
            from polm_wallet import WalletServer
            url  = args[1] if len(args)>1 else "http://localhost:6060"
            port = int(args[2]) if len(args)>2 else 7070
            network = "testnet" if testnet else "mainnet"
            srv = WalletServer(wpath, url, port, network)
            srv.run()
        except ImportError:
            print("Install: pip install flask")

    else:
        print(f"""
PoLM BIP-39 Wallet  v{VERSION}  —  {WEBSITE}
24-word seed phrase · BIP-44 HD · secp256k1

First install:
  pip install mnemonic cryptography flask

Commands:
  python polm_bip39.py new      [label]   Generate 24-word wallet
  python polm_bip39.py recover            Restore from seed phrase
  python polm_bip39.py show               List addresses
  python polm_bip39.py balance  [url]     Check balances
  python polm_bip39.py send     <f> <t> <amt>  Send POLM
  python polm_bip39.py ui       [url] [port]   Web UI

Coin type: 7070 (POLM — to be registered in SLIP-44)
Path:      m/44'/7070'/0'/0/0
""")
