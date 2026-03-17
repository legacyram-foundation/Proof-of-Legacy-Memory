#!/bin/bash
# PoLM v1.2.0 — Linux / macOS Installer
# https://polm.com.br
set -e

G='\033[0;32m'; C='\033[0;36m'; Y='\033[1;33m'; B='\033[1m'; NC='\033[0m'
log() { echo -e "${C}[polm]${NC} $1"; }
ok()  { echo -e "${G}[ok]${NC}   $1"; }
warn(){ echo -e "${Y}[warn]${NC} $1"; }

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BASE"
OS=$(uname -s)

echo ""
echo "  ██████████████████████████████████████████████████"
echo "  ██  PoLM — Proof of Legacy Memory   v1.2.0     ██"
echo "  ██  polm.com.br                                ██"
echo "  ████████████████████████████████████████████████"
echo ""

# ── system deps ────────────────────────────────────────────────
if [ "$OS" = "Linux" ]; then
    if command -v apt &>/dev/null; then
        log "Installing system dependencies..."
        sudo apt update -q 2>/dev/null || true
        sudo apt install -y python3 python3-venv python3-pip git curl dmidecode -q 2>/dev/null || true
        ok "System packages ready"
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3 python3-pip git curl dmidecode -q 2>/dev/null || true
    fi
fi

python3 --version &>/dev/null || { echo "Python 3 required — https://python.org"; exit 1; }

# ── venv ───────────────────────────────────────────────────────
log "Setting up Python environment..."
python3 -m venv venv
venv/bin/pip install --upgrade pip -q
venv/bin/pip install flask cryptography requests -q
ok "Dependencies ready"

# ── detect RAM ────────────────────────────────────────────────
detect_ram(){
    local R=""
    if [ "$OS" = "Linux" ]; then
        R=$(sudo dmidecode -t memory 2>/dev/null | grep -i "^\s*Type:" | \
            grep -v "Unknown\|Error\|Flash" | head -1 | awk '{print $2}' | \
            tr '[:lower:]' '[:upper:]')
    elif [ "$OS" = "Darwin" ]; then
        R=$(system_profiler SPMemoryDataType 2>/dev/null | grep -i "type:" | \
            grep -v "ECC" | head -1 | awk '{print $2}' | tr '[:lower:]' '[:upper:]')
    fi
    case "$R" in DDR2|DDR3|DDR4|DDR5) echo "$R";; *) echo "DDR4";; esac
}
RAM=$(detect_ram)
THREADS=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2)
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || ipconfig getifaddr en0 2>/dev/null || echo "127.0.0.1")
ok "RAM=$RAM  Threads=$THREADS  IP=$MY_IP"

# ── wallet ────────────────────────────────────────────────────
DATA="$HOME/.polm"
mkdir -p "$DATA"
WPATH="$DATA/wallet.json"

log "Setting up wallet..."
ADDR=$(venv/bin/python3 -c "
import sys; sys.path.insert(0,'.')
from polm_wallet import WalletFile
w = WalletFile('$WPATH')
print(w.default())
" 2>/dev/null || echo "POLM_ADDRESS")
ok "Address: $ADDR"

# ── start scripts ─────────────────────────────────────────────
log "Creating launch scripts..."

cat > start_node.sh << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")"
echo "  PoLM Node v1.2.0  —  polm.com.br"
venv/bin/python3 polm.py node 6060
SCRIPT

cat > start_miner.sh << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")"
echo "  Mining as: $ADDR  ($RAM)"
venv/bin/python3 polm.py miner http://localhost:6060 $ADDR $RAM
SCRIPT

cat > start_wallet.sh << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")"
echo "  Wallet UI: http://localhost:7070"
which xdg-open &>/dev/null && xdg-open http://localhost:7070 &
which open      &>/dev/null && open      http://localhost:7070 &
venv/bin/python3 polm_wallet.py ui http://localhost:6060 7070
SCRIPT

cat > start_explorer.sh << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")"
echo "  Explorer: http://localhost:5050"
venv/bin/python3 polm_explorer.py http://localhost:6060 5050
SCRIPT

cat > start_all.sh << SCRIPT
#!/bin/bash
cd "\$(dirname "\$0")"
pkill -f "polm.py\|polm_wallet.py\|polm_explorer.py" 2>/dev/null; sleep 1
echo "  PoLM v1.2.0  —  polm.com.br"
echo "  Starting all services..."
nohup venv/bin/python3 polm.py node 6060 > /tmp/polm_node.log 2>&1 &
sleep 4
echo "  Node started (h=\$(curl -s http://localhost:6060/ | python3 -c 'import sys,json; print(json.load(sys.stdin)["height"])' 2>/dev/null || echo '?'))"
nohup venv/bin/python3 polm.py miner http://localhost:6060 $ADDR $RAM > /tmp/polm_miner.log 2>&1 &
nohup venv/bin/python3 polm_wallet.py ui http://localhost:6060 7070 > /tmp/polm_wallet.log 2>&1 &
nohup venv/bin/python3 polm_explorer.py http://localhost:6060 5050 > /tmp/polm_explorer.log 2>&1 &
sleep 3
which xdg-open &>/dev/null && xdg-open http://localhost:7070 2>/dev/null &
which open      &>/dev/null && open      http://localhost:7070 2>/dev/null &
echo ""
echo "  All started!"
echo "    Wallet   : http://localhost:7070"
echo "    Explorer : http://localhost:5050"
echo "    Node API : http://localhost:6060"
echo "    Website  : https://polm.com.br"
SCRIPT

chmod +x start_node.sh start_miner.sh start_wallet.sh start_explorer.sh start_all.sh

ok "Launch scripts created"

echo ""
echo "  ██████████████████████████████████████████████████"
echo "  ██  Installation complete!                      ██"
echo "  ████████████████████████████████████████████████"
echo ""
echo "  Address  :  $ADDR"
echo "  RAM      :  $RAM"
echo "  Threads  :  $THREADS"
echo ""
echo "  ─────────────────────────────────────────────────"
echo "  ./start_all.sh       start everything"
echo "  ./start_wallet.sh    wallet UI"
echo "  ./start_miner.sh     mine solo"
echo "  ./start_node.sh      run full node"
echo "  ─────────────────────────────────────────────────"
echo "  Wallet   : http://localhost:7070"
echo "  Explorer : http://localhost:5050"
echo "  Website  : https://polm.com.br"
echo "  ─────────────────────────────────────────────────"
echo ""
