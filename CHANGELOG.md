# ANUBIS Platform — Changelog

All notable changes to this project are documented here.

---

## [3.0.0] — 2026-03-25

### Added
- **Compliance & Overwatch Layer** — Full rule-based compliance monitoring engine
  - 6 built-in default risk rules (min portfolio stage, max fragility index, max drawdown, max concentration, max critical holdings, max overextended count)
  - Custom rule CRUD via API and UI
  - Platform registry — register and track multiple trading platforms/accounts
  - Timestamped violation alert log with resolve workflow
  - 12 new `/api/compliance/*` endpoints
  - Compliance dashboard UI panel (Rules, Platforms, Alerts tabs)
- **API Key Authentication** — `X-ANUBIS-API-KEY` header enforcement
  - Master key via `ANUBIS_API_KEY` environment variable
  - Demo key for evaluation access
  - Dev mode (no key required) when master key is not configured
- **SQLite Persistence** — Compliance data, alert log, and platforms survive restarts
  - Configurable via `ANUBIS_DB_PATH` environment variable
  - Auto-schema migration on startup
- **`/api/license` endpoint** — Returns product/IP information and key tier
- **`/api/compliance/summary` endpoint** — Aggregate dashboard across all platforms
- Finance-aligned terminology throughout (replaced all mystical/spiritual labels)
  - 10 SAP stage labels updated (Total Loss → Elite Alpha)
  - 10 Trader archetypes updated
  - All protocol names, metric names, and UI labels modernized
- Proprietary LICENSE, NOTICE, and SECURITY files

### Changed
- Version bumped to 3.0.0
- App description updated to reflect compliance capabilities
- Health endpoint now returns copyright, patent, and auth mode information
- All API routes now support auth via dependency injection

---

## [2.0.0] — 2026-03-24

### Added
- ANUBIS Platform initial production build
- SAP 10-stage portfolio classification (NSDT framework)
- Position Trajectory Tracker (stage_velocity, risk_momentum, rigidity_index, recovery_index)
- Discipline Protocol: Hubris Scanner + False Breakout Detection + Controlled Exposure Reduction
- Drawdown Recovery Protocol: Last Healthy Baseline + Baseline Recovery Sequence + Circuit Breaker Mode
- Adaptive Rebalancer (60% rerouting from Stage 0-2 positions)
- Stop-Loss & Replace Protocol
- CITI Systemic Tumbling Alert
- Trader Behavior Profiler (7-metric behavioral stage assessment)
- React frontend served from `/static/index.html`
- yfinance real-time data with deterministic mock fallback
- Docker + Render.com deployment configuration

---

## Legend

- **Added** — New features
- **Changed** — Changes in existing functionality
- **Deprecated** — Soon-to-be removed features
- **Removed** — Removed features
- **Fixed** — Bug fixes
- **Security** — Security fixes

---

*© 2024-2026 Richard L. Stanfield / MAAT — All Rights Reserved*
