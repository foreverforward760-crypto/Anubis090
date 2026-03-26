# ANUBIS Changelog

## v4.0.0 — March 2026
**LUMINARK v5 integration — SAR / NMAP / Bifurcation / 369 Resonance**

New endpoints powered by LUMINARK OVERWATCH PRIME ULTRA v5.0:

- `POST /api/sar/velocity` — Stage velocity simulation (dS/dt physics engine). Compute how fast any position is moving through SAR stages, project N steps forward, get full trajectory with gate notation (e.g. `4.5↓@L1`).
- `POST /api/sar/bifurcation` — Stage 5 three-way bifurcation probability. For any position approaching the critical threshold, returns P(advance), P(graceful regression), P(crisis) using sigmoid model.
- `POST /api/sar/resonance` — 369 critical gate detection. Identifies positions at magnetic drag gates (3/6: 90%, 8: 100% High Voltage, 9: 0% Slipstream).
- `POST /api/nmap/classify` — NMAP Economic Stage Classifier. Classifies economic/market conditions into SAP Stage 0-9. Stage 8 detection: ≥4 of 6 criteria → 70% probability Stage 9 correction within 18-36 months.
- `POST /api/sar/container_rule` — Container Rule analysis. Content (inner drive, 1st digit) vs Container (outer form, 2nd digit), pivot at 4.5, Divine Line detection (digital root 9).
- `GET  /api/sar/stage_names` — SAR gate name + flux dynamics reference table.

## v3.1.0 — March 2026
- API key auth (tiered: master / demo)
- SQLite persistence for compliance data and audit trail
- Full IP / legal licensing layer (MAAT Commercial License)
- SECURITY.md, NOTICE file

## v3.0.0 — March 2026
- Compliance & Overwatch layer: multi-platform rule enforcement
- Finance terminology modernization
- Violation log with resolve/clear workflow

## v2.0.0 — March 2026
- LUMINARK-powered portfolio intelligence (initial build)
- SAP 10-stage portfolio classification
- CITI systemic alert
- Trader behavior profiler
- Yunus / Harrowing protocols
- React frontend
