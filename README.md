# ANUBIS — 0-9-0 Portfolio and Market-Analysis Prototype

**Status: experimental software prototype. No patent application has been filed.**

ANUBIS is a FastAPI application that applies the project's 0-9-0 / Stanfield's Axiom of Perpetuity framework to user-supplied portfolio, market, and system metrics. It is a rule-based classification and journaling/analysis prototype—not a production-grade portfolio platform, brokerage integration, investment adviser, or validated forecasting system.

## Conceptual origin and implementation

The project owner states that the underlying 0-9-0 framework, ANUBIS concept, and ideas for its applications originated with him. AI systems generated the implementation code and suggested supporting technical mechanisms. NSDT and the Container Rule are AI-added implementation mechanisms within the owner's framework, not independent conceptual origins.

This records the project owner's account; it is not a legal determination of copyright ownership, inventorship, or exclusive rights. Third-party dependencies, submodule licenses, AI-service terms, and code provenance require separate review before commercial transfer or licensing.

## What the current code does

The FastAPI application imports the LUMINARK engine from the `luminark-engine` Git submodule and exposes these endpoints:

| Endpoint | Actual behavior |
|---|---|
| `POST /api/classify` | Converts five supplied numeric inputs into an NSDT vector and calls the engine's rule-based stage analysis |
| `POST /api/sar/bifurcation` | Applies a simple recalibration condition and returns fixed probability sets; these are programmed outputs, not statistically calibrated probabilities |
| `POST /api/nmap/classify` | Converts six supplied economic indicators through fixed formulas, then classifies the resulting vector |
| `POST /api/frequency` | Converts supplied frequency-related metrics through the engine's FrequencyAdapter; this is not a validated physiological or bio-resonance assessment |
| `GET /api/sar/stage_names` | Returns the engine's stage-name registry |
| `GET /api/health` | Returns application and engine status |
| `GET /api/audit/recent` | Returns recent audit metadata; requires API authentication |

The application stores request/response audit records in a local SQLite database. Audit storage is not encrypted by this application. Do not submit sensitive financial, personal, or client information to a public deployment without a privacy and security review.

## Important limitations

- No broker, exchange, custodian, payment network, or trading-platform integration is established by the current application.
- No independent market, portfolio, economic, clinical, or infrastructure validation is established.
- The bifurcation endpoint returns fixed rule-based probability values. They should not be interpreted as measured or calibrated probabilities.
- Economic and frequency inputs are mapped through project-defined formulas. Their outputs are not validated economic forecasts or physiological measurements.
- Stage classifications and TrapScore values are framework-based heuristics, not established predictors of returns, losses, defaults, or market events.
- The application is not a substitute for licensed financial advice or professional risk controls.
- The local SQLite audit database is not encrypted. Retention, access controls, backups, and deletion procedures require review before handling sensitive data.

## Security configuration

The application no longer ships with a default API key. Authenticated endpoints return HTTP 503 until a master key of at least 32 characters is configured. An optional development demo key must also be at least 32 characters and is rejected when `ANUBIS_ENVIRONMENT=production`.

Generate a key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set the following environment variables before starting the service:

- `ANUBIS_ENVIRONMENT` — `development` or `production`
- `ANUBIS_API_KEY` — required random secret, at least 32 characters
- `ANUBIS_DEMO_KEY` — optional separate demo credential, at least 32 characters
- `ANUBIS_CORS_ORIGINS` — optional comma-separated list of explicitly trusted browser origins; empty by default
- `ANUBIS_ENGINE_PRESET` — engine preset; defaults to `industrial_strict`
- `ANUBIS_DB_PATH` — SQLite path; defaults to `anubis_audit.db`

Do not expose the prototype publicly without TLS, secret management, database protection, rate-limit review, dependency review, and independent security testing.

## Local setup

The engine is a Git submodule. Clone with submodules:

```bash
git clone --recurse-submodules https://github.com/foreverforward760-crypto/Anubis090.git
cd Anubis090
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configure the environment variables above, then run:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

The API documentation is available at `/docs` while the service is running. The static frontend is served by the application after API routes are registered.

## Verification status

The repository includes the LUMINARK engine test suite as a submodule and ANUBIS-specific security tests. Passing software tests confirms only the tested code paths. It does not establish predictive performance, investment value, security certification, production readiness, or customer outcomes.

## Commercial status

The most defensible current description is an experimental framework-based analytics prototype. A commercial offering would require a defined customer problem, validated data sources, tested integrations, documented performance against baselines, security/privacy review, and independent domain review.
