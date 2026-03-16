"""
PoLM Explorer v3.2 — Professional Black Edition
"""
from flask import Flask, render_template_string, jsonify, request
import json, time, urllib.request

EXPLORER_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PoLM Explorer</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#08090b;--s1:#0e1117;--s2:#141820;--s3:#1c2330;
  --b1:#252f3e;--b2:#2e3b4e;
  --cyan:#22d3ee;--cyan2:#06b6d4;--green:#22c55e;
  --amber:#f59e0b;--orange:#f97316;--purple:#a78bfa;
  --t1:#f1f5f9;--t2:#94a3b8;--t3:#475569;
  --mono:'JetBrains Mono',monospace;
  --sans:'Space Grotesk',sans-serif;
}
html{font-size:13px}
body{background:var(--bg);color:var(--t1);font-family:var(--sans);min-height:100vh;
  background-image:radial-gradient(ellipse 60% 40% at 50% 0%,rgba(34,211,238,.04) 0%,transparent 70%)}
header{background:rgba(14,17,23,.97);border-bottom:1px solid var(--b1);
  padding:0 28px;height:56px;display:flex;align-items:center;gap:16px;
  position:sticky;top:0;z-index:200;backdrop-filter:blur(12px)}
.logo{font-family:var(--mono);font-size:1.05rem;font-weight:700;color:var(--cyan)}
.logo span{color:var(--t2);font-weight:400}
.badge{background:rgba(34,197,94,.1);border:1px solid rgba(34,197,94,.2);
  color:var(--green);font-size:.6rem;padding:3px 10px;border-radius:20px;font-family:var(--mono);
  display:flex;align-items:center;gap:5px}
.badge::before{content:'';width:5px;height:5px;border-radius:50%;background:var(--green);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.hdr-right{margin-left:auto;display:flex;align-items:center;gap:10px}
#ts{font-size:.62rem;color:var(--t3);font-family:var(--mono)}
.rbtn{background:var(--s2);border:1px solid var(--b1);color:var(--t2);
  padding:5px 12px;border-radius:6px;cursor:pointer;font-family:var(--mono);font-size:.68rem;transition:all .15s}
.rbtn:hover{border-color:var(--cyan);color:var(--cyan)}

.wrap{max-width:1440px;margin:0 auto;padding:20px 18px}

.search-row{margin-bottom:20px;display:flex;gap:8px;max-width:600px}
.search-row input{flex:1;background:var(--s1);border:1px solid var(--b1);border-radius:8px;
  padding:9px 14px;color:var(--t1);font-family:var(--mono);font-size:.8rem;outline:none;transition:border-color .15s}
.search-row input:focus{border-color:var(--cyan)}
.search-row input::placeholder{color:var(--t3)}
.search-row button{background:var(--cyan);border:none;color:#000;padding:9px 18px;
  border-radius:8px;cursor:pointer;font-family:var(--sans);font-size:.75rem;font-weight:600}

.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:8px;margin-bottom:20px}
.sc{background:var(--s1);border:1px solid var(--b1);border-radius:10px;padding:14px;
  position:relative;overflow:hidden;transition:border-color .15s}
.sc::after{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--ac,var(--cyan));opacity:.4}
.sc:hover{border-color:var(--b2)}
.sc-lbl{font-size:.58rem;color:var(--t3);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px;font-family:var(--mono)}
.sc-val{font-size:1.2rem;font-weight:700;color:var(--t1);font-family:var(--mono);line-height:1}
.sc-sub{font-size:.6rem;color:var(--t3);margin-top:3px;font-family:var(--mono)}

.sec{background:var(--s1);border:1px solid var(--b1);border-radius:10px;padding:18px;margin-bottom:14px}
.sec-ttl{font-size:.62rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
  color:var(--t2);margin-bottom:14px;display:flex;align-items:center;gap:8px;font-family:var(--mono)}
.sec-ttl::after{content:'';flex:1;height:1px;background:var(--b1)}

.supply-bar-bg{height:5px;background:var(--s3);border-radius:3px;overflow:hidden;margin:8px 0}
.supply-bar-fill{height:100%;background:var(--cyan);border-radius:3px;transition:width .8s}
.supply-meta{display:flex;justify-content:space-between;font-size:.62rem;color:var(--t3);font-family:var(--mono)}

.two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
@media(max-width:880px){.two{grid-template-columns:1fr}}

.mrow{display:grid;grid-template-columns:22px 1fr 70px 52px 60px 44px;
  align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--b1)}
.mrow:last-child{border-bottom:none}
.rnk{font-family:var(--mono);font-size:.65rem;color:var(--t3);font-weight:700}
.rnk.r1{color:#fbbf24}.rnk.r2{color:#94a3b8}.rnk.r3{color:#b45309}
.minfo{min-width:0}
.maddr{font-family:var(--mono);font-size:.7rem;color:var(--cyan);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mmeta{font-size:.6rem;color:var(--t3);margin-top:1px;font-family:var(--mono)}
.bar-bg{height:3px;background:var(--s3);border-radius:2px;overflow:hidden}
.bar-fill{height:100%;border-radius:2px;transition:width .5s}
.num{font-family:var(--mono);font-size:.72rem;text-align:right;white-space:nowrap}
.gc{color:var(--green)}.ac{color:var(--amber)}.cc{color:var(--cyan)}.mc{color:var(--t3)}

.ram{display:inline-block;padding:1px 6px;border-radius:3px;font-size:.58rem;font-weight:700;font-family:var(--mono)}
.ddr2{background:rgba(249,115,22,.1);color:#fb923c;border:1px solid rgba(249,115,22,.18)}
.ddr3{background:rgba(245,158,11,.08);color:#fbbf24;border:1px solid rgba(245,158,11,.18)}
.ddr4{background:rgba(34,211,238,.07);color:var(--cyan);border:1px solid rgba(34,211,238,.14)}
.ddr5{background:rgba(34,197,94,.07);color:var(--green);border:1px solid rgba(34,197,94,.14)}

.bgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}
@media(max-width:580px){.bgrid{grid-template-columns:repeat(2,1fr)}}
.bc{background:var(--s2);border:1px solid var(--b1);border-radius:8px;padding:12px;text-align:center}
.bt{font-family:var(--mono);font-size:.95rem;font-weight:700;margin-bottom:3px}
.bm{font-size:1.3rem;font-weight:700;font-family:var(--mono)}
.bs{font-size:.58rem;color:var(--t3);margin-top:3px;font-family:var(--mono)}
.b2 .bt,.b2 .bm{color:#fb923c}.b3 .bt,.b3 .bm{color:#fbbf24}
.b4 .bt,.b4 .bm{color:var(--cyan)}.b5 .bt,.b5 .bm{color:var(--green)}

.irow{display:flex;justify-content:space-between;align-items:center;
  padding:6px 0;border-bottom:1px solid var(--b1);font-size:.73rem}
.irow:last-child{border-bottom:none}
.ik{color:var(--t3);font-family:var(--mono)}.iv{color:var(--t1);font-family:var(--mono);font-weight:500}

table{width:100%;border-collapse:collapse;font-size:.72rem}
th{text-align:left;padding:7px 10px;color:var(--t3);font-size:.58rem;letter-spacing:.1em;
  text-transform:uppercase;border-bottom:1px solid var(--b1);font-family:var(--mono);font-weight:400}
td{padding:9px 10px;border-bottom:1px solid rgba(37,47,62,.4);vertical-align:middle;font-family:var(--mono)}
tr:hover td{background:rgba(34,211,238,.02);cursor:pointer}
tr:last-child td{border-bottom:none}
a.hl{color:var(--cyan);text-decoration:none;font-size:.7rem}
a.hl:hover{text-decoration:underline}
.hm{color:var(--t3);font-size:.65rem}

footer{border-top:1px solid var(--b1);padding:16px 28px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.fl{font-size:.62rem;color:var(--t3);font-family:var(--mono)}
</style>
</head>
<body>
<header>
  <div class="logo">PoLM <span>Explorer</span></div>
  <div class="badge">testnet</div>
  <div class="hdr-right">
    <span id="ts"></span>
    <button class="rbtn" onclick="load()">refresh</button>
  </div>
</header>

<div class="wrap">
  <div class="search-row">
    <input id="q" placeholder="Block height or hash (64 chars)…" onkeydown="if(event.key==='Enter')go()">
    <button onclick="go()">Search</button>
  </div>

  <div class="sgrid" id="sg"></div>

  <div class="sec">
    <div class="sec-ttl">Supply</div>
    <div style="display:flex;justify-content:space-between;font-size:.75rem;font-family:var(--mono)">
      <span id="sm" style="color:var(--cyan)"></span>
      <span style="color:var(--t3)">/ 32,000,000 POLM</span>
    </div>
    <div class="supply-bar-bg"><div class="supply-bar-fill" id="sb" style="width:0%"></div></div>
    <div class="supply-meta"><span id="sp"></span><span>halving every ~4yr · 5.0 POLM initial</span></div>
  </div>

  <div class="two">
    <div class="sec">
      <div class="sec-ttl">Miner leaderboard</div>
      <div id="lb"></div>
    </div>
    <div>
      <div class="sec" style="margin-bottom:14px">
        <div class="sec-ttl">Network info</div>
        <div id="ni"></div>
      </div>
      <div class="sec">
        <div class="sec-ttl">Legacy boost multipliers</div>
        <div class="bgrid">
          <div class="bc b2"><div class="bt">DDR2</div><div class="bm">6.00×</div><div class="bs">80 steps</div></div>
          <div class="bc b3"><div class="bt">DDR3</div><div class="bm">2.80×</div><div class="bs">150 steps</div></div>
          <div class="bc b4"><div class="bt">DDR4</div><div class="bm">1.00×</div><div class="bs">500 steps</div></div>
          <div class="bc b5"><div class="bt">DDR5</div><div class="bm">0.70×</div><div class="bs">700 steps</div></div>
        </div>
      </div>
    </div>
  </div>

  <div class="sec">
    <div class="sec-ttl" style="justify-content:space-between">
      <span>Latest blocks</span>
      <span id="bc" style="color:var(--t3);font-size:.6rem;font-weight:400;letter-spacing:0"></span>
    </div>
    <div style="overflow-x:auto">
    <table>
      <thead><tr><th>Height</th><th>Hash</th><th>Miner</th><th>RAM</th><th>Latency</th><th>Score</th><th>Reward</th><th>Age</th></tr></thead>
      <tbody id="bb"></tbody>
    </table>
    </div>
  </div>
</div>

<footer>
  <div class="fl">PoLM v3.1.0 &nbsp;·&nbsp; Proof of Legacy Memory &nbsp;·&nbsp; MIT</div>
  <div class="fl"><a href="https://github.com/proof-of-legacy/Proof-of-Legacy-Memory" style="color:var(--cyan);text-decoration:none">github.com/proof-of-legacy</a></div>
</footer>

<script>
const B={DDR2:6,DDR3:2.8,DDR4:1,DDR5:.7};
const RC={DDR2:'#fb923c',DDR3:'#fbbf24',DDR4:'#22d3ee',DDR5:'#22c55e'};
async function load(){
  try{
    const[s,bl,m]=await Promise.all([
      fetch('/api/summary').then(r=>r.json()),
      fetch('/api/blocks?limit=30').then(r=>r.json()),
      fetch('/api/miners').then(r=>r.json()),
    ]);
    rStats(s);rSupply(s);rLeader(m);rNet(s);rBlocks(bl);
    document.getElementById('bc').textContent='showing 30 of '+(s.height+1);
    document.getElementById('ts').textContent='updated '+new Date().toLocaleTimeString();
  }catch(e){console.error(e)}
}
function rStats(s){
  const ep=((s.height%100000)/100000*100).toFixed(1);
  const items=[
    {l:'Block Height',v:s.height.toLocaleString(),s:'blocks mined',a:'var(--cyan)'},
    {l:'Difficulty',v:s.difficulty,s:'target: '+'0'.repeat(s.difficulty)+'…',a:'var(--amber)'},
    {l:'Next Reward',v:s.next_reward.toFixed(2)+' POLM',s:'per block',a:'var(--green)'},
    {l:'Epoch',v:s.epoch,s:ep+'% complete',a:'var(--purple)'},
    {l:'Block Time',v:s.block_time+'s',s:'target interval',a:'var(--orange)'},
    {l:'Chain Tip',v:s.tip_hash.slice(0,8)+'…',s:'sha3-256',a:'var(--cyan)'},
  ];
  document.getElementById('sg').innerHTML=items.map(i=>
    `<div class="sc" style="--ac:${i.a}"><div class="sc-lbl">${i.l}</div><div class="sc-val">${i.v}</div><div class="sc-sub">${i.s}</div></div>`
  ).join('');
}
function rSupply(s){
  const p=(s.total_supply/s.max_supply*100);
  document.getElementById('sm').textContent=Number(s.total_supply).toLocaleString('en',{maximumFractionDigits:0})+' POLM mined';
  document.getElementById('sb').style.width=Math.min(p,100).toFixed(6)+'%';
  document.getElementById('sp').textContent=p.toFixed(4)+'% of max';
}
function rb(r){const c={DDR2:'ddr2',DDR3:'ddr3',DDR4:'ddr4',DDR5:'ddr5'}[r]||'ddr4';return`<span class="ram ${c}">${r}</span>`}
function rLeader(m){
  const s=Object.entries(m).sort((a,b)=>b[1].blocks-a[1].blocks);
  const t=s.reduce((x,[,v])=>x+v.blocks,0);
  const rk=['r1','r2','r3'];
  document.getElementById('lb').innerHTML=s.map(([id,v],i)=>{
    const p=t?(v.blocks/t*100):0;
    const boost=B[v.ram]||1;
    return`<div class="mrow">
      <div class="rnk ${rk[i]||''}">#${i+1}</div>
      <div class="minfo">
        <div class="maddr">${id.slice(0,26)}…</div>
        <div class="mmeta">${rb(v.ram)} boost ${boost}× · ${v.avg_latency.toFixed(0)}ns avg</div>
      </div>
      <div class="bar-bg"><div class="bar-fill" style="width:${Math.min(p,100).toFixed(1)}%;background:${RC[v.ram]||'#22d3ee'}"></div></div>
      <div class="num cc">${v.blocks}</div>
      <div class="num gc">${v.reward.toFixed(0)}</div>
      <div class="num mc">${p.toFixed(1)}%</div>
    </div>`;
  }).join('');
}
function rNet(s){
  const rows=[['Symbol','POLM'],['Max supply','32,000,000'],['Halving','every ~4 years'],
    ['Retarget','every 144 blocks'],['Hash algo','SHA3-256'],['Version','v3.1.0']];
  document.getElementById('ni').innerHTML=rows.map(([k,v])=>
    `<div class="irow"><span class="ik">${k}</span><span class="iv">${v}</span></div>`).join('');
}
function age(ts){const d=Math.floor(Date.now()/1000)-ts;
  if(d<60)return d+'s';if(d<3600)return Math.floor(d/60)+'m'+Math.floor(d%60)+'s';
  return Math.floor(d/3600)+'h'+Math.floor((d%3600)/60)+'m';}
function rBlocks(bl){
  if(!bl.length){document.getElementById('bb').innerHTML='<tr><td colspan="8" style="text-align:center;padding:28px;color:var(--t3)">No blocks</td></tr>';return;}
  document.getElementById('bb').innerHTML=bl.map(b=>{
    const c=RC[b.ram_type]||'#22d3ee';
    return`<tr onclick="window.location='/block/${b.height}'">
      <td style="color:${c};font-weight:600">${b.height}</td>
      <td><a class="hl" href="/block/${b.height}">${b.block_hash.slice(0,14)}…</a></td>
      <td style="color:var(--t2);max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${b.miner_id.slice(0,16)}…</td>
      <td>${rb(b.ram_type)}</td>
      <td style="color:var(--t3)">${Number(b.latency_ns).toFixed(0)}ns</td>
      <td style="color:var(--amber)">${Number(b.score).toLocaleString('en',{maximumFractionDigits:0})}</td>
      <td style="color:var(--green)">${b.reward.toFixed(1)}</td>
      <td style="color:var(--t3)">${age(b.timestamp)}</td>
    </tr>`;}).join('');
}
function go(){
  const q=document.getElementById('q').value.trim();
  if(!q)return;
  if(/^[0-9]+$/.test(q)){window.location='/block/'+q;return;}
  if(q.length===64){window.location='/block/hash/'+q;return;}
  alert('Enter a valid block height or 64-char hash');
}
load();setInterval(load,8000);
</script>
</body>
</html>"""

BLOCK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Block #{{ height }} — PoLM Explorer</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#08090b;--s1:#0e1117;--b1:#252f3e;--cyan:#22d3ee;--green:#22c55e;--amber:#f59e0b;--t1:#f1f5f9;--t2:#94a3b8;--t3:#475569;--mono:'JetBrains Mono',monospace;--sans:'Space Grotesk',sans-serif}
body{background:var(--bg);color:var(--t1);font-family:var(--sans);padding:28px;min-height:100vh}
a.back{color:var(--cyan);text-decoration:none;font-size:.78rem;font-family:var(--mono);display:inline-block;margin-bottom:18px}
h1{font-size:1.3rem;font-weight:700;margin-bottom:18px;font-family:var(--mono);color:var(--cyan)}
.card{background:var(--s1);border:1px solid var(--b1);border-radius:10px;padding:18px}
.row{display:flex;justify-content:space-between;gap:16px;padding:9px 0;border-bottom:1px solid var(--b1);font-size:.78rem}
.row:last-child{border-bottom:none}
.k{color:var(--t3);font-family:var(--mono);min-width:130px;flex-shrink:0}
.v{color:var(--t1);font-family:var(--mono);word-break:break-all;text-align:right}
.cyan{color:var(--cyan)}.green{color:var(--green)}.amber{color:var(--amber)}
</style>
</head>
<body>
<a class="back" href="/">← back to explorer</a>
<h1>Block #{{ height }}</h1>
<div class="card">
{% for key, val, cls in rows %}
<div class="row"><span class="k">{{ key }}</span><span class="v {{ cls }}">{{ val }}</span></div>
{% endfor %}
</div>
</body>
</html>"""


def create_explorer(node_url="http://localhost:6060", port=5050):
    app = Flask("polm-explorer-v32")

    def fetch(path):
        try:
            r = urllib.request.urlopen(f"{node_url}{path}", timeout=5)
            return json.loads(r.read())
        except:
            return None

    @app.route("/")
    def index():
        return EXPLORER_HTML

    @app.route("/api/summary")
    def api_summary():
        d = fetch("/")
        return app.response_class(json.dumps(d or {"error":"offline"}), mimetype='application/json')

    @app.route("/api/blocks")
    def api_blocks():
        limit = request.args.get("limit", 30)
        d = fetch(f"/chain?limit={limit}")
        return app.response_class(json.dumps(d or []), mimetype='application/json')

    @app.route("/api/miners")
    def api_miners():
        d = fetch("/miners")
        return app.response_class(json.dumps(d or {}), mimetype='application/json')

    @app.route("/block/<int:h>")
    def block_detail(h):
        b = fetch(f"/block/{h}")
        if not b:
            return "Block not found", 404
        ts = time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(b["timestamp"]))
        rows = [
            ("height",       str(b["height"]),                           "cyan"),
            ("hash",         b["block_hash"],                            "cyan"),
            ("prev hash",    b["prev_hash"],                             ""),
            ("timestamp",    f"{b['timestamp']} ({ts})",                 ""),
            ("miner",        b["miner_id"],                              "amber"),
            ("RAM type",     b["ram_type"],                              ""),
            ("threads",      str(b["threads"]),                          ""),
            ("epoch",        str(b["epoch"]),                            ""),
            ("difficulty",   str(b["difficulty"]),                       ""),
            ("nonce",        f"{b['nonce']:,}",                         ""),
            ("latency proof",f"{b['latency_ns']:.2f} ns",               "amber"),
            ("memory proof", b["mem_proof"],                             ""),
            ("score",        f"{b['score']:,.0f}",                      ""),
            ("reward",       f"{b['reward']} POLM",                     "green"),
        ]
        return render_template_string(BLOCK_HTML, height=h, rows=rows)

    @app.route("/block/hash/<h>")
    def block_by_hash(h):
        blocks = fetch("/chain?limit=500") or []
        for b in blocks:
            if b.get("block_hash") == h:
                return block_detail(b["height"])
        return "Block not found", 404

    print(f"\n[Explorer] PoLM Explorer v3.2 Professional")
    print(f"[Explorer] Node: {node_url}")
    print(f"[Explorer] http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    import sys
    node = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:6060"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 5050
    create_explorer(node_url=node, port=port)
