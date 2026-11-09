# 🎬 KUKU Promo Finder — Microdrama Ad Intelligence Engine

> **AI Generalist Assignment Submission — Problem 1: Find the Promos (Ads)**  
> Evaluated on 50 Real Microdrama Episodes (Regency Romance & Revenge Arc).

---

## 📌 Executive Summary

In vertical microdrama streaming (Kuku, ReelShort, DramaBox), **User Acquisition (CAC) and ad creative fatigue on TikTok / Meta** are the core growth bottlenecks. Editors spend 15–20 hours per show manually watching 50+ episodes to find 30-second clips.

This system is an **automated AI Content Intelligence engine** that ingests complete microdrama screenplays and extracts broadcast-ready 20–60s promo ads ranked by viral conversion potential:
- **3-Second Thumb-Stop Hook:** Physical shock, verbal betrayal, heightened emotion.
- **Unresolved Cliffhanger Cut:** Cuts at maximum dramatic tension before resolution, compelling app downloads.
- **Cold-Viewer Standalone Clarity:** Zero prior lore required to understand the stakes.

---

## ⚡ Performance & Scale Benchmarks

| Metric | Measured Result |
| :--- | :--- |
| **Episodes Evaluated** | **50 Episodes** (Complete Season Arc) |
| **Candidate Windows Scanned** | **47,267 Temporal Windows** |
| **Full Pipeline Execution Time** | **9.50 seconds** (Standard CPU) |
| **Inference Cost / 50 Episodes** | **< $0.01** (Zero GPU required) |
| **Production Pass Rate** | **44 / 50 Clean Pass** (6 Human Review Flags) |

---

## 🏗️ Architecture: Code vs. AI Division of Labor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PROMO INTELLIGENCE ENGINE ARCHITECTURE                │
├─────────────────┬──────────────────┬─────────────────┬──────────────────────┤
│ 1. DETERMINISTIC│ 2. TEMPORAL NMS  │ 3. MULTI-FACTOR │ 4. AUTOMATED AUDIT   │
│    PARSER (CODE)│    WINDOWING     │    VIRAL SCORER │    & FAILURE FILTER  │
├─────────────────┼──────────────────┼─────────────────┼──────────────────────┤
│ • Regex AST for │ • Sliding window │ • 3s Thumb-Stop │ • Silent dead-air    │
│   cues/delivery │   (20s - 60s)    │   Hook (0-30)   │   detection          │
│ • Speech cadence│ • Beat-boundary  │ • Cliffhanger   │ • Lore-trap penalty  │
│   math & time   │   snapping       │   Gap (0-30)    │ • False-cliffhanger  │
│ • Scene bounds  │ • Temporal IoU   │ • Standalone    │   suppression        │
│                 │   suppression    │   Clarity (0-20)│ • Pacing truncation  │
│                 │   (Threshold 0.35│ • Trope Potency │   mitigation         │
└─────────────────┴──────────────────┴─────────────────┴──────────────────────┘
```

1. **Deterministic Parser (`src/parser.py`)**: Converts raw screenplay text into structured `Episode`, `Scene`, and `Beat` AST objects.
2. **Temporal Non-Maximum Suppression (`src/ranker.py`)**: Applies computer vision-inspired 1D IoU suppression to eliminate redundant sub-second cut variants and extract only the best distinct moments.
3. **Multi-Factor Scorer (`src/scoring.py`)**: 100-point rubric assessing Hook Stop-Rate, Cliffhanger Tension, Zero-Context Clarity, and Trope Potency.
4. **Automated Quality Audit (`src/quality_checker.py`)**: Detects failure modes (dead air, lore traps, false cliffhangers, mid-sentence cuts).

---

## 🚀 Quickstart & How to Run

### Option 1: Native Web UI (Zero External Dependencies)
Runs with standard Python library (`http.server`):
```bash
python3 web_app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### Option 2: Run End-to-End Pipeline
Re-evaluates all 50 episodes and regenerates all JSON, CSV, and Markdown outputs in under 10 seconds:
```bash
python3 src/pipeline.py
```

### Option 3: Streamlit Interactive Dashboard
```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📁 Repository Structure

```
kuku_promo_intelligence/
├── src/
│   ├── parser.py              # Screenplay AST parser & timecode math
│   ├── segmenter.py           # Sliding candidate generator & beat-snapping
│   ├── scoring.py             # 100-point Virality Rubric & Trope engine
│   ├── ranker.py              # Temporal NMS & 3-Phase Campaign portfolio
│   ├── quality_checker.py     # Automated failure mode auditor
│   └── pipeline.py            # End-to-end execution script
├── outputs/                   # Unedited raw outputs for all 50 episodes
│   ├── promos_all_50_episodes.json
│   ├── promos_all_50_episodes.csv
│   ├── top_ranked_promos.md
│   └── failure_modes_analysis.md
├── solution_doc/
│   ├── KUKU_AI_SOLUTION_DOC.pdf   # Official 2-Page Submission PDF
│   └── kuku_solution_doc.html     # Source document
├── web_app.py                 # Standalone local interactive server
├── app.py                     # Streamlit dashboard
├── VIDEO_WALKTHROUGH_SCRIPT.md# 3-minute Loom video script
└── requirements.txt
```

---

## 🏆 Deliverables Checklist

- [x] **Solution Doc:** `solution_doc/KUKU_AI_SOLUTION_DOC.pdf` (Exactly 2 pages, structured across the 5 evaluation lenses).
- [x] **Prototype Link:** Runnable web dashboard (`web_app.py` & `app.py`).
- [x] **Raw Outputs:** Full unedited outputs for all 50 episodes in `outputs/promos_all_50_episodes.json` & `.csv`.
- [x] **Quality Checking:** Real failure mode analysis in `outputs/failure_modes_analysis.md`.
- [x] **Walkthrough Video Script:** Word-for-word voiceover script in `VIDEO_WALKTHROUGH_SCRIPT.md`.
