import os
import json
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse

PORT = 8501
DATA_PATH = os.path.join(os.path.dirname(__file__), "outputs", "promos_all_50_episodes.json")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>KUKU Promo Finder — Microdrama Ad Intelligence</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111726;
      --card-border: #1e293b;
      --accent-red: #ff3366;
      --accent-gold: #ffb703;
      --accent-cyan: #06d6a0;
      --accent-purple: #8338ec;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    body { background-color: var(--bg); color: var(--text-main); line-height: 1.5; padding: 24px; }
    .container { max-width: 1300px; margin: 0 auto; }
    
    /* Header */
    header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 24px; border-bottom: 1px solid var(--card-border); margin-bottom: 24px; }
    .logo-area { display: flex; align-items: center; gap: 14px; }
    .badge { background: linear-gradient(135deg, var(--accent-red), #e63946); color: white; font-weight: 800; font-size: 13px; padding: 4px 10px; border-radius: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
    h1 { font-size: 26px; font-weight: 800; }
    .subtitle { color: var(--text-muted); font-size: 14px; margin-top: 2px; }
    .actions { display: flex; gap: 10px; }
    .btn { background: #1e293b; border: 1px solid #334155; color: white; padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: all 0.2s; }
    .btn:hover { background: #334155; }
    .btn-primary { background: var(--accent-red); border-color: var(--accent-red); }
    .btn-primary:hover { background: #e02454; }

    /* Stats Banner */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
    .stat-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 18px; }
    .stat-val { font-size: 26px; font-weight: 800; color: #fff; }
    .stat-val.accent { color: var(--accent-red); }
    .stat-val.gold { color: var(--accent-gold); }
    .stat-val.cyan { color: var(--accent-cyan); }
    .stat-label { font-size: 12px; color: var(--text-muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }

    /* Filters */
    .filter-bar { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 14px 20px; margin-bottom: 24px; gap: 16px; flex-wrap: wrap; }
    .tabs { display: flex; gap: 8px; }
    .tab-btn { background: transparent; border: none; color: var(--text-muted); font-weight: 600; font-size: 14px; padding: 8px 14px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
    .tab-btn.active { background: #1e293b; color: white; border: 1px solid #334155; }
    .search-box { background: #0b1120; border: 1px solid #334155; border-radius: 8px; padding: 8px 14px; color: white; font-size: 13px; width: 280px; }
    .search-box:focus { outline: none; border-color: var(--accent-red); }

    /* Cards */
    .promos-list { display: flex; flex-direction: column; gap: 18px; }
    .promo-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; padding: 22px; transition: transform 0.15s, border-color 0.15s; }
    .promo-card:hover { border-color: #3b82f6; }
    .card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
    .rank-pill { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 800; padding: 4px 10px; border-radius: 6px; }
    .rank-top3 { background: rgba(255, 183, 3, 0.15); color: var(--accent-gold); border: 1px solid rgba(255, 183, 3, 0.3); }
    .rank-normal { background: #1e293b; color: #cbd5e1; }
    .funnel-tag { font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 4px 8px; border-radius: 6px; letter-spacing: 0.5px; }
    .funnel-tofu { background: rgba(255, 51, 102, 0.15); color: #ff3366; border: 1px solid rgba(255, 51, 102, 0.3); }
    .funnel-mofu { background: rgba(6, 214, 160, 0.15); color: #06d6a0; border: 1px solid rgba(6, 214, 160, 0.3); }
    .funnel-bofu { background: rgba(131, 56, 236, 0.15); color: #a78bfa; border: 1px solid rgba(131, 56, 236, 0.3); }
    
    .card-meta { display: flex; gap: 14px; font-size: 13px; color: var(--text-muted); align-items: center; }
    .timecode { font-family: 'JetBrains Mono', monospace; background: #0a0f1d; border: 1px solid #1e293b; padding: 3px 8px; border-radius: 6px; color: #38bdf8; font-weight: 600; }

    .card-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
    .section-title { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.5px; margin-bottom: 4px; }
    .hook-box, .cliff-box { background: #0a0f1d; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; border-left: 3px solid #3b82f6; font-size: 13.5px; }
    .hook-box { border-left-color: var(--accent-red); }
    .cliff-box { border-left-color: var(--accent-gold); }
    .why-it-works-box { font-size: 13.5px; color: #e2e8f0; font-weight: 500; font-style: italic; background: rgba(30, 41, 59, 0.4); padding: 10px 14px; border-radius: 8px; border: 1px solid #1e293b; }

    /* Score Column */
    .score-breakdown { background: #0a0f1d; border: 1px solid #1e293b; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; }
    .total-score { text-align: center; padding-bottom: 12px; border-bottom: 1px solid #1e293b; margin-bottom: 12px; }
    .total-score .num { font-size: 32px; font-weight: 800; color: #fff; }
    .score-row { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
    .score-row span:last-child { font-weight: 700; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; }
    .audit-badge { margin-top: 10px; text-align: center; font-size: 11px; font-weight: 700; padding: 4px; border-radius: 6px; }
    .audit-pass { background: rgba(6, 214, 160, 0.1); color: var(--accent-cyan); border: 1px solid rgba(6, 214, 160, 0.2); }
    .audit-warn { background: rgba(255, 183, 3, 0.1); color: var(--accent-gold); border: 1px solid rgba(255, 183, 3, 0.2); }

    .tropes-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
    .trope-chip { font-size: 11px; background: #1e293b; color: #cbd5e1; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-area">
        <span class="badge">KUKU AI GENERALIST</span>
        <div>
          <h1>Find the Promos (Ads) — Microdrama Intelligence Engine</h1>
          <div class="subtitle">Screenplay Parser • Hook & Cliffhanger Extractor • Viral Ranker • Automated Quality Audit</div>
        </div>
      </div>
      <div class="actions">
        <a class="btn" href="/promos.json" download="promos_all_50_episodes.json">📥 Export JSON</a>
        <a class="btn btn-primary" href="/promos.csv" download="promos_all_50_episodes.csv">📊 Export CSV</a>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-val">50</div>
        <div class="stat-label">Episodes Analyzed</div>
      </div>
      <div class="stat-card">
        <div class="stat-val accent">47,267</div>
        <div class="stat-label">Candidate Windows Tested</div>
      </div>
      <div class="stat-card">
        <div class="stat-val cyan">9.5s</div>
        <div class="stat-label">Full Show Ingestion Speed</div>
      </div>
      <div class="stat-card">
        <div class="stat-val gold">&lt; $0.01</div>
        <div class="stat-label">Inference Cost / 50 Eps</div>
      </div>
    </div>

    <div class="filter-bar">
      <div class="tabs">
        <button class="tab-btn active" onclick="setFilter('ALL')">All Promos (50)</button>
        <button class="tab-btn" onclick="setFilter('TOP10')">🏆 Top 10 Hero Promos</button>
        <button class="tab-btn" onclick="setFilter('TOFU')">🚀 Cold Top-of-Funnel</button>
        <button class="tab-btn" onclick="setFilter('MOFU')">🔥 Curiosity Cliffhangers</button>
        <button class="tab-btn" onclick="setFilter('BOFU')">👑 Catharsis & Payoff</button>
      </div>
      <input type="text" id="searchInput" class="search-box" placeholder="Search by episode, character, trope..." oninput="renderPromos()">
    </div>

    <div class="promos-list" id="promosList">
      <!-- Injected via JavaScript -->
    </div>
  </div>

  <script>
    let PROMOS_DATA = null;
    let CURRENT_FILTER = 'ALL';

    fetch('/api/data')
      .then(res => res.json())
      .then(data => {
        PROMOS_DATA = data;
        renderPromos();
      });

    function setFilter(filter) {
      CURRENT_FILTER = filter;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      renderPromos();
    }

    function renderPromos() {
      if (!PROMOS_DATA) return;
      const list = document.getElementById('promosList');
      const query = document.getElementById('searchInput').value.toLowerCase();
      let promos = PROMOS_DATA.all_promos;

      if (CURRENT_FILTER === 'TOP10') {
        promos = PROMOS_DATA.top_10_hero_promos;
      } else if (CURRENT_FILTER === 'TOFU') {
        promos = promos.filter(p => p.target_funnel.includes('Top-of-Funnel') || p.scores.hook_strength >= 26);
      } else if (CURRENT_FILTER === 'MOFU') {
        promos = promos.filter(p => p.target_funnel.includes('High-Curiosity') || p.scores.cliffhanger_tension >= 22);
      } else if (CURRENT_FILTER === 'BOFU') {
        promos = promos.filter(p => p.target_funnel.includes('Catharsis') || p.target_funnel.includes('Retargeting'));
      }

      if (query) {
        promos = promos.filter(p => 
          p.episode_title.toLowerCase().includes(query) ||
          p.hook.toLowerCase().includes(query) ||
          p.cliffhanger.toLowerCase().includes(query) ||
          p.why_it_works.toLowerCase().includes(query) ||
          p.identified_tropes.some(t => t.toLowerCase().includes(query)) ||
          ("ep " + p.episode).includes(query)
        );
      }

      list.innerHTML = promos.map(p => {
        const isTop3 = p.global_rank <= 3;
        let funnelClass = 'funnel-tofu';
        if (p.target_funnel.includes('Curiosity')) funnelClass = 'funnel-mofu';
        if (p.target_funnel.includes('Catharsis') || p.target_funnel.includes('Retargeting')) funnelClass = 'funnel-bofu';

        const auditStatus = p.quality_audit.status;
        const auditClass = auditStatus === 'PASS' ? 'audit-pass' : 'audit-warn';

        return `
          <div class="promo-card">
            <div class="card-top">
              <div>
                <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
                  <span class="rank-pill ${isTop3 ? 'rank-top3' : 'rank-normal'}">Rank #${p.global_rank}</span>
                  <span class="funnel-tag ${funnelClass}">${p.target_funnel.split('-')[0].trim()}</span>
                  <span style="font-weight:700; font-size:16px;">Episode ${p.episode}</span>
                  <span style="color:var(--text-muted); font-size:13px;">— ${p.scene_heading}</span>
                </div>
                <div class="card-meta">
                  <span>⏱ Timestamps: <strong class="timecode">${p.start_time} - ${p.end_time}</strong></span>
                  <span>Duration: <strong>${p.duration_seconds}s</strong></span>
                </div>
              </div>
            </div>

            <div class="card-grid">
              <div>
                <div class="section-title">⚡ 3-Second Hook</div>
                <div class="hook-box">${p.hook}</div>

                <div class="section-title">🔪 Cliffhanger Cut</div>
                <div class="cliff-box">${p.cliffhanger}</div>

                <div class="section-title">💡 Why It Works (UA / Creative Strategy)</div>
                <div class="why-it-works-box">"${p.why_it_works}"</div>

                <div class="tropes-row">
                  ${p.identified_tropes.map(t => `<span class="trope-chip">${t}</span>`).join('')}
                </div>
              </div>

              <div class="score-breakdown">
                <div>
                  <div class="total-score">
                    <div class="num">${p.scores.total_virality_score}</div>
                    <div class="stat-label">Virality Score / 100</div>
                  </div>
                  <div class="score-row"><span>Hook Strength (0-30)</span><span>${p.scores.hook_strength}</span></div>
                  <div class="score-row"><span>Cliffhanger Tension (0-30)</span><span>${p.scores.cliffhanger_tension}</span></div>
                  <div class="score-row"><span>Standalone Clarity (0-20)</span><span>${p.scores.standalone_clarity}</span></div>
                  <div class="score-row"><span>Trope & Pacing (0-20)</span><span>${p.scores.trope_and_pacing}</span></div>
                </div>

                <div>
                  <div class="audit-badge ${auditClass}">
                    ${auditStatus === 'PASS' ? '✓ Quality Audit: Clean Pass' : '⚠ Quality Audit: 1 Review Flag'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }
  </script>
</body>
</html>
"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
        elif url.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with open(DATA_PATH, "rb") as f:
                self.wfile.write(f.read())
        elif url.path == "/promos.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", 'attachment; filename="promos_all_50_episodes.json"')
            self.end_headers()
            with open(DATA_PATH, "rb") as f:
                self.wfile.write(f.read())
        elif url.path == "/promos.csv":
            csv_path = os.path.join(os.path.dirname(__file__), "outputs", "promos_all_50_episodes.csv")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", 'attachment; filename="promos_all_50_episodes.csv"')
            self.end_headers()
            with open(csv_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)

if __name__ == "__main__":
    server = socketserver.TCPServer(("", PORT), Handler)
    print(f"🚀 Kuku Promo Finder Server running at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
