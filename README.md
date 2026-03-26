# 𓂀 ANUBIS — LUMINARK Portfolio Intelligence Platform
**Version 4.0.0 | Powered by LUMINARK v5**

> *"ANUBIS doesn't just tell you where your portfolio is. It tells you where it's going, whether it's lying to itself, and what happens if it keeps going the way it's going."*

Copyright © 2024-2026 Richard L. Stanfield | Meridian Axiom Alignment Technologies (MAAT)
**Patent Pending — USPTO (Application filed March 2026) | All Rights Reserved**

---

## What ANUBIS Does

ANUBIS is a production-grade portfolio intelligence and compliance platform built on the **LUMINARK dual-engine architecture**:

- **LUMINARK OVERWATCH PRIME ULTRA** — Infrastructure intelligence, stage physics, economic classification
- **LUMINARK CONSCIOUSNESS ENGINE OMEGA** — Behavioral intelligence, consciousness mapping, ethical validation

ANUBIS applies these engines to financial portfolios, trading behavior, and market conditions. It answers questions that standard portfolio tools cannot:

- *Where is this position in its development cycle — and is it lying about it?*
- *Is this portfolio approaching Stage 5 bifurcation? What's the probability of crisis vs. graceful regression?*
- *Is the broader economy signaling Stage 8 overextension? When does Stage 9 correction arrive?*
- *Is this position at a 3-6-9 critical gate where magnetic drag changes everything?*

---

## New in v4.0 — LUMINARK v5 Integration

Six new endpoints powered by 3,700 lines of new LUMINARK math:

| Endpoint | Capability |
|---|---|
| `POST /api/sar/velocity` | Stage velocity (dS/dt) — simulate trajectory N steps forward |
| `POST /api/sar/bifurcation` | Stage 5 three-way probability: advance / regression / crisis |
| `POST /api/sar/resonance` | 369 critical gate detection — flux drag + phase transition |
| `POST /api/nmap/classify` | NMAP Economic Classifier — Stage 0-9, Stage 8 six-criteria test |
| `POST /api/sar/container_rule` | Content vs Container digit analysis, Divine Line detection |
| `GET  /api/sar/stage_names` | SAR gate names + flux dynamics reference |

---

## Core Capabilities (All Versions)

- **SAP 10-Stage Classification** — Every position assigned a stage (0-9) with confidence score
- **NSDT 5-Vector Assessment** — complexity, stability, tension, adaptability, coherence
- **TrapScore Engine** — Detects Stage 8 rigidity and false breakout patterns
- **Temporal State Tracking** — Session-level trajectory: stage_velocity, risk_momentum, rigidity_index
- **Yunus Protocol** — Three-tier isolation: Partial (I<50%), Full (I<25%), Arc Disorientation (>70%)
- **Harrowing Protocol** — Controlled disassembly for positions past Stage 8 point of no return
- **CITI Systemic Alert** — Cross-Indicator Tumbling Index — predicts cascade failure
- **Trader Behavior Profiler** — 7-metric behavioral stage assessment
- **Compliance & Overwatch** — Multi-platform rule enforcement, violation log, audit trail
- **API Key Authentication** — Tiered access control (master / demo)
- **SQLite Persistence** — Compliance data, alerts, full audit trail

---

## API Access

```bash
# Health check (no key required)
curl https://your-deployment-url/api/health

# Stage velocity simulation
curl -X POST https://your-deployment-url/api/sar/velocity \
  -H "X-ANUBIS-API-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d '{"gate": 4, "micro_stage": 0.8, "energy": 72, "integrity": 65, "maat": 80, "steps": 15}'

# NMAP economic classification
curl -X POST https://your-deployment-url/api/nmap/classify \
  -H "X-ANUBIS-API-KEY: your-key" \
  -H "Content-Type: application/json" \
  -d '{"gdp_growth": 3.8, "unemployment": 3.6, "inflation": 4.1, "debt_to_gdp": 128, "asset_deviation_sd": 2.3, "credit_expansion": 17.5}'

# Full API docs
open https://your-deployment-url/api/docs
```

---

## Deployment

```bash
pip install -r requirements.txt
export ANUBIS_API_KEY="your-master-key"
uvicorn app:app --host 0.0.0.0 --port 8000
```

Render.com: `render.yaml` is included for one-click deployment.

---

## Architecture

```
ANUBIS v4.0
├── Core Engine (7 Protected Modules)
│   ├── NSDT Engine         — 5-vector stage classification
│   ├── Stage Classifier    — SAP 0-9 assessment
│   ├── TrapScore Engine    — rigidity + false breakout detection
│   ├── Temporal State      — trajectory tracking
│   ├── Consensus Engine    — multi-evaluator confidence
│   ├── Pattern Recurrence  — behavioral history analysis
│   └── Alert Engine        — Harrowing + Yunus protocol triggers
├── Domain Adapter (v5 additions)
│   ├── SAR Math            — dm/dt formalization, gate names, flux dynamics
│   ├── NMAP Classifier     — economic stage quantitative thresholds
│   ├── Container Rule      — digit vessel analysis
│   └── Arc Notation        — 4.5↓@L1 position encoding
├── Application Layer
│   ├── Stage 5 Bifurcation — 3-way sigmoid probability
│   ├── 369 Resonance       — phase gate detection
│   ├── Compliance Layer    — multi-platform rule enforcement
│   └── Yunus/Harrowing     — isolation + disassembly protocols
└── Interface Layer
    ├── FastAPI REST API    — /api/docs for full schema
    ├── React Frontend      — /static/index.html
    └── SQLite Persistence  — compliance + audit trail
```

---

## Intellectual Property

ANUBIS is built on **Stanfield's Axiom of Perpetuity (SAP)** and the **Noctilucan Stage Development Theory (NSDT)** — proprietary frameworks developed by Richard L. Stanfield.

Commercial licensing: [info.rstanfield@gmail.com](mailto:info.rstanfield@gmail.com)
