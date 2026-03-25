# 𓂀 ANUBIS — LUMINARK Portfolio Intelligence & Compliance Platform

> **"ANUBIS doesn't just tell you where your portfolio is. It tells you where it's going, whether to trust what you're seeing, whether you as the trader are the problem, what to do if things go wrong — and whether your trading platforms are operating within your defined risk rules."**

ANUBIS is a stock portfolio intelligence and **compliance monitoring** platform powered by the **LUMINARK SAP (Stanfield's Asset Progression)** 10-stage framework. It classifies portfolio health, tracks behavioral trajectory, detects overextension, enforces risk-based compliance rules, and provides early-warning signals before catastrophic drawdowns.

---

## What ANUBIS Does

| Capability | What It Means |
|---|---|
| **SAP 10-Stage Classification** | Every holding and the overall portfolio is assigned a stage (0–9) from Total Loss to Elite Alpha based on multi-dimensional NSDT analysis |
| **Position Trajectory Tracker** | Tracks stage velocity, risk momentum, rigidity index, and recovery index — tells you ASCENDING, ESCALATING, RECOVERING, TRAPPED, STABLE, or OSCILLATING |
| **False Breakout Detection** | Flags holdings that appear Stage 7-8 strong but have collapsing underlying trend consistency — the most dangerous pattern in markets |
| **Discipline Protocol** | Scans your trading notes for overconfidence language and hubris markers before you execute (Hubris Scanner) |
| **Drawdown Recovery Protocol** | Auto-preserves the last healthy portfolio configuration (Stage 4-6); shows restoration path when things go wrong |
| **Adaptive Rebalancer** | Recommends rerouting 60% of critical position weight to healthy holdings |
| **CITI Systemic Alert** | Fires when portfolio stage, trader behavioral stage, and trap risk deteriorate simultaneously |
| **Trader Behavior Profiler** | Assesses you as a trader across 7 metrics: win rate, hold period, concentration, drawdown, leverage, plan overrides, correlation |
| **Compliance & Overwatch Monitor** | Register trading platforms, define risk rules, run automated compliance checks, and track a timestamped violation alert log |

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

### Portfolio Intelligence
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Server status + yfinance data mode |
| `GET` | `/api/portfolio/demo` | Load 6-holding demo portfolio |
| `POST` | `/api/analyze` | Full portfolio + behavioral analysis |
| `GET` | `/api/trajectory` | Session trajectory metrics |
| `POST` | `/api/yunus_scan` | Discipline Protocol text scan |
| `GET` | `/api/harrowing_status` | Drawdown Recovery Protocol state |

### Compliance & Overwatch
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/compliance/rules` | List all compliance rules |
| `POST` | `/api/compliance/rules` | Add a custom compliance rule |
| `DELETE` | `/api/compliance/rules/{id}` | Delete a rule |
| `POST` | `/api/compliance/rules/{id}/toggle` | Enable/disable a rule |
| `GET` | `/api/compliance/platforms` | List registered trading platforms |
| `POST` | `/api/compliance/platforms` | Register a platform for monitoring |
| `DELETE` | `/api/compliance/platforms/{id}` | Remove a platform |
| `POST` | `/api/compliance/check` | Run compliance check on a portfolio |
| `GET` | `/api/compliance/alerts` | Get the violation alert log |
| `DELETE` | `/api/compliance/alerts` | Clear all alerts |
| `POST` | `/api/compliance/alerts/{id}/resolve` | Mark an alert as resolved |
| `GET` | `/api/compliance/summary` | Overall compliance dashboard summary |
| `GET` | `/api/docs` | Interactive Swagger docs |

---

## SAP Stage Reference

| Stage | Label | Meaning |
|---|---|---|
| 0 | Total Loss | Emergency — complete failure, liquidation required |
| 1 | Critical Risk | Severe deterioration across positions |
| 2 | Active Decline | Sustained losses, no recovery signal |
| 3 | Stress Zone | High volatility pressure, instability |
| 4 | Inflection Point | Volatile but recovery capacity present |
| 5 | Neutral Zone | Balanced risk/reward — holding steady |
| 6 | Bullish Trend | Positive momentum building |
| 7 | High Alpha | Strong trend consistency, high resilience |
| 8 | **Overextended** | **FALSE BREAKOUT — surface strength concealing fragility** |
| 9 | Elite Alpha | Rare, sustained, exceptional performance |

---

## Built-in Compliance Rules

| Rule | Default Threshold | Severity |
|---|---|---|
| Min Portfolio Stage | ≥ 3 | WARNING |
| Max Fragility Index | ≤ 0.75 | WARNING |
| Max Critical Holdings (Stage 0-1) | ≤ 1 | CRITICAL |
| Max Overextended Count (Stage 8) | ≤ 2 | WARNING |
| Max Portfolio Drawdown | ≥ −25% | CRITICAL |
| Max Concentration (Top-3) | ≤ 60% | WARNING |

All built-in rules can be toggled on/off. Custom rules can be added via API or UI.

---

## Architecture

```
anubis/
├── app.py           # FastAPI backend — LUMINARK engine + Compliance layer
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
