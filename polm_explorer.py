"""
polm_explorer.py — PoLM Block Explorer v2.0
=============================================
Explorer profissional estilo BSCScan/Etherscan.

Rotas:
  GET /                     — dashboard principal
  GET /blocks               — lista de blocos paginada
  GET /block/<height>       — detalhes de um bloco
  GET /tx/<txid>            — detalhes de uma transação
  GET /address/<addr>       — saldo e histórico
  GET /miners               — ranking de mineradores
  GET /epochs               — informações de épocas
  GET /api/stats            — estatísticas JSON
  GET /api/blocks           — blocos JSON paginados
  GET /api/block/<height>   — bloco JSON
  GET /api/address/<addr>   — endereço JSON
  GET /api/epoch            — época atual JSON
"""

import gzip
import json
import os
import sys
import time
from typing import Optional

try:
    from flask import Flask, jsonify, render_template_string, abort, request, redirect
except ImportError:
    print("Flask não instalado. Execute: pip install flask")
    sys.exit(1)

from polm_core import (
    COIN, MAX_SUPPLY_COINS, CHAIN_FILE, UTXO_FILE,
    get_epoch_info, get_epoch_config, get_ram_multiplier,
    get_cpu_multiplier, EPOCH_INTERVAL, TARGET_BLOCK_TIME,
)
from polm_chain import Blockchain

app   = Flask(__name__)
_chain: Optional[Blockchain] = None

def get_chain() -> Blockchain:
    global _chain
    if _chain is None:
        _chain = Blockchain()
        _chain.initialize()
    return _chain

# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _ts_ago(ts):
    delta = int(time.time() - ts)
    if delta < 60:    return f"{delta}s atrás"
    if delta < 3600:  return f"{delta//60}m atrás"
    if delta < 86400: return f"{delta//3600}h atrás"
    return f"{delta//86400}d atrás"

def _ts_fmt(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts))

def _fmt_polm(sats):
    return f"{sats / COIN:,.8f}"

def _short(s, n=16):
    return s[:n] + "…" if len(s) > n else s

def _ram_badge(ram):
    colors = {
        "DDR1":   ("#7c3aed","#a78bfa"),
        "DDR2":   ("#065f46","#6ee7b7"),
        "DDR3":   ("#1e3a5f","#60a5fa"),
        "DDR4":   ("#713f12","#fbbf24"),
        "DDR5":   ("#7c1d13","#fca5a5"),
        "LPDDR3": ("#134e4a","#5eead4"),
        "LPDDR4": ("#1c1917","#a8a29e"),
        "LPDDR5": ("#4c1d95","#c4b5fd"),
        "AUTO":   ("#1f2937","#9ca3af"),
    }
    bg, fg = colors.get(ram, colors["AUTO"])
    return f'<span style="background:{bg}22;color:{fg};border:1px solid {bg}88;padding:2px 8px;border-radius:4px;font-size:10px;letter-spacing:1px">{ram}</span>'

def _get_miner_stats(chain, n=500):
    """Retorna estatísticas dos mineradores."""
    blocks  = chain.get_recent_blocks(n)
    miners  = {}
    for b in blocks:
        m   = b.get("miner", "")
        ram = b.get("ram_type", "AUTO")
        s   = b.get("ram_score", 0)
        conf = b.get("ram_confidence", 1.0)
        if isinstance(b.get("ram_proof"), dict):
            ram  = b["ram_proof"].get("ram_type", ram)
            s    = b["ram_proof"].get("score", s)
            conf = b["ram_proof"].get("confidence", conf)
        if m not in miners:
            miners[m] = {"blocks":0,"ram":ram,"score":0,"confidence":0,"reward":0}
        miners[m]["blocks"]     += 1
        miners[m]["score"]      += s
        miners[m]["confidence"] += conf
        if b.get("transactions"):
            cb = b["transactions"][0]
            miners[m]["reward"] += sum(o["value"] for o in cb.get("outputs",[]))
    result = []
    for addr, v in miners.items():
        n_b = v["blocks"]
        result.append({
            "address":    addr,
            "blocks":     n_b,
            "ram":        v["ram"],
            "avg_score":  round(v["score"] / max(n_b,1), 2),
            "avg_conf":   round(v["confidence"] / max(n_b,1), 3),
            "reward_polm": round(v["reward"] / COIN, 4),
            "pct":        round(n_b / n * 100, 1),
        })
    return sorted(result, key=lambda x: -x["blocks"])

# ═══════════════════════════════════════════════════════════
# HTML BASE
# ═══════════════════════════════════════════════════════════

CSS = """
<style>
:root{
  --bg:#0b0e14;--surface:#111827;--surface2:#1a2234;
  --border:#1f2d45;--border2:#2a3f5f;
  --accent:#00e5b0;--accent2:#ff6b35;--accent3:#6366f1;
  --text:#e2e8f0;--muted:#64748b;--muted2:#94a3b8;
  --green:#22c55e;--red:#ef4444;--yellow:#eab308;
  --font:'JetBrains Mono','Courier New',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:var(--font);font-size:13px;line-height:1.6;min-height:100vh}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline;color:#00ffcc}

/* HEADER */
header{
  background:var(--surface);border-bottom:1px solid var(--border);
  padding:0 32px;display:flex;align-items:center;gap:0;
  position:sticky;top:0;z-index:100;
}
.logo{
  font-size:22px;font-weight:900;letter-spacing:3px;
  color:var(--accent);padding:16px 32px 16px 0;
  border-right:1px solid var(--border);margin-right:32px;
}
.logo span{color:var(--accent2)}
nav{display:flex;gap:0}
nav a{
  color:var(--muted2);font-size:12px;text-transform:uppercase;
  letter-spacing:1.5px;padding:20px 16px;
  border-bottom:2px solid transparent;transition:all .2s;
}
nav a:hover,nav a.active{color:var(--accent);border-bottom-color:var(--accent);text-decoration:none}

/* HERO SEARCH */
.hero{
  background:linear-gradient(135deg,#0b0e14 0%,#0f1a2e 50%,#0b0e14 100%);
  border-bottom:1px solid var(--border);padding:32px;text-align:center;
}
.hero h1{font-size:14px;text-transform:uppercase;letter-spacing:3px;color:var(--muted2);margin-bottom:8px}
.hero-sub{font-size:11px;color:var(--muted);margin-bottom:24px}
.search-wrap{display:flex;max-width:700px;margin:0 auto;gap:0}
.search-input{
  flex:1;background:var(--surface2);border:1px solid var(--border2);
  border-right:none;border-radius:6px 0 0 6px;
  color:var(--text);padding:12px 16px;font-family:var(--font);font-size:12px;
  outline:none;
}
.search-input:focus{border-color:var(--accent)}
.search-btn{
  background:var(--accent);color:#000;font-weight:700;
  border:none;padding:12px 24px;border-radius:0 6px 6px 0;
  font-family:var(--font);font-size:12px;cursor:pointer;
  text-transform:uppercase;letter-spacing:1px;
}
.search-btn:hover{background:#00ffcc}

/* CONTAINER */
.container{max-width:1280px;margin:0 auto;padding:32px 24px}

/* STAT CARDS */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:32px}
.stat-card{
  background:var(--surface);border:1px solid var(--border);border-radius:8px;
  padding:20px;position:relative;overflow:hidden;
}
.stat-card::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2));
}
.stat-label{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px}
.stat-value{font-size:24px;font-weight:700;color:var(--accent);letter-spacing:-0.5px}
.stat-sub{color:var(--muted2);font-size:11px;margin-top:4px}
.stat-icon{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-size:28px;opacity:.15}

/* PROGRESS BAR */
.bar-wrap{background:var(--border);border-radius:2px;height:4px;margin-top:10px;overflow:hidden}
.bar{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px}

/* SECTION */
.section{background:var(--surface);border:1px solid var(--border);border-radius:8px;margin-bottom:24px;overflow:hidden}
.section-header{
  display:flex;align-items:center;justify-content:space-between;
  padding:16px 20px;border-bottom:1px solid var(--border);
}
.section-title{font-size:11px;text-transform:uppercase;letter-spacing:2px;color:var(--muted2);font-weight:700}
.section-link{font-size:11px;color:var(--accent)}

/* TABLE */
.tbl{width:100%;border-collapse:collapse}
.tbl th{
  text-align:left;font-size:10px;text-transform:uppercase;
  letter-spacing:1.5px;color:var(--muted);
  padding:12px 16px;border-bottom:1px solid var(--border);
  background:var(--surface2);font-weight:500;
}
.tbl td{padding:12px 16px;border-bottom:1px solid var(--border);font-size:12px;vertical-align:middle}
.tbl tr:last-child td{border-bottom:none}
.tbl tr:hover td{background:var(--surface2)}

/* EPOCH CARD */
.epoch-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.epoch-card{
  background:var(--surface2);border:1px solid var(--border);border-radius:8px;
  padding:20px;
}
.epoch-num{font-size:32px;font-weight:900;color:var(--accent3);opacity:.3;float:right;margin-top:-4px}
.epoch-status{display:inline-block;padding:2px 10px;border-radius:12px;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}
.status-active{background:#00e5b022;color:var(--accent);border:1px solid #00e5b044}
.status-future{background:#6366f122;color:#a5b4fc;border:1px solid #6366f144}
.status-past{background:#64748b22;color:var(--muted);border:1px solid #64748b44}

/* DETAIL */
.detail-card{background:var(--surface);border:1px solid var(--border);border-radius:8px;overflow:hidden}
.detail-row{display:flex;padding:12px 20px;border-bottom:1px solid var(--border);gap:16px;align-items:flex-start}
.detail-row:last-child{border-bottom:none}
.detail-key{width:180px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:1px;flex-shrink:0;padding-top:2px}
.detail-val{color:var(--text);word-break:break-all;flex:1}

/* BADGES */
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;text-transform:uppercase;letter-spacing:1px}
.badge-green{background:#22c55e22;color:var(--green);border:1px solid #22c55e44}
.badge-red{background:#ef444422;color:var(--red);border:1px solid #ef444444}
.badge-blue{background:#3b82f622;color:#93c5fd;border:1px solid #3b82f644}
.badge-purple{background:#7c3aed22;color:#c4b5fd;border:1px solid #7c3aed44}
.badge-yellow{background:#eab30822;color:var(--yellow);border:1px solid #eab30844}

/* AMOUNTS */
.polm{color:var(--green);font-weight:700}
.hash-text{color:var(--muted2);font-size:11px}
.addr{color:var(--accent);font-size:11px}

/* CONFIDENCE BAR */
.conf-bar{display:flex;align-items:center;gap:8px}
.conf-fill{height:6px;border-radius:3px;background:var(--accent);min-width:4px}
.conf-wrap{background:var(--border);border-radius:3px;height:6px;flex:1;overflow:hidden}

/* PAGINATION */
.pagination{display:flex;gap:8px;justify-content:center;margin-top:24px}
.page-btn{
  background:var(--surface);border:1px solid var(--border);
  color:var(--text);padding:6px 14px;border-radius:4px;font-family:var(--font);
  font-size:11px;cursor:pointer;text-decoration:none;
}
.page-btn:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
.page-btn.active{background:var(--accent);color:#000;border-color:var(--accent)}

/* TICKER */
.ticker{
  background:var(--surface2);border-bottom:1px solid var(--border);
  padding:8px 32px;font-size:11px;color:var(--muted2);
  display:flex;gap:32px;overflow:hidden;
}
.ticker span{white-space:nowrap}
.ticker b{color:var(--accent)}

/* FOOTER */
footer{
  border-top:1px solid var(--border);padding:24px 32px;
  color:var(--muted);font-size:11px;text-align:center;margin-top:48px;
  background:var(--surface);
}
footer a{color:var(--muted2)}

/* RESPONSIVE */
@media(max-width:768px){
  header{padding:0 16px}
  .container{padding:16px}
  .stats-grid{grid-template-columns:1fr 1fr}
  .detail-key{width:120px}
  nav a{padding:16px 8px;font-size:10px}
}
</style>
"""

def _base(title, body, active=""):
    chain = get_chain()
    tip   = chain.tip or {}
    h     = chain.height
    ei    = get_epoch_info(h)
    next_h = ei["next_epoch_block"]
    blocks_left = ei["blocks_until_next"]
    mins_left = blocks_left * TARGET_BLOCK_TIME // 60

    ticker = f"""
    <div class="ticker">
      <span>Altura: <b>{h:,}</b></span>
      <span>Época: <b>{ei['epoch']}</b></span>
      <span>RAM mín: <b>{ei['min_ram_mb']//1024}GB</b></span>
      <span>Próx. época: bloco <b>{next_h:,}</b> (~{mins_left//60}h)</span>
      <span>Dificuldade: <b>{tip.get('difficulty','—')} bits</b></span>
      <span>Permitido: <b>{', '.join(ei['allowed_ram'])}</b></span>
    </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>{title} — PoLM Explorer</title>
{CSS}
</head>
<body>
<header>
  <div class="logo">Po<span>LM</span></div>
  <nav>
    <a href="/" class="{'active' if active=='home' else ''}">Dashboard</a>
    <a href="/blocks" class="{'active' if active=='blocks' else ''}">Blocos</a>
    <a href="/miners" class="{'active' if active=='miners' else ''}">Mineradores</a>
    <a href="/epochs" class="{'active' if active=='epochs' else ''}">Épocas</a>
    <a href="/api/stats">API</a>
  </nav>
</header>
{ticker}
<div class="hero">
  <h1>Proof of Legacy Memory — Explorer</h1>
  <div class="hero-sub">Hardware antigo tem valor. Cada ciclo de RAM é prova de vida.</div>
  <form action="/search" method="get" style="display:flex;max-width:700px;margin:0 auto;gap:0">
    <input class="search-input" name="q" placeholder="Buscar por bloco, txid, endereço..." autocomplete="off">
    <button class="search-btn" type="submit">Buscar</button>
  </form>
</div>
{body}
<footer>
  PoLM — Proof of Legacy Memory &nbsp;|&nbsp;
  Supply máximo: 32.000.000 PoLM &nbsp;|&nbsp;
  Época {ei['epoch']} — RAM mín: {ei['min_ram_mb']//1024}GB &nbsp;|&nbsp;
  <a href="/api/stats">API</a> &nbsp;|&nbsp;
  <a href="https://github.com/proof-of-legacy/Proof-of-Legacy-Memory">GitHub</a>
</footer>
</body></html>"""

# ═══════════════════════════════════════════════════════════
# ROTAS
# ═══════════════════════════════════════════════════════════

@app.route("/")
def index():
    chain  = get_chain()
    tip    = chain.tip or {}
    supply = chain.total_supply() / COIN
    blocks = list(reversed(chain.get_recent_blocks(20)))
    miners = _get_miner_stats(chain, 500)[:5]
    ei     = get_epoch_info(chain.height)

    # Calcula tempo médio de bloco
    recent = chain.get_recent_blocks(20)
    if len(recent) >= 2:
        avg_time = (recent[-1]["timestamp"] - recent[0]["timestamp"]) / (len(recent)-1)
    else:
        avg_time = TARGET_BLOCK_TIME

    stats_html = f"""
    <div class="container">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Altura da cadeia</div>
          <div class="stat-value">{chain.height:,}</div>
          <div class="stat-sub">blocos confirmados</div>
          <div class="stat-icon">&#9648;</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Supply circulante</div>
          <div class="stat-value">{supply:,.0f}</div>
          <div class="stat-sub">de 32.000.000 PoLM &mdash; {supply/MAX_SUPPLY_COINS*100:.3f}%</div>
          <div class="bar-wrap"><div class="bar" style="width:{min(100,supply/MAX_SUPPLY_COINS*100):.3f}%"></div></div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Dificuldade</div>
          <div class="stat-value">{tip.get('difficulty','—')}</div>
          <div class="stat-sub">bits de PoW</div>
          <div class="stat-icon">&#9881;</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Tempo médio bloco</div>
          <div class="stat-value">{avg_time:.0f}s</div>
          <div class="stat-sub">alvo: {TARGET_BLOCK_TIME}s (2.5 min)</div>
          <div class="stat-icon">&#9201;</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Época atual</div>
          <div class="stat-value">{ei['epoch']}</div>
          <div class="stat-sub">RAM mín: {ei['min_ram_mb']//1024}GB &mdash; {ei['blocks_until_next']:,} blocos para próx.</div>
          <div class="bar-wrap"><div class="bar" style="width:{min(100,(chain.height%EPOCH_INTERVAL)/EPOCH_INTERVAL*100):.1f}%"></div></div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Recompensa por bloco</div>
          <div class="stat-value">50</div>
          <div class="stat-sub">PoLM &mdash; halving a cada 210.000 blocos</div>
          <div class="stat-icon">&#9651;</div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:2fr 1fr;gap:24px">
        <div>
          <div class="section">
            <div class="section-header">
              <div class="section-title">Últimos blocos</div>
              <a class="section-link" href="/blocks">Ver todos &rarr;</a>
            </div>
            <table class="tbl">
              <thead><tr>
                <th>Altura</th><th>Hash</th><th>Minerador</th>
                <th>RAM</th><th>Score</th><th>Conf.</th><th>TXs</th><th>Tempo</th>
              </tr></thead>
              <tbody>"""

    for b in blocks:
        ram  = b.get("ram_type","AUTO")
        if isinstance(b.get("ram_proof"), dict):
            rp  = b["ram_proof"]
            ram = rp.get("ram_type", ram)
            score = rp.get("score", b.get("ram_score",0))
            conf  = rp.get("confidence", 1.0)
        else:
            score = b.get("ram_score", 0)
            conf  = 1.0
        conf_pct = int(conf * 100)
        conf_color = "#22c55e" if conf >= 0.8 else "#eab308" if conf >= 0.5 else "#ef4444"
        reward = b["transactions"][0]["outputs"][0]["value"] / COIN if b.get("transactions") else 0
        age    = _ts_ago(b["timestamp"])

        stats_html += f"""
              <tr>
                <td><a href="/block/{b['height']}">{b['height']:,}</a></td>
                <td><span class="hash-text"><a href="/block/{b['height']}">{b['hash'][:18]}…</a></span></td>
                <td><span class="addr"><a href="/address/{b['miner']}">{b['miner'][:16]}…</a></span></td>
                <td>{_ram_badge(ram)}</td>
                <td>{score:.2f}</td>
                <td>
                  <div class="conf-bar">
                    <div class="conf-wrap"><div class="conf-fill" style="width:{conf_pct}%;background:{conf_color}"></div></div>
                    <span style="color:{conf_color};font-size:10px">{conf_pct}%</span>
                  </div>
                </td>
                <td>{len(b.get('transactions',[]))}</td>
                <td class="hash-text">{age}</td>
              </tr>"""

    stats_html += f"""
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <div class="section">
            <div class="section-header">
              <div class="section-title">Top Mineradores</div>
              <a class="section-link" href="/miners">Ver todos &rarr;</a>
            </div>
            <table class="tbl">
              <thead><tr><th>Endereço</th><th>RAM</th><th>Blocos</th><th>%</th></tr></thead>
              <tbody>"""

    total_blocks = chain.height + 1
    for m in miners:
        pct = m["blocks"] / max(total_blocks, 1) * 100
        stats_html += f"""
              <tr>
                <td><span class="addr"><a href="/address/{m['address']}">{m['address'][:14]}…</a></span></td>
                <td>{_ram_badge(m['ram'])}</td>
                <td>{m['blocks']:,}</td>
                <td>
                  <div class="bar-wrap" style="width:80px"><div class="bar" style="width:{min(100,pct):.0f}%"></div></div>
                  <span style="font-size:10px;color:var(--muted2)">{pct:.1f}%</span>
                </td>
              </tr>"""

    stats_html += """
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>"""

    return _base("Dashboard", stats_html, "home")


@app.route("/blocks")
def blocks_page():
    chain  = get_chain()
    page   = int(request.args.get("page", 1))
    size   = 25
    total  = len(chain._chain)
    start  = max(0, total - page * size)
    end    = max(0, total - (page-1) * size)
    blocks = list(reversed(chain._chain[start:end]))

    rows = ""
    for b in blocks:
        ram = b.get("ram_type","AUTO")
        if isinstance(b.get("ram_proof"),dict):
            rp  = b["ram_proof"]
            ram = rp.get("ram_type", ram)
            score = rp.get("score", b.get("ram_score",0))
            conf  = rp.get("confidence",1.0)
        else:
            score = b.get("ram_score",0)
            conf  = 1.0
        reward = b["transactions"][0]["outputs"][0]["value"]/COIN if b.get("transactions") else 0
        rows += f"""
        <tr>
          <td><a href="/block/{b['height']}">{b['height']:,}</a></td>
          <td><span class="hash-text"><a href="/block/{b['height']}">{b['hash'][:24]}…</a></span></td>
          <td><span class="addr"><a href="/address/{b['miner']}">{b['miner'][:20]}…</a></span></td>
          <td>{_ram_badge(ram)}</td>
          <td>{score:.2f}</td>
          <td>{int(conf*100)}%</td>
          <td>{len(b.get('transactions',[]))}</td>
          <td class="polm">{reward:.4f}</td>
          <td class="hash-text">{_ts_fmt(b['timestamp'])}</td>
        </tr>"""

    total_pages = (total + size - 1) // size
    pages_html = ""
    for p in range(max(1,page-3), min(total_pages+1, page+4)):
        active = "active" if p==page else ""
        pages_html += f'<a class="page-btn {active}" href="/blocks?page={p}">{p}</a>'

    body = f"""
    <div class="container">
      <div class="section">
        <div class="section-header">
          <div class="section-title">Todos os blocos — {total:,} total</div>
          <span style="font-size:11px;color:var(--muted)">Página {page} de {total_pages}</span>
        </div>
        <table class="tbl">
          <thead><tr>
            <th>Altura</th><th>Hash</th><th>Minerador</th>
            <th>RAM</th><th>Score</th><th>Conf.</th><th>TXs</th><th>Recompensa</th><th>Timestamp</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <div class="pagination">
        {'<a class="page-btn" href="/blocks?page=1">« Primeiro</a>' if page > 3 else ''}
        {pages_html}
        {'<a class="page-btn" href="/blocks?page=' + str(total_pages) + '">Último »</a>' if page < total_pages - 3 else ''}
      </div>
    </div>"""
    return _base(f"Blocos — Página {page}", body, "blocks")


@app.route("/block/<int:height>")
def block_detail(height):
    chain = get_chain()
    b     = chain.get_block(height)
    if not b:
        abort(404)

    ram = b.get("ram_type","AUTO")
    rp  = b.get("ram_proof",{})
    if isinstance(rp, dict):
        ram   = rp.get("ram_type", ram)
        score = rp.get("score", b.get("ram_score",0))
        conf  = rp.get("confidence",1.0)
        lat   = rp.get("latency",0)
        therm = rp.get("thermal_ratio",1.0)
        pf    = rp.get("page_fault_ratio",1.0)
        var   = rp.get("variance",0)
        cpu_m = rp.get("cpu_mult",1.0)
        cpu_c = rp.get("cpu_cores",0)
    else:
        score = b.get("ram_score",0)
        conf  = 1.0
        lat = therm = pf = var = cpu_m = cpu_c = 0

    reward = b["transactions"][0]["outputs"][0]["value"]/COIN if b.get("transactions") else 0
    epoch  = b.get("epoch", 0)
    susp   = rp.get("is_suspicious", False) if isinstance(rp,dict) else False

    # Navegação
    prev_link = f'<a href="/block/{height-1}">&larr; Bloco {height-1}</a>' if height > 0 else ""
    next_b = chain.get_block(height+1)
    next_link = f'<a href="/block/{height+1}">Bloco {height+1} &rarr;</a>' if next_b else ""

    txs_html = ""
    for tx in b.get("transactions",[]):
        txid    = tx.get("txid","")
        is_cb   = tx["inputs"][0].get("txid","") == "0"*64
        total_v = sum(o["value"] for o in tx.get("outputs",[]))
        txs_html += f"""
        <tr>
          <td><span class="hash-text"><a href="/tx/{txid}">{txid[:28]}…</a></span></td>
          <td>{'<span class="badge badge-yellow">COINBASE</span>' if is_cb else '<span class="badge badge-blue">TX</span>'}</td>
          <td>{len(tx.get('outputs',[]))}</td>
          <td class="polm">{total_v/COIN:.8f} PoLM</td>
        </tr>"""

    body = f"""
    <div class="container">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <div style="color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:2px">
          Bloco #{height:,}
          {'<span class="badge badge-red" style="margin-left:8px">SUSPEITO</span>' if susp else ''}
        </div>
        <div style="display:flex;gap:16px;font-size:11px">{prev_link} &nbsp; {next_link}</div>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px">
        <div class="detail-card">
          <div style="padding:12px 20px;border-bottom:1px solid var(--border);font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--muted2)">Informações do bloco</div>
          <div class="detail-row"><div class="detail-key">Hash</div><div class="detail-val hash-text">{b['hash']}</div></div>
          <div class="detail-row"><div class="detail-key">Altura</div><div class="detail-val">{height:,}</div></div>
          <div class="detail-row"><div class="detail-key">Época</div><div class="detail-val">{epoch}</div></div>
          <div class="detail-row"><div class="detail-key">Bloco anterior</div><div class="detail-val hash-text"><a href="/block/{height-1}">{b['prev_hash'][:32]}…</a></div></div>
          <div class="detail-row"><div class="detail-key">Merkle Root</div><div class="detail-val hash-text">{b.get('merkle_root','')[:32]}…</div></div>
          <div class="detail-row"><div class="detail-key">Timestamp</div><div class="detail-val">{_ts_fmt(b['timestamp'])}</div></div>
          <div class="detail-row"><div class="detail-key">Dificuldade</div><div class="detail-val">{b.get('difficulty',0)} bits</div></div>
          <div class="detail-row"><div class="detail-key">Nonce</div><div class="detail-val">{b.get('nonce',0):,}</div></div>
          <div class="detail-row"><div class="detail-key">Recompensa</div><div class="detail-val polm">{reward:.8f} PoLM</div></div>
        </div>

        <div class="detail-card">
          <div style="padding:12px 20px;border-bottom:1px solid var(--border);font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--muted2)">Prova de RAM física</div>
          <div class="detail-row"><div class="detail-key">Minerador</div><div class="detail-val"><a href="/address/{b['miner']}" class="addr">{b['miner']}</a></div></div>
          <div class="detail-row"><div class="detail-key">Tipo de RAM</div><div class="detail-val">{_ram_badge(ram)}</div></div>
          <div class="detail-row"><div class="detail-key">Score RAM</div><div class="detail-val polm">{score:.4f}</div></div>
          <div class="detail-row"><div class="detail-key">Latência</div><div class="detail-val">{lat:.6f}s</div></div>
          <div class="detail-row">
            <div class="detail-key">Confiança física</div>
            <div class="detail-val">
              <div class="conf-bar">
                <div class="conf-wrap"><div class="conf-fill" style="width:{int(conf*100)}%;background:{'#22c55e' if conf>=0.8 else '#eab308' if conf>=0.5 else '#ef4444'}"></div></div>
                <span style="color:{'#22c55e' if conf>=0.8 else '#eab308' if conf>=0.5 else '#ef4444'}">{int(conf*100)}%</span>
              </div>
            </div>
          </div>
          <div class="detail-row"><div class="detail-key">Thermal ratio</div><div class="detail-val">{'✅ ' if therm>=1.03 else '⚠️ '}{therm:.4f}</div></div>
          <div class="detail-row"><div class="detail-key">Page fault ratio</div><div class="detail-val">{'✅ ' if pf>=1.1 else '⚠️ '}{pf:.4f}</div></div>
          <div class="detail-row"><div class="detail-key">Variância RAM</div><div class="detail-val">{'✅ ' if 0.02<=var<=0.35 else '⚠️ '}{var:.4f}</div></div>
          <div class="detail-row"><div class="detail-key">CPU cores</div><div class="detail-val">{cpu_c} cores &mdash; mult {cpu_m:.2f}x</div></div>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <div class="section-title">Transações ({len(b.get('transactions',[]))})</div>
        </div>
        <table class="tbl">
          <thead><tr><th>TXID</th><th>Tipo</th><th>Outputs</th><th>Valor</th></tr></thead>
          <tbody>{txs_html}</tbody>
        </table>
      </div>
    </div>"""
    return _base(f"Bloco #{height}", body, "blocks")


@app.route("/miners")
def miners_page():
    chain  = get_chain()
    miners = _get_miner_stats(chain, min(chain.height+1, 1000))

    rows = ""
    for i, m in enumerate(miners):
        pct = m["pct"]
        rows += f"""
        <tr>
          <td style="color:var(--muted)">{i+1}</td>
          <td><a href="/address/{m['address']}" class="addr">{m['address']}</a></td>
          <td>{_ram_badge(m['ram'])}</td>
          <td>{m['blocks']:,}</td>
          <td>
            <div class="bar-wrap"><div class="bar" style="width:{min(100,pct*2):.0f}%"></div></div>
            {pct:.1f}%
          </td>
          <td>{m['avg_score']:.2f}</td>
          <td>{int(m['avg_conf']*100)}%</td>
          <td class="polm">{m['reward_polm']:,.4f}</td>
        </tr>"""

    body = f"""
    <div class="container">
      <div class="section">
        <div class="section-header">
          <div class="section-title">Ranking de Mineradores — últimos {min(chain.height+1,1000)} blocos</div>
        </div>
        <table class="tbl">
          <thead><tr>
            <th>#</th><th>Endereço</th><th>RAM</th><th>Blocos</th>
            <th>% da rede</th><th>Score médio</th><th>Confiança</th><th>PoLM ganhos</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
    </div>"""
    return _base("Mineradores", body, "miners")


@app.route("/address/<addr>")
def address_page(addr):
    chain   = get_chain()
    utxos   = chain.utxo.get_by_address(addr, chain.height)
    balance = sum(u["value"] for u in utxos) / COIN

    # Histórico de blocos minerados
    mined = []
    for b in reversed(chain.get_recent_blocks(500)):
        if b.get("miner") == addr:
            mined.append(b)

    rows = ""
    for b in mined[:50]:
        reward = b["transactions"][0]["outputs"][0]["value"]/COIN if b.get("transactions") else 0
        rows += f"""
        <tr>
          <td><a href="/block/{b['height']}">{b['height']:,}</a></td>
          <td class="hash-text">{b['hash'][:24]}…</td>
          <td>{_ram_badge(b.get('ram_type','AUTO'))}</td>
          <td class="polm">{reward:.4f}</td>
          <td class="hash-text">{_ts_fmt(b['timestamp'])}</td>
        </tr>"""

    utxo_rows = ""
    for u in utxos[:20]:
        mature = "✅" if not u.get("coinbase") or (chain.height - u["height"]) >= 100 else "⏳"
        utxo_rows += f"""
        <tr>
          <td class="hash-text">{u['txid'][:24]}…</td>
          <td>{u.get('height',0):,}</td>
          <td class="polm">{u['value']/COIN:.8f}</td>
          <td>{mature}</td>
        </tr>"""

    body = f"""
    <div class="container">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:24px">
        <div class="stat-card">
          <div class="stat-label">Saldo disponível</div>
          <div class="stat-value" style="font-size:20px">{balance:,.4f}</div>
          <div class="stat-sub">PoLM</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Blocos minerados</div>
          <div class="stat-value">{len(mined):,}</div>
          <div class="stat-sub">nos últimos 500 blocos</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">UTXOs disponíveis</div>
          <div class="stat-value">{len(utxos)}</div>
          <div class="stat-sub">saídas não gastas</div>
        </div>
      </div>

      <div class="detail-card" style="margin-bottom:24px">
        <div style="padding:12px 20px;border-bottom:1px solid var(--border);font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--muted2)">Endereço</div>
        <div class="detail-row"><div class="detail-key">Endereço</div><div class="detail-val hash-text">{addr}</div></div>
        <div class="detail-row"><div class="detail-key">Saldo total</div><div class="detail-val polm">{balance:,.8f} PoLM</div></div>
        <div class="detail-row"><div class="detail-key">UTXOs</div><div class="detail-val">{len(utxos)}</div></div>
      </div>

      <div class="section" style="margin-bottom:24px">
        <div class="section-header"><div class="section-title">Blocos minerados (últimos 50)</div></div>
        <table class="tbl">
          <thead><tr><th>Altura</th><th>Hash</th><th>RAM</th><th>Recompensa</th><th>Timestamp</th></tr></thead>
          <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:24px">Nenhum bloco minerado</td></tr>'}</tbody>
        </table>
      </div>

      <div class="section">
        <div class="section-header"><div class="section-title">UTXOs (saídas não gastas)</div></div>
        <table class="tbl">
          <thead><tr><th>TXID</th><th>Bloco</th><th>Valor</th><th>Matura</th></tr></thead>
          <tbody>{utxo_rows if utxo_rows else '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:24px">Sem UTXOs</td></tr>'}</tbody>
        </table>
      </div>
    </div>"""
    return _base(f"Endereço {addr[:16]}…", body)


@app.route("/epochs")
def epochs_page():
    chain = get_chain()
    h     = chain.height

    cards = ""
    for epoch in range(11):
        height_start = epoch * EPOCH_INTERVAL
        height_end   = (epoch + 1) * EPOCH_INTERVAL - 1
        is_current   = get_epoch_info(h)["epoch"] == epoch
        is_past      = h > height_end
        status_class = "status-active" if is_current else "status-past" if is_past else "status-future"
        status_text  = "Ativa agora" if is_current else "Concluída" if is_past else "Futura"

        cfg     = get_epoch_config(height_start)
        min_gb  = cfg.get("min_ram_mb", 0) // 1024
        allowed = {k:v for k,v in cfg.items() if k not in ("min_ram_mb","_cpu","_min_ram_by_type") and v is not None}
        obsolete= [k for k,v in cfg.items() if k not in ("min_ram_mb","_cpu","_min_ram_by_type") and v is None]

        ram_rows = ""
        for ram, mult in allowed.items():
            stick_mb  = {"DDR1":1024,"DDR2":2048,"DDR3":8192,"DDR4":32768,"DDR5":65536}.get(ram,2048)
            min_ram_mb = cfg.get("_min_ram_by_type",{}).get(ram, cfg.get("min_ram_mb",2048))
            sticks    = max(1, min_ram_mb // stick_mb)
            ram_rows += f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:11px"><span>{_ram_badge(ram)}</span><span style="color:var(--accent)">{mult}x</span><span style="color:var(--muted2)">{sticks}x sticks</span></div>'

        for ram in obsolete:
            ram_rows += f'<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:11px"><span>{_ram_badge(ram)}</span><span style="color:var(--red)">OBSOLETO</span></div>'

        # Investimento estimado
        invest = {"DDR1":3,"DDR2":5,"DDR3":15,"DDR4":80,"DDR5":200}
        dom_ram = list(allowed.keys())[0] if allowed else "DDR5"
        dom_stick = {"DDR1":1024,"DDR2":2048,"DDR3":8192,"DDR4":32768,"DDR5":65536}.get(dom_ram,2048)
        n_sticks = max(1, cfg.get("min_ram_mb",2048) // dom_stick)
        est_usd  = n_sticks * invest.get(dom_ram, 50)

        cards += f"""
        <div class="epoch-card {'border:2px solid var(--accent)' if is_current else ''}">
          <span class="epoch-num">{epoch}</span>
          <div><span class="epoch-status {status_class}">{status_text}</span></div>
          <div style="font-size:18px;font-weight:700;margin-bottom:4px">Época {epoch}</div>
          <div style="font-size:11px;color:var(--muted2);margin-bottom:16px">
            Blocos {height_start:,} – {height_end:,}
          </div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:8px">RAM mínima: <b style="color:var(--text)">{min_gb}GB</b></div>
          <div style="font-size:11px;color:var(--muted);margin-bottom:12px">Invest. estimado: <b style="color:var(--yellow)">~${est_usd:,}</b></div>
          <div style="border-top:1px solid var(--border);padding-top:12px">{ram_rows}</div>
        </div>"""

    body = f"""
    <div class="container">
      <div style="margin-bottom:24px">
        <div style="font-size:11px;color:var(--muted2);margin-bottom:8px;text-transform:uppercase;letter-spacing:2px">Sistema de épocas PoLM</div>
        <div style="font-size:13px;color:var(--text);max-width:800px;line-height:1.8">
          A cada época (~1 ano), a RAM mínima dobra e a geração mais antiga de hardware sai de circulação.
          Assim como Bitcoin exige mais energia com o tempo, PoLM exige mais RAM física —
          incentivando hardware dedicado e preservação de memórias antigas.
        </div>
      </div>
      <div class="epoch-grid">{cards}</div>
    </div>"""
    return _base("Épocas", body, "epochs")


@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    if not q:
        return redirect("/")
    chain = get_chain()
    # Tenta como altura
    try:
        height = int(q)
        if chain.get_block(height):
            return redirect(f"/block/{height}")
    except Exception:
        pass
    # Tenta como hash de bloco
    b = chain.get_block_by_hash(q)
    if b:
        return redirect(f"/block/{b['height']}")
    # Tenta como endereço
    if len(q) >= 20:
        return redirect(f"/address/{q}")
    # Tenta como txid
    return redirect(f"/tx/{q}")


@app.route("/tx/<txid>")
def tx_detail(txid):
    chain = get_chain()
    for b in reversed(chain._chain):
        for tx in b.get("transactions",[]):
            if tx.get("txid") == txid:
                ins_html  = "".join(f'<div class="detail-row"><div class="detail-key">Input {i}</div><div class="detail-val hash-text">{inp.get("txid","")[:32]}… : {inp.get("vout","")}</div></div>' for i,inp in enumerate(tx.get("inputs",[])))
                outs_html = "".join(f'<div class="detail-row"><div class="detail-key">Output {i}</div><div class="detail-val"><a href="/address/{out.get("address","")}" class="addr">{out.get("address","")}</a> &mdash; <span class="polm">{out.get("value",0)/COIN:.8f} PoLM</span></div></div>' for i,out in enumerate(tx.get("outputs",[])))
                body = f"""
                <div class="container">
                  <div class="detail-card">
                    <div style="padding:12px 20px;border-bottom:1px solid var(--border);font-size:10px;text-transform:uppercase;letter-spacing:2px;color:var(--muted2)">Transação</div>
                    <div class="detail-row"><div class="detail-key">TXID</div><div class="detail-val hash-text">{txid}</div></div>
                    <div class="detail-row"><div class="detail-key">Bloco</div><div class="detail-val"><a href="/block/{b['height']}">{b['height']:,}</a></div></div>
                    <div class="detail-row"><div class="detail-key">Timestamp</div><div class="detail-val">{_ts_fmt(b['timestamp'])}</div></div>
                    <div class="detail-row"><div class="detail-key">Tipo</div><div class="detail-val">{'<span class="badge badge-yellow">COINBASE</span>' if tx["inputs"][0].get("txid","")=="0"*64 else '<span class="badge badge-blue">TRANSFERÊNCIA</span>'}</div></div>
                    {ins_html}{outs_html}
                  </div>
                </div>"""
                return _base(f"TX {txid[:16]}…", body)
    abort(404)


# ═══════════════════════════════════════════════════════════
# API JSON
# ═══════════════════════════════════════════════════════════

@app.route("/api/stats")
def api_stats():
    chain  = get_chain()
    tip    = chain.tip or {}
    supply = chain.total_supply() / COIN
    ei     = get_epoch_info(chain.height)
    recent = chain.get_recent_blocks(20)
    avg_t  = (recent[-1]["timestamp"]-recent[0]["timestamp"])/(len(recent)-1) if len(recent)>=2 else TARGET_BLOCK_TIME
    return jsonify({
        "height":       chain.height,
        "tip_hash":     tip.get("hash",""),
        "difficulty":   tip.get("difficulty",0),
        "supply_polm":  round(supply,8),
        "supply_pct":   round(supply/MAX_SUPPLY_COINS*100,6),
        "max_supply":   MAX_SUPPLY_COINS,
        "avg_block_time": round(avg_t,2),
        "epoch":        ei,
        "timestamp":    time.time(),
    })

@app.route("/api/blocks")
def api_blocks():
    chain  = get_chain()
    page   = int(request.args.get("page",1))
    size   = int(request.args.get("size",20))
    total  = len(chain._chain)
    start  = max(0, total - page*size)
    end    = max(0, total - (page-1)*size)
    return jsonify({
        "page": page, "size": size, "total": total,
        "blocks": list(reversed(chain._chain[start:end]))
    })

@app.route("/api/block/<int:height>")
def api_block(height):
    chain = get_chain()
    b = chain.get_block(height)
    if not b: abort(404)
    return jsonify(b)

@app.route("/api/address/<addr>")
def api_address(addr):
    chain   = get_chain()
    utxos   = chain.utxo.get_by_address(addr, chain.height)
    balance = sum(u["value"] for u in utxos)
    return jsonify({"address":addr,"balance_sats":balance,"balance_polm":balance/COIN,"utxos":utxos})

@app.route("/api/epoch")
def api_epoch():
    chain = get_chain()
    return jsonify(get_epoch_info(chain.height))

@app.route("/api/miners")
def api_miners():
    chain = get_chain()
    return jsonify(_get_miner_stats(chain))

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    chain = get_chain()
    print(f"\n  PoLM Explorer v2.0 — http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
