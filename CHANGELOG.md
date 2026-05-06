# ANUBIS Changelog

## v5.0.0 — May 2026
**Rate limiting (slowapi), v5 API surface finalised**

- `slowapi` rate limiting wired to all authenticated endpoints (60 req/min write, 30 req/min read)
- Removed unimplemented v4 endpoint stubs from docs: `/api/sar/velocity`, `/api/sar/resonance`, `/api/sar/container_rule`
- Stage 8 description updated to Dual-Chamber Trap canonical terminology (Chamber A: Illusion of Arrival / Chamber B: Illusion of Permanence)
- Version header corrected to 5.0.0

## v4.0.0 — March 2026
**LUMINARK v5 integration — NMAP / Bifurcation / Frequency analysis**

New endpoints implemented and production-ready:

- `POST /api/sar/bifurcation` — Stage 5 three-way bifurcation probability. For any position approaching the critical threshold, returns P(advance), P(graceful regression), P(crisis) using sigmoid model.
- `POST /api/nmap/classify` — NMAP Economic Stage Classifier. Classifies economic/market conditions into SAP Stage 0-9. Stage 8 detection: ≥4 of 6 criteria → 70% probability Stage 9 correction within 18-36 months.
- `POST /api/frequency` — Bio-resonance / acoustic frequency analysis via FrequencyAdapter.
- `GET  /api/sar/stage_names` — Canonical SAP stage name reference table.

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
