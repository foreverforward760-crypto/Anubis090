# 𓂀 ANUBIS — LUMINARK Portfolio Intelligence Platform

> **"ANUBIS doesn't just tell you where your portfolio is. It tells you where it's going, whether to trust what you're seeing, whether you as the trader are the problem, and what to do if things go wrong."**

ANUBIS is a stock portfolio intelligence platform powered by the **LUMINARK SAP (Stanfield's Axiom of Perpetuity)** 10-stage framework. It classifies portfolio health, tracks behavioral trajectory, detects epistemic overconfidence, and provides early-warning signals before catastrophic drawdowns — capabilities no conventional trading dashboard offers.

---

## What ANUBIS Does

| Capability | What It Means |
|---|---|
| **SAP 10-Stage Classification** | Every holding and the overall portfolio is assigned a stage (0–9) from Collapse to Transcendence based on multi-dimensional NSDT analysis |
| **Trajectory Engine** | Tracks stage velocity, risk momentum, rigidity index, and recovery index across your session — tells you ESCALATING, RECOVERING, TRAPPED, or STABLE |
| **False Light Detection** | Flags holdings that appear Stage 7-8 strong but have collapsing underlying coherence — the most dangerous pattern in markets |
| **Yunus Protocol** | Scans your trading notes for overconfidence language and arrogance markers before you execute |
| **Harrowing Protocol** | Auto-preserves the last healthy portfolio configuration (Stage 4-6); shows restoration path when things go wrong |
| **InfraAdaptiveCamouflage** | Recommends rerouting 60% of critical position weight to healthy holdings |
| **Systemic Alert (CITI)** | Fires when portfolio stage, trader behavioral stage, and trap risk deteriorate simultaneously |
| **Trader Behavioral Stage** | Assesses you as a trader across 7 metrics: win rate, hold period, concentration, drawdown, leverage, plan overrides, correlation |

---

## Quick Start

### Local (Python)
```bash
git clone https://github.com/foreverforward760-crypto/Anubis.git
cd Anubis
pip install -r requirements.txt
python app.py
```
Open: **http://localhost:8000**

### Docker
```bash
docker build -t anubis .
docker run -p 8000:8000 anubis
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Server status + yfinance data mode |
| `GET` | `/api/portfolio/demo` | Load 6-holding demo portfolio |
| `POST` | `/api/analyze` | Full portfolio + behavioral analysis |
| `GET` | `/api/trajectory` | Session trajectory metrics |
| `POST` | `/api/yunus_scan` | Epistemic safety text scan |
| `GET` | `/api/harrowing_status` | Harrowing protocol state |
| `GET` | `/api/docs` | Interactive Swagger docs |

---

## SAP Stage Reference

| Stage | Label | Meaning |
|---|---|---|
| 0 | System Collapse | Emergency — complete failure |
| 1 | Critical Failure | Severe deterioration |
| 2 | Crisis | Active crisis state |
| 3 | Struggle | High stress, instability |
| 4 | Transition | Volatile but recovering |
| 5 | Equilibrium | Balanced, stable |
| 6 | Growth | Positive momentum |
| 7 | Peak Performance | High coherence + adaptability |
| 8 | **Brittle Peak** | **FALSE LIGHT — appears strong, collapse imminent** |
| 9 | Transcendence | Rare, sustained excellence |

---

## Architecture

```
anubis/
├── app.py           # FastAPI backend with full LUMINARK engine
├── static/
│   └── index.html   # React dashboard (no build step required)
├── requirements.txt
├── Dockerfile
├── render.yaml      # Render.com one-click deployment
└── .env.example
```

---

## Powered By

**LUMINARK OVERWATCH PRIME ULTRA** + **LUMINARK CONSCIOUSNESS ENGINE OMEGA**  
MAAT — Meridian Axiom Alignment Technologies | Inventor: Richard L. Stanfield  
Patent Pending — USPTO (Amended Specification filed March 2026)

---

*ANUBIS does not constitute financial advice. All stage assessments are for informational and research purposes only.*
