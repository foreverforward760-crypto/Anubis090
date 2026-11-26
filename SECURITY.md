# Security Policy — ANUBIS Prototype

## Support status

ANUBIS is an experimental prototype. There is no formal security-support SLA.

| Version | Status |
|---|---|
| Current repository version (5.x) | Best-effort review of reported issues |
| Earlier versions | No security support |

## Reporting a vulnerability

Please do not publish exploitable vulnerabilities in a public issue. Report them privately to:

**info.rstanfield@gmail.com**

Include the affected version or commit, a description, reproducible steps, and potential impact. Acknowledgment and remediation timelines are not guaranteed.

## API key security

Authenticated API endpoints require an explicitly configured `ANUBIS_API_KEY` of at least 32 characters. The application no longer supplies a default API key. An optional `ANUBIS_DEMO_KEY` must also be at least 32 characters.

Generate credentials with a cryptographically secure random generator. Do not commit secrets to source control. Use environment variables or a secrets manager.

## Browser access

Cross-origin browser access is disabled unless trusted origins are explicitly listed in `ANUBIS_CORS_ORIGINS`. Do not use a wildcard origin for a public deployment.

## Data handling

The current application writes request and response audit records to a local SQLite database. That database is not encrypted by the application. Protect the database file, restrict filesystem access, define retention and deletion procedures, and do not submit sensitive financial or personal information to a public instance without a separate privacy and security review.

The current application code does not send portfolio inputs to an external inference service. This statement should be revisited if external data or AI integrations are added.

## Deployment limitations

API key authentication and CORS configuration do not make this prototype production-ready. Public deployment also requires TLS, secure secret storage, dependency updates, database access controls, monitoring, backup/restore testing, rate-limit review, and independent security testing.

© 2024-2026 Richard L. Stanfield / MAAT
